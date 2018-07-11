#!/usr/bin/env python3

from __future__ import division
import os
import sys
import json
import logging
import re
import urllib3
import requests
import yaml
import pickle
import collections
import datetime
import tempfile
import subprocess
import shutil

CACHEDIR = '.cache/'

logging.basicConfig(level=logging.INFO)

def request_get(url, params=None, expected_codes=[200], cached=True, stream=False):
    # If available, read it from cache
    if cached and not stream and os.path.isfile(cached):
        with open(cached, 'r') as fp:
            return fp.read()

    # Get the response from the server
    urllib3.disable_warnings()
    response = requests.get(
        url,
        auth=requests.auth.HTTPBasicAuth(
            config['usr'], config['pwd']),
        params=params,
        verify=False
    )

    # Check we got expected exit code
    if response.status_code not in expected_codes:
        raise requests.HTTPError("Failed to get %s with %s" % (url, response.status_code))

    # If we were streaming file
    if stream:
        with open(cached, 'w+b') as fp:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:   # filter out keep-alive new chunks
                    fp.write(chunk)
            fp.close()
        return

    # In some cases 404 just means "we have nothing"
    if response.status_code == 404:
        return ''

    # If cache was configured, dump data in there
    if cached:
        os.makedirs(os.path.dirname(cached), exist_ok=True)
        with open(cached, 'w') as fp:
            fp.write(response.text)

    return response.text


class Config(collections.UserDict):

    LATEST = 'latest'   # how do we call latest job group in the config?

    def __init__(self):
        with open("config.yaml", "r") as file:
            self.data = yaml.load(file)

        # Additional params when talking to Jenkins
        self['headers'] = None
        self['pull_params'] = {
            u'tree': u'suites[cases[className,duration,name,status,stdout,errorDetails,errorStackTrace,testActions[reason]]]{0}'
        }

    def get_builds(self, job_group=''):
        if job_group == '':
            job_group = self.LATEST
        out = collections.OrderedDict()
        for job in self.data['job_groups'][job_group]['jobs']:
            key = self.data['job_groups'][job_group]['template'].format(**job)
            out[key] = job
        return out

    def init_headers(self):
        url = '{0}/crumbIssuer/api/json'.format(self['url'])
        crumb_data = request_get(url, params=None, expected_codes=[200], cached=False)
        crumb = json.loads(crumb_data)
        self['headers'] = {crumb['crumbRequestField']: crumb['crumb']}


class ForemanDebug(object):

    def __init__(self, job_group, job, build):
        self._url = "%s/job/%s/%s/artifact/foreman-debug.tar.xz" % (config['url'], job, build)
        self._extracted = None

    @property
    def extracted(self):
        if self._extracted is None:
            fp, fname = tempfile.mkstemp()
            print(fname)
            request_get(self._url, cached=fname, stream=True)
            tmpdir = tempfile.mkdtemp()
            subprocess.call(['tar', '-xf', fname, '--directory', tmpdir])
            logging.debug('Extracted to %s' % tmpdir)
            self._extracted = os.path.join(tmpdir, 'foreman-debug')
        return self._extracted


class ProductionLog(object):

    FILE_ENCODING = 'ISO-8859-1'   # guessed it only, that file contains ugly binary mess as well
    DATE_REGEXP = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ')   # 2018-06-13T07:37:26
    DATE_FMT = '%Y-%m-%dT%H:%M:%S'   # 2018-06-13T07:37:26

    def __init__(self, job_group, job, build):
        self._log = None
        self._logfile = os.path.join(CACHEDIR, job_group, job, 'production.log')
        self._foreman_debug = None

        # If we do not have logfile downloaded already, we will need foreman-debug
        if not os.path.isfile(self._logfile):
            self._foreman_debug = ForemanDebug(job_group, job, build)

    @property
    def log(self):
        if self._log is None:
            if self._foreman_debug is not None:
                a = os.path.join(self._foreman_debug.extracted,
                                 'var', 'log', 'foreman', 'production.log')
                shutil.copy2(a, self._logfile)
            self._log = []
            buf = []
            last = None
            with open(self._logfile, 'r', encoding=self.FILE_ENCODING) as fp:
                for line in fp:

                    # This line starts with date - denotes first line of new log record
                    if re.search(self.DATE_REGEXP, line):

                        # This is a new log record, so firs save previous one
                        if len(buf) != 0:
                            self._log.append({'time': last, 'data': buf})
                        last = datetime.datetime.strptime(line[:19], self.DATE_FMT)
                        buf = []
                        buf.append(re.sub(self.DATE_REGEXP, '', line, count=1))

                    # This line does not start with line - comtains continuation of a log recorder started before
                    else:
                        buf.append(line)

                # Save last line
                if len(buf) != 0:
                    self._log.append({'time': last, 'data': buf})

            logging.debug("File %s parsed into memory" % self._logfile)
        return self._log

    def from_to(self, from_time, to_time):
        out = []
        for i in self.log:
            if from_time <= i['time'] <= to_time:
                out.append(i)
            # Do not do following as time is not sequentional in the log (or maybe some workers are off or with different TZ?):
            # TODO: Fix ordering of the log and uncomment this
            #
            # E.g.:
            #   2018-06-17T17:29:44 [I|dyn|] start terminating clock...
            #   2018-06-17T21:34:49 [I|app|] Current user: foreman_admin (administrator)
            #   2018-06-17T21:37:21 [...]
            #   2018-06-17T17:41:38 [I|app|] Started POST "/katello/api/v2/organizations"...
            #
            #if i['time'] > to_time:
            #    break
        return out


class Case(collections.UserDict):
    """
    Result of one test case
    """

    FAIL_STATUSES = ("FAILED", "ERROR", "REGRESSION")
    LOG_DATE_REGEXP = re.compile('^([0-9]{4}-[01][0-9]-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) -')
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, data):
        self.data = data

    def __contains__(self, name):
        return name in self.data or name in ('start', 'end', 'production.log')

    def __getitem__(self, name):
        if name == 'testName':
            self['testName'] = "%s.%s" % (self['className'], self['name'])
        if name in ('start', 'end') and \
            ('start' not in self.data or 'end' not in self.data):
            self.load_timings()
        if name == 'production.log':
            self['production.log'] = "\n".join(
                ["\n".join(i['data']) for i in
                    self.data['OBJECT:production.log'].from_to(
                        self['start'], self['end'])])
        return self.data[name]

    def matches_to_rule(self, rule, indentation=0):
        """
        Returns True if result matches to rule, otherwise returns False
        """
        logging.debug("%srule_matches(%s, %s, %s)" % (" "*indentation, self['name'], rule, indentation))
        if 'field' in rule and 'pattern' in rule:
            # This is simple rule, we can just check regexp against given field and we are done
            try:
                data = self[rule['field']]
                if data is None:
                    data = ''
                out = re.search(rule['pattern'], data) is not None
                logging.debug("%s=> %s" % (" "*indentation, out))
                return out
            except KeyError:
                logging.debug("%s=> Failed to get field %s from case" % (" "*indentation, rule['field']))
                return None
        elif 'AND' in rule:
            # We need to check if all sub-rules in list of rules rule['AND'] matches
            out = None
            for r in rule['AND']:
                r_out = self.matches_to_rule(r, indentation+4)
                out = r_out if out is None else out and r_out
                if not out:
                    break
            return out
        elif 'OR' in rule:
            # We need to check if at least one sub-rule in list of rules rule['OR'] matches
            for r in rule['OR']:
                if self.matches_to_rule(r, indentation+4):
                    return True
            return False
        else:
            raise Exception('Rule %s not formatted correctly' % rule)

    def push_claim(self, reason, sticky=False, propagate=False):
        '''Claims a given test with a given reason

        :param reason: string with a comment added to a claim (ideally this is a link to a bug or issue)

        :param sticky: whether to make the claim sticky (False by default)

        :param propagate: should jenkins auto-claim next time if same test fails again? (False by default)
        '''
        logging.info('claiming {0}::{1} with reason: {2}'.format(self["className"], self["name"], reason))

        if config['headers'] is None:
            config.init_headers()

        claim_req = requests.post(
            u'{0}/claim/claim'.format(self['url']),
            auth=requests.auth.HTTPBasicAuth(
                config['usr'],
                config['pwd']
            ),
            data={u'json': u'{{"assignee": "", "reason": "{0}", "sticky": {1}, "propagateToFollowingBuilds": {2}}}'.format(reason, sticky, propagate)},
            headers=config['headers'],
            allow_redirects=False,
            verify=False
        )

        if claim_req.status_code != 302:
            raise requests.HTTPError(
                'Failed to claim: {0}'.format(claim_req))

        self['testActions'][0]['reason'] = reason
        return(claim_req)

    def load_timings(self):
        if self['stdout'] is None:
            return
        log = self['stdout'].split("\n")
        log_size = len(log)
        log_used = 0
        start = None
        end = None
        counter = 0
        while start is None:
            match = self.LOG_DATE_REGEXP.match(log[counter])
            if match:
                start = datetime.datetime.strptime(match.group(1),
                    self.LOG_DATE_FORMAT)
                break
            counter += 1
        log_used += counter
        counter = -1
        while end is None:
            match = self.LOG_DATE_REGEXP.match(log[counter])
            if match:
                end = datetime.datetime.strptime(match.group(1),
                    self.LOG_DATE_FORMAT)
                break
            counter -= 1
        log_used -= counter
        assert log_used <= log_size, \
            "Make sure detected start date is not below end date and vice versa"
        self['start'] = start
        self['end'] = end




class Report(collections.UserList):
    """
    Report is a list of Cases (i.e. test results)
    """

    def __init__(self, job_group=''):
        # If job group is not specified, we want latest one
        if job_group == '':
            job_group = config.LATEST
        self.job_group = job_group
        self._cache = os.path.join(CACHEDIR, self.job_group, 'main.pickle')

        # Attempt to load data from cache
        if os.path.isfile(self._cache):
            self.data = pickle.load(open(self._cache, 'rb'))
            return

        # Load the actual data
        self.data = []
        for name, meta in config.get_builds(self.job_group).items():
            build = meta['build']
            rhel = meta['rhel']
            tier = meta['tier']
            production_log = ProductionLog(self.job_group, name, build)
            for report in self.pull_reports(name, build):
                report['tier'] = tier
                report['distro'] = rhel
                report['OBJECT:production.log'] = production_log
                self.data.append(Case(report))

        # Dump parsed data into cache
        pickle.dump(self.data, open(self._cache, 'wb'))

    def pull_reports(self, job, build):
        """
        Fetches the test report for a given job and build
        """
        build_url = '{0}/job/{1}/{2}'.format(
            config['url'], job, build)
        build_data = request_get(
            build_url+'/testReport/api/json',
            params=config['pull_params'],
            expected_codes=[200, 404],
            cached=os.path.join(CACHEDIR, self.job_group, job, 'main.json'))
        cases = json.loads(build_data)['suites'][0]['cases']

        # Enrich individual reports with URL
        for c in cases:
            className = c['className'].split('.')[-1]
            testPath = '.'.join(c['className'].split('.')[:-1])
            c['url'] = u'{0}/testReport/junit/{1}/{2}/{3}'.format(build_url, testPath, className, c['name'])

        return(cases)


class Ruleset(collections.UserList):

    def __init__(self):
        with open('kb.json', 'r') as fp:
            self.data = json.loads(fp.read())


# Create shared config file
config = Config()

def claim_by_rules(report, rules, dryrun=False):
    for rule in rules:
        for case in [i for i in report if i['status'] in Case.FAIL_STATUSES and not i['testActions'][0].get('reason')]:
            if case.matches_to_rule(rule):
                logging.info(u"{0}::{1} matching pattern for '{2}' on {3}".format(case['className'], case['name'], rule['reason'], case['url']))
                if not dryrun:
                    case.push_claim(rule['reason'])

#!/usr/bin/env python3

from __future__ import division
import os
import sys
import json
import logging
import re
import requests
import yaml
import pickle
import collections

logging.basicConfig(level=logging.INFO)

class Config(collections.UserDict):
    def __init__(self):
        with open("config.yaml", "r") as file:
            self.data = yaml.load(file)

        # If cache is configured, save it into configuration
        if 'DEBUG_CLAIMS_CACHE' in os.environ:
            self.data['cache'] = os.environ['DEBUG_CLAIMS_CACHE']
        else:
            self.data['cache'] = None


class Jenkins(object):

    PULL_PARAMS = {
        u'tree': u'suites[cases[className,duration,name,status,stdout,errorDetails,errorStackTrace,testActions[reason]]]{0}'
    }

    def __init__(self, config):
        self.config = config
        self.headers = None

    def _init_headers(self):
        requests.packages.urllib3.disable_warnings()

        # Get the Jenkins crumb (csrf protection)
        crumb_request = requests.get(
                '{0}/crumbIssuer/api/json'.format(self.config['url']),
                auth=requests.auth.HTTPBasicAuth(self.config['usr'], self.config['pwd']),
                verify=False
            )

        if crumb_request.status_code != 200:
            raise requests.HTTPError(
                'Failed to obtain crumb: {0}'.format(crumb_request.reason))

        crumb = json.loads(crumb_request.text)
        self.headers = {crumb['crumbRequestField']: crumb['crumb']}

    def pull_reports(self, job, build):
        """
        Fetches the test report for a given job and build
        """
        build_url = '{0}/job/{1}/{2}'.format(
            self.config['url'], job, build)

        logging.debug("Getting {}".format(build_url))
        bld_req = requests.get(
            build_url + '/testReport/api/json',
            auth=requests.auth.HTTPBasicAuth(
                self.config['usr'], self.config['pwd']),
            params=self.PULL_PARAMS,
            verify=False
        )

        if bld_req.status_code == 404:
            return []
        if bld_req.status_code != 200:
            raise requests.HTTPError(
                'Failed to obtain: {0}'.format(bld_req))

        cases = json.loads(bld_req.text)['suites'][0]['cases']

        # Enritch individual reports with URL
        for c in cases:
            className = c['className'].split('.')[-1]
            testPath = '.'.join(c['className'].split('.')[:-1])
            c['url'] = u'{0}/testReport/junit/{1}/{2}/{3}'.format(build_url, testPath, className, c['name'])

        return(cases)

    def push_claim(self, test, reason, sticky=False, propagate=False):
        '''Claims a given test with a given reason

        :param test: a dict test representation (need to contain the 'url' key)

        :param reason: string with a comment added to a claim (ideally this is a link to a bug or issue)

        :param sticky: whether to make the claim sticky (False by default)

        :param propagate: should jenkins auto-claim next time if same test fails again? (False by default)
        '''
        logging.info('claiming {0} with reason: {1}'.format(test["className"]+"::"+test["name"], reason))

        if self.headers is None:
            self._init_headers()

        claim_req = requests.post(
            u'{0}/claim/claim'.format(test['url']),
            auth=requests.auth.HTTPBasicAuth(
                self.config['usr'],
                self.config['pwd']
            ),
            data={u'json': u'{{"assignee": "", "reason": "{0}", "sticky": {1}, "propagateToFollowingBuilds": {2}}}'.format(reason, sticky, propagate)},
            headers=self.headers,
            allow_redirects=False,
            verify=False
        )

        if bld_req.status_code != 302:
            raise requests.HTTPError(
                'Failed to claim: {0}'.format(claim_req))

        test['testActions'][0]['reason'] = reason
        return(claim_req)



class Results(collections.UserList):

    TIERS = [1, 2, 3, 4]
    RHELS = [6, 7]
    FAIL_STATUSES = ("FAILED", "ERROR", "REGRESSION")

    def __init__(self, config, jenkins):
        self.config = config
        self.jenkins = jenkins

        # If cache is configured, load data from it
        if config['cache']:
            if os.path.isfile(config['cache']):
                logging.debug("Because cache is set to '{0}', loading data from there".format(
                    config['cache']))
                self.data = pickle.load(open(config['cache'], 'rb'))
                return
            else:
                logging.debug("Cache set to '{0}' but that file does not exist, creating one".format(
                    config['cache']))

        self.data = []
        for i in self.TIERS:
            for j in self.RHELS:
                for report in jenkins.pull_reports(
                                config['job'].format(i, j),
                                config['bld']):
                    report['tier'] = 't{}'.format(i)
                    report['distro'] = 'el{}'.format(j)
                    self.data.append(report)

        if config['cache']:
            pickle.dump(self.data, open(config['cache'], 'wb'))

    def copy(self):
        return self.__class__(self.config, self.jenkins)

    def rule_matches(self, result, rule, indentation=0):
        """
        Returns True id result matches to rule, orhervise returns False
        """
        logging.debug("%srule_matches(%s, %s, %s)" % (" "*indentation, result, rule, indentation))
        if 'field' in rule and 'pattern' in rule:
            # This is simple rule, we can just check regexp against given field and we are done
            assert rule['field'] in result
            out = re.search(rule['pattern'], result[rule['field']]) is not None
            logging.debug("%s=> %s" % (" "*indentation, out))
            return out
        elif 'AND' in rule:
            # We need to check if all sub-rules in list of rules rule['AND'] matches
            out = None
            for r in rule['AND']:
                r_out = self.rule_matches(result, r, indentation+4)
                out = r_out if out is None else out and r_out
                if not out:
                    break
            return out
        elif 'OR' in rule:
            # We need to check if at least one sub-rule in list of rules rule['OR'] matches
            for r in rule['OR']:
                if self.rule_matches(result, r, indentation+4):
                    return True
            return False
        else:
            raise Exception('Rule %s not formatted correctly' % rule)

    def claim_by_rules(self, rules, dryrun=False):
        for rule in rules:
            for result in self.get_failed():
                if self.rule_matches(result, rule):
                    logging.info(u"{0}::{1} matching pattern for '{2}' on {3}".format(result['className'], result['name'], rule['reason'], result['url']))
                    if not dryrun:
                        self.jenkins.push_claim(result, rule['reason'])

    def get_failed(self):
        """
        Return only failed results
        """
        out = self.copy()
        out.data = [i for i in self.data if i.get('status') in self.FAIL_STATUSES]
        return out

    def get_claimed(self):
        """
        Only return failed results which do not have claim/waiver
        """
        out = self.copy()
        out.data = [i for i in self.data if i.get('status') in self.FAIL_STATUSES and i['testActions'][0]['reason']]
        return out

    def get_unclaimed(self):
        """
        Only return results which do not have claim/waiver
        """
        out = self.copy()
        out.data = [i for i in self.data if i.get('status') in self.FAIL_STATUSES and not i['testActions'][0]['reason']]
        return out


class Rules(collections.UserList):

    def __init__(self):
        with open('kb.json', 'r') as fp:
            self.data = json.loads(fp.read())

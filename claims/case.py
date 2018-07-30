import collections
import re
import logging
import datetime
import requests

from .config import config


class Case(collections.UserDict):
    """
    Result of one test case
    """

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


def claim_by_rules(report, rules, dryrun=False):
    claimed = []
    for rule in rules:
        for case in [i for i in report if i['status'] in config.FAIL_STATUSES and not i['testActions'][0].get('reason')]:
            if case.matches_to_rule(rule):
                logging.debug(u"{0}::{1} matching pattern for '{2}' on {3}".format(case['className'], case['name'], rule['reason'], case['url']))
                if not dryrun:
                    case.push_claim(rule['reason'])
                claimed.append(case)
    return claimed

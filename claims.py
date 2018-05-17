from __future__ import division
import json
import logging
import re
import requests
import yaml

logger = logging.getLogger()
logger.setLevel(logging.INFO)

requests.packages.urllib3.disable_warnings()
config = {}
# load config
with open("config.yaml", "r") as file:
    try:
        config = yaml.load(file)
    except yaml.YAMLERROR as exc:
        print(exc)

FAIL_STATUSES = ("FAILED", "ERROR", "REGRESSION")
PARAMS = {
    u'tree': u'suites[cases[className,name,status,errorDetails,errorStackTrace,testActions[reason]]]{0}'
    }
ep = [u'ui', u'api', u'cli']


def fetch_test_report(url, job, build):
    bld_req = requests.get(
        u'{0}/job/{1}/{2}/testReport/api/json'.format(url, job, build),
        auth=requests.auth.HTTPBasicAuth(
            config['usr'],
            config['pwd']
        ),
        params=PARAMS,
        verify=False
    )

    if bld_req.status_code == 200:
        cases = json.loads(bld_req.text)['suites'][0]['cases']
        for c in cases:
            className = c['className'].split('.')[-1]
            testPath = '.'.join(c['className'].split('.')[:-1])
            c['url'] = u'{0}/job/{1}/{2}/testReport/junit/{3}/{4}/{5}'.format(url, job, build, testPath, className, c['name'])

        return(cases)


def fetch_all_reports(job=None, build=None):
    if job is None:
        job = config['job']
    if build is None:
        build = config['bld']
    results = {}
    for i in list(reversed(range(1, 5))):
        results['t{}'.format(i)] = {}
        for j in [6, 7]:
            job1 = job.format(i, j)
            tr = fetch_test_report(config['url'], job1, build)
            fails = tr #parse_fails(tr)
            results['t{}'.format(i)]['el{}'.format(j)] = fails
    return(results)


def flatten_reports(reports):
    """
    From tree dict like this:
        {
            'tier1': {
                'el7': [...]
            },
            ...
        }
    create a flat list of test results with distro and tier added.
    """
    reports_flat = []
    for tier in reports.keys():
        for distro in reports[tier].keys():
            if reports[tier][distro] is not None:
                for report in reports[tier][distro]:
                    report['distro'] = distro
                    report['tier'] = tier
                    reports_flat.append(report)
    return reports_flat


def filter_fails(bld):
    if not bld:
        bld = []
    return([i for i in bld if i.get('status') in FAIL_STATUSES])

# fetch_test_report(config['url'], config['job'], config['bld'])
# fetch the failed tests with claim reasons
# bld = fetch_test_report(config['url'], config['job'], config['build'])


def filter_not_claimed(reports):
    """
    Only return results which do not have claim/waiver
    """
    return [i for i in reports if not i['testActions'][0]['reason']]


def load_rules():
        with open('kb.json', 'r') as file:
            return json.loads(file.read())
            file.close()


def parse_reasons(fails, fallback=False):
    ''' parses the claim reasons from the given list of tests

    :param fails: An input list of tests
    :param fallback: Whether to replace the reason by
        the 'ErrorDetails' field if 'reason' is None
    '''
    reasons = {}
    for f in fails:
        if(fallback and not f['testActions'][0]['reason']):
            reason = unicode(f.get('errorDetails'))
        else:
            reason = unicode(f['testActions'][0]['reason'])
        if reasons.get(reason):
            reasons[reason] += 1
        else:
            reasons[reason] = 1
    return(reasons)


def get_endpoints_ratio(tests, ep):
    endpoints = {i: 0 for i in ep}
    for t in tests:
        for e in endpoints.keys():
            if u'tests.foreman.{}'.format(e) in t['className']:
                endpoints[e] += 1
    return endpoints


def get_endpoints_failure_ratio(total, fails):
    f = get_endpoints_ratio(fails, ep)
    t = get_endpoints_ratio(total, ep)
    return {i: (f[i] / t[i]) * 100 for i in ep}


def claim(test, reason, sticky=False):
    '''Claims a given test with a given reason

    :param test: a dict test representation (need to contain the 'url' key)

    :param reason: a string - reason

    :param sticky: whether to make the claim sticky (False by default)
    '''
    logger.info('claiming {0} with reason: {1}'.format(test, reason))
    claim_req = requests.post(
        u'{0}/claim/claim'.format(test['url']),
        auth=requests.auth.HTTPBasicAuth(
            config['usr'],
            config['pwd']
        ),
        data={u'json': u'{{"assignee": "", "reason": "{0}", "sticky": {1}}}'.format(reason, sticky)},
        allow_redirects=False,
        verify=False
    )
    # fixme: do a request result verification
    test['testActions'][0]['reason'] = reason
    return(claim_req)


def claim_by_rules(fails, rules):
    for rule in rules:
        for fail in [i for i in fails if re.search(rule['pattern'], i['errorDetails'])]:
            logger.info(u'{0} matching pattern: {1}'.format(fail['name'], rule['pattern']))
            claim(fail, rule['reason'])

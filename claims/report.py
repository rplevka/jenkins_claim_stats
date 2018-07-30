import os
import collections
import pickle
import json

from .config import config
from .build_logs import ProductionLog
from .utils import request_get
from .case import Case


class Report(collections.UserList):
    """
    Report is a list of Cases (i.e. test results)
    """

    def __init__(self, job_group=''):
        # If job group is not specified, we want latest one
        if job_group == '':
            job_group = config.LATEST
        self.job_group = job_group
        self._cache = os.path.join(config.CACHEDIR, self.job_group, 'main.pickle')

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
            user=config['usr'],
            password=config['pwd'],
            params=config['pull_params'],
            expected_codes=[200, 404],
            cached=os.path.join(config.CACHEDIR, self.job_group, job, 'main.json'))
        cases = json.loads(build_data)['suites'][0]['cases']

        # Enrich individual reports with URL
        for c in cases:
            className = c['className'].split('.')[-1]
            testPath = '.'.join(c['className'].split('.')[:-1])
            c['url'] = u'{0}/testReport/junit/{1}/{2}/{3}'.format(build_url, testPath, className, c['name'])

        return(cases)

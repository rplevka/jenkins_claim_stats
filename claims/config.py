import collections
import yaml
import logging


class Config(collections.UserDict):

    LATEST = 'latest'   # how do we call latest job group in the config?
    CACHEDIR = '.cache/'   # where is the cache stored

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


logging.basicConfig(level=logging.INFO)

config = Config()

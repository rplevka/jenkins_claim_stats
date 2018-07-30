import os
import re
import tempfile
import subprocess
import logging
import shutil
import datetime

from .config import config
from .utils import request_get


class ForemanDebug(object):

    def __init__(self, job_group, job, build):
        self._url = "%s/job/%s/%s/artifact/foreman-debug.tar.xz" % (config['url'], job, build)
        self._extracted = None

    @property
    def extracted(self):
        if self._extracted is None:
            fp, fname = tempfile.mkstemp()
            print(fname)
            request_get(self._url, config['usr'], config['pwd'],
                cached=fname, stream=True)
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
        self._logfile = os.path.join(config.CACHEDIR, job_group, job, 'production.log')
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

#!/usr/bin/python3

import claims

config = claims.Config()
jenkins = claims.Jenkins(config)
reports = claims.Results(config, jenkins).get_failed().get_unclaimed()

for r in reports:
    print(u'{0} {1} {2}'.format(r['distro'], r['className'], r['name']))

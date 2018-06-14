#!/usr/bin/python3

import claims

reports = claims.Report().get_unclaimed()

for r in reports:
    print(u'{0} {1} {2}'.format(r['distro'], r['className'], r['name']))

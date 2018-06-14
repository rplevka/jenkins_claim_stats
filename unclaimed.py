#!/usr/bin/python3

import claims

reports = [i for i in claims.Report() if i['status'] in claims.Case.FAIL_STATUSES and not i['testActions'][0].get('reason')]

for r in reports:
    print(u'{0} {1} {2}'.format(r['distro'], r['className'], r['name']))

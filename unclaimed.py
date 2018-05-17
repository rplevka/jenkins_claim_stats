#!/usr/bin/python

import claims

reports = claims.fetch_all_reports()
reports = claims.flatten_reports(reports)
reports = claims.filter_fails(reports)
reports = claims.filter_not_claimed(reports)

for r in reports:
    print(u'{0} {1} {2}'.format(r['distro'], r['className'], r['name']))

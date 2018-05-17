#!/usr/bin/python

import claims

reports = claims.fetch_all_reports()
fails = []

tiers = reports.keys()
distros = reports[tiers[0]].keys()

for i in tiers:
     for j in reports[i].keys():
         fs = claims.filter_fails(reports[i][j])
         for f in fs:
             f['distro'] = j
             f['tier'] = i
         fails += fs

unclaimed = [i for i in fails if not i['testActions'][0]['reason']]

for i in tiers:
    print(i)
    fls = [f for f in unclaimed if f['tier'] is i]
    for j in distros:
        print(i)
        for k in [f for f in fls if f['distro'] == j]:
            #print(k['url'])
            print(u'{0} {1} {2}'.format(j, k['className'], k['name']))
    print

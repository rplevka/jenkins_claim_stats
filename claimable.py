#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import claims

report = claims.Report()
rules = claims.Ruleset()

#report = [r for r in report if r['name'] == 'test_positive_create_with_puppet_class_id']
#rules = [r for r in rules if r['reason'] == 'https://github.com/SatelliteQE/robottelo/issues/6115']

claims.claim_by_rules(report, rules, dryrun=True)

for case in [i for i in report if i['status'] in claims.Case.FAIL_STATUSES]:
    print(case['url'])

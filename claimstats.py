#!/usr/bin/env python3

import claims
import tabulate

config = claims.Config()
jenkins = claims.Jenkins(config)
reports = claims.Results(config, jenkins)

stat_all = len(reports)
reports_fails = reports.get_failed()
stat_failed = len(reports_fails)
reports_claimed = reports.get_claimed()
stat_claimed = len(reports_claimed)

print("\nOverall stats")
print(tabulate.tabulate(
    [[stat_all, stat_failed, stat_claimed]],
    headers=['all reports', 'failures', 'claimed failures']))

rules = claims.Rules()
rules_reasons = [r['reason'] for r in rules]
reports_per_reason = {'UNKNOWN': stat_failed-stat_claimed}
reports_per_reason.update({r:0 for r in rules_reasons})
for report in reports_claimed:
    reason = report['testActions'][0]['reason']
    if reason not in reports_per_reason:
        reports_per_reason[reason] = 0
    reports_per_reason[reason] += 1

print("\nHow various reasons for claims are used")
reports_per_reason = sorted(reports_per_reason.items(), key=lambda x: x[1], reverse=True)
reports_per_reason = [(r, c, r in rules_reasons) for r, c in reports_per_reason]
print(tabulate.tabulate(
    reports_per_reason,
    headers=['claim reason', 'number of times', 'is it in current knowleadgebase?']))

reports_per_class = {}
for report in reports:
    class_name = report['className']
    if class_name not in reports_per_class:
        reports_per_class[class_name] = {'all': 0, 'failed': 0}
    reports_per_class[class_name]['all'] += 1
    if report in reports_fails:
        reports_per_class[class_name]['failed'] += 1

print("\nHow many failures are there per class")
print(tabulate.tabulate(
    sorted([(c, r['all'], r['failed'], float(r['failed'])/r['all']) for c,r in reports_per_class.items()],
        key=lambda x: x[3], reverse=True),
    headers=['class name', 'number of reports', 'number of failures', 'failures ratio'],
    floatfmt=".3f"))

reports_per_method = {}
for report in reports:
    method = report['className'].split('.')[2]
    if method not in reports_per_method:
        reports_per_method[method] = {'all': 0, 'failed': 0}
    reports_per_method[method]['all'] += 1
    if report in reports_fails:
        reports_per_method[method]['failed'] += 1

print("\nHow many failures are there per method (CLI vs. API vs. UI)")
print(tabulate.tabulate(
    sorted([(c, r['all'], r['failed'], float(r['failed'])/r['all']) for c,r in reports_per_method.items()],
        key=lambda x: x[3], reverse=True),
    headers=['method', 'number of reports', 'number of failures', 'failures ratio'],
    floatfmt=".3f"))

#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import datetime
import collections
import statistics
import tabulate
import csv
import claims

BUILDS = [22, 21, 19, 18, 17, 14, 13, 12, 10, 9, 8, 7, 6]
matrix = collections.OrderedDict()


def sanitize_state(state):
    if state == 'REGRESSION':
        state = 'FAILED'
    if state == 'FIXED':
        state = 'PASSED'
    if state == 'PASSED':
        return 0
    if state == 'FAILED':
        return 1
    raise KeyError("Do not know how to handle state %s" % state)


for build_id in range(len(BUILDS)):
    build = BUILDS[build_id]
    claims.config['bld'] = build
    claims.config['cache'] = 'cache-%s-%s.pickle' \
        % (datetime.datetime.now().strftime('%Y%m%d'), build)
    logging.info("Initializing report for build %s with cache in %s" \
        % (build, claims.config['cache']))
    #report = [i for i in claims.Report() if i['tier'] == 't4']
    report = claims.Report()
    for r in report:
        t = "%s::%s@%s" % (r['className'], r['name'], r['distro'])
        if t not in matrix:
            matrix[t] = [None for i in BUILDS]
        try:
            state = sanitize_state(r['status'])
        except KeyError:
            continue
        matrix[t][build_id] = state

# Count statistical measure of the results
for k,v in matrix.items():
    try:
        stdev = statistics.pstdev([i for i in v if i is not None])
    except statistics.StatisticsError:
        stdev = None
    v.append(stdev)
    try:
        stdev = statistics.pstdev([i for i in v[:3] if i is not None])
    except statistics.StatisticsError:
        stdev = None
    v.append(stdev)

print("Legend:\n    0 ... PASSED or FIXED\n    1 ... FAILED or REGRESSION\n    Population standard deviation, 0 is best (stable), 0.5 is worst (unstable)\n    Same but only for newest 3 builds")
matrix_flat = [[k]+v for k,v in matrix.items()]
headers = ['test']+BUILDS+['pstdev (all)', 'pstdev (3 newest)']
print(tabulate.tabulate(
    matrix_flat,
    headers=headers,
    floatfmt=".3f"
))

filename = "/tmp/tests-stability.csv"
print("Writing data to %s" % filename)
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([headers])
    writer.writerows(matrix_flat)

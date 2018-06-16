#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import datetime
import svgwrite
import claims


STATUS_COLOR = {
'FAILED': 'red',
'FIXED': 'blue',
'PASSED': 'green',
'REGRESSION': 'purple',
'SKIPPED': 'fuchsia',
}
LANE_HEIGHT = 10
LANES_START = LANE_HEIGHT   # we will place a timeline into the first lane
HOUR = 3600
X_CONTRACTION = 0.1


def overlaps(a, b):
    """
    Return true if two intervals overlap:
        overlaps((1, 3), (2, 10)) => True
        overlaps((1, 3), (5, 10)) => False
    """
    if b[0] <= a[0] <= b[1] or b[0] <= a[1] <= b[1]:
        return True
    else:
        return False


def scale(a):
    return (a[0] * X_CONTRACTION, a[1])


reports = [i for i in claims.Report() if i['tier'] == 't4']

# Load all the reports and sort them in lanes
###counter = 0
lanes = []
start = None
end = None
for r in reports:
    # Get start and end time. If unknown, skip the result
    try:
        r_start = r['start'].timestamp()
        r_end = r['end'].timestamp()
    except KeyError:
        logging.info("No start time for %s::%s" % (r['className'], r['name']))
        continue
    # Find overal widtht of time line
    if start is None or r_start < start:
        logging.debug("Test %s started before current minimum of %s" % (r['name'], start))
        start = r_start
    if end is None or r_end > end:
        end = r_end
    r['interval'] = (r_start, r_end)
    # Check if there is a free lane for us, if not, create a new one
    lane_found = False
    for lane in lanes:
        lane_found = True
        for interval in lane:
            if overlaps(r['interval'], interval['interval']):
                lane_found = False
                break
        if lane_found:
            break
    if not lane_found:
        logging.debug("Adding lane %s" % (len(lanes)+1))
        lane = []
        lanes.append(lane)
    lane.append(r)
    ###counter += 1
    ###if counter > 10: break

# Create a drawing with timeline
dwg = svgwrite.Drawing('/tmp/rungraph.svg',
    size=scale((end-start, LANE_HEIGHT*(len(lanes)+1))))
dwg.add(dwg.line(
    scale((0, LANE_HEIGHT)),
    scale((end-start, LANE_HEIGHT)),
    style="stroke: black; stroke-width: 1;"
))
start_full_hour = int(start / HOUR) * HOUR
timeline = start_full_hour - start
while start + timeline <= end:
    if timeline >= 0:
        dwg.add(dwg.line(
            scale((timeline, LANE_HEIGHT)),
            scale((timeline, 2*LANE_HEIGHT/3)),
            style="stroke: black; stroke-width: 1;"
        ))
        dwg.add(dwg.text(
            datetime.datetime.fromtimestamp(start+timeline) \
                .strftime('%Y-%m-%d %H:%M:%S'),
            insert=scale((timeline, 2*LANE_HEIGHT/3)),
            style="fill: black; font-size: 3pt;"
        ))
    timeline += HOUR/4

# Draw tests
for lane_no in range(len(lanes)):
    for r in lanes[lane_no]:
        logging.debug("In lane %s adding %s::%s %s" \
            % (lane_no, r['className'], r['name'], r['interval']))
        s, e = r['interval']
        dwg.add(dwg.rect(
            insert=scale((s - start, LANES_START + LANE_HEIGHT*lane_no + LANE_HEIGHT/2)),
            size=scale((e - s, LANE_HEIGHT/2)),
            style="fill: %s; stroke: %s; stroke-width: 0;" \
                % (STATUS_COLOR[r['status']], STATUS_COLOR[r['status']])
        ))
        dwg.add(dwg.text(
            "%s::%s" % (r['className'], r['name']),
            insert=scale((s - start, LANES_START + LANE_HEIGHT*lane_no + LANE_HEIGHT/2)),
            transform="rotate(-30, %s, %s)" \
                % scale((s - start, LANES_START + LANE_HEIGHT*lane_no + LANE_HEIGHT/2)),
            style="fill: gray; font-size: 2pt;"
        ))
dwg.save()

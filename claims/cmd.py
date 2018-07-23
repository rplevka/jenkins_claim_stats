#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os.path
import sys
import logging
import argparse
import re
import tabulate
import csv
import collections
import statistics
import shutil

import lib

logging.basicConfig(level=logging.INFO)


class ClaimsCli(object):

    LATEST = 'latest'

    def __init__(self):
        self.job_group = self.LATEST
        self.grep_results = None
        self.grep_rules = None
        self._results = None
        self._rules = None

    @property
    def results(self):
        if not self._results:
            self._results = {}
        if self.job_group not in self._results:
            self._results[self.job_group] = lib.Report(self.job_group)
            if self.grep_results:
                self._results[self.job_group] = [r for r in self._results[self.job_group] if re.search(self.grep_results, "%s.%s" % (r['className'], r['name']))]
        return self._results[self.job_group]

    @property
    def rules(self):
        if not self._rules:
            self._rules = lib.Ruleset()
            if self.grep_rules:
                self._rules = [r for r in self._rules if re.search(self.grep_rules, r['reason'])]
        return self._rules

    def _table(self, data, headers=[], tablefmt=None, floatfmt='%.01f'):
        if self.output == 'csv':
            writer = csv.writer(sys.stdout)
            if headers:
                writer.writerow(headers)
            for row in data:
                writer.writerow(row)
        else:
            print(tabulate.tabulate(
                data,
                headers=headers,
                floatfmt=floatfmt,
                tablefmt=self.output))

    def clean_cache(self):
        d = os.path.join(lib.CACHEDIR, self.job_group)
        try:
            shutil.rmtree(d)
            logging.info("Removed %s" % d)
        except FileNotFoundError:
            pass

    def show_failed(self):
        self._table(
            [[r['testName']] for r in self.results if r['status'] in lib.Case.FAIL_STATUSES],
            headers=['failed test name'], tablefmt=self.output)

    def show_claimed(self):
        self._table(
            [[r['testName'], r['testActions'][0].get('reason')] for r in self.results if r['status'] in lib.Case.FAIL_STATUSES and r['testActions'][0].get('reason')],
            headers=['claimed test name', 'claim reason'], tablefmt=self.output)

    def show_unclaimed(self):
        self._table(
            [[r['testName']] for r in self.results if r['status'] in lib.Case.FAIL_STATUSES and not r['testActions'][0].get('reason')],
            headers=['unclaimed test name'], tablefmt=self.output)

    def show_claimable(self):
        claimable = lib.claim_by_rules(self.results, self.rules, dryrun=True)
        self._table(
            [[r['testName']] for r in claimable],
            headers=['claimable test name'], tablefmt=self.output)

    def show(self, test_class, test_name):
        MAXWIDTH = 100
        FIELDS_EXTRA = ['start', 'end', 'production.log']
        FIELDS_SKIP = ['OBJECT:production.log']
        data = []
        for r in self.results:
            if r['className'] == test_class and r['name'] == test_name:
                for k in sorted(r.keys()) + FIELDS_EXTRA:
                    if k in FIELDS_SKIP:
                        continue
                    v = r[k]
                    print("%s:" % k)
                    if isinstance(v, str):
                        for row in v.split("\n"):
                            if k == 'url':
                                print(" "*len(k), row)
                            if k == 'production.log' and len(row) == 0:
                                continue
                            width = len(row)
                            printed = MAXWIDTH
                            print(" "*len(k), row[0:MAXWIDTH])
                            while printed < width:
                                print(" "*(len(k)+4), row[printed:printed+MAXWIDTH-4])
                                printed += len(row[printed:printed+MAXWIDTH-4])
                break

    def claim(self):
        claimed = lib.claim_by_rules(self.results, self.rules, dryrun=False)
        self._table(
            [[r['testName']] for r in claimed],
            headers=['claimed test name'], tablefmt=self.output)

    def stats(self):
        def _perc(perc_from, perc_sum):
            """Just a shortcur to safely count percentage"""
            try:
                return float(perc_from)/perc_sum*100
            except ZeroDivisionError:
                return None

        stat_all = len(self.results)
        reports_fails = [i for i in self.results if i['status'] in lib.Case.FAIL_STATUSES]
        stat_failed = len(reports_fails)
        reports_claimed = [i for i in reports_fails if i['testActions'][0].get('reason')]
        stat_claimed = len(reports_claimed)

        stats_all = ['TOTAL', stat_all, stat_failed, _perc(stat_failed, stat_all), stat_claimed, _perc(stat_claimed, stat_failed)]

        stats = []
        for t in [i['tier'] for i in lib.config.get_builds(self.job_group).values()]:
            filtered = [r for r in self.results if r['tier'] == t]
            stat_all_tiered = len(filtered)
            reports_fails_tiered = [i for i in filtered if i['status'] in lib.Case.FAIL_STATUSES]
            stat_failed_tiered = len(reports_fails_tiered)
            reports_claimed_tiered = [i for i in reports_fails_tiered if i['testActions'][0].get('reason')]
            stat_claimed_tiered = len(reports_claimed_tiered)
            stats.append(["t%s" % t, stat_all_tiered, stat_failed_tiered, _perc(stat_failed_tiered, stat_all_tiered), stat_claimed_tiered, _perc(stat_claimed_tiered, stat_failed_tiered)])

        print("\nOverall stats")
        self._table(
            stats + [stats_all],
            headers=['tier', 'all reports', 'failures', 'failures [%]', 'claimed failures', 'claimed failures [%]'],
            floatfmt=".01f",
            tablefmt=self.output)

        reports_per_method = {}
        for report in self.results:
            method = report['className'].split('.')[2]
            if method not in reports_per_method:
                reports_per_method[method] = {'all': 0, 'failed': 0, 'claimed': 0}
            reports_per_method[method]['all'] += 1
            if report in reports_fails:
                reports_per_method[method]['failed'] += 1
            if report in reports_claimed:
                reports_per_method[method]['claimed'] += 1

        print("\nHow many failures are there per endpoint")
        self._table(
            sorted([(c, r['all'], r['failed'], _perc(r['failed'], r['all']), r['claimed'], _perc(r['claimed'], r['failed'])) for c,r in reports_per_method.items()],
                key=lambda x: x[3], reverse=True) + [stats_all],
            headers=['method', 'all reports', 'failures', 'failures [%]', 'claimed failures', 'claimed failures [%]'],
            floatfmt=".1f",
            tablefmt=self.output)

        rules_reasons = [r['reason'] for r in self.rules]
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
        self._table(
            reports_per_reason,
            headers=['claim reason', 'claimed times', 'claiming automated?'],
            tablefmt=self.output)

        reports_per_class = {}
        for report in self.results:
            class_name = report['className']
            if class_name not in reports_per_class:
                reports_per_class[class_name] = {'all': 0, 'failed': 0}
            reports_per_class[class_name]['all'] += 1
            if report in reports_fails:
                reports_per_class[class_name]['failed'] += 1

        print("\nHow many failures are there per class")
        self._table(
            sorted([(c, r['all'], r['failed'], _perc(r['failed'], r['all'])) for c,r in reports_per_class.items()],
                key=lambda x: x[3], reverse=True),
            headers=['class name', 'number of reports', 'number of failures', 'failures ratio'],
            floatfmt=".1f",
            tablefmt=self.output)

    def history(self):

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

        matrix = collections.OrderedDict()

        # Load tests results
        job_groups = lib.config['job_groups'].keys()
        for job_group in job_groups:
            logging.info('Loading job group %s' % job_group)
            self.job_group = job_group
            report = self.results
            for r in report:
                t = "%s::%s@%s" % (r['className'], r['name'], r['distro'])
                if t not in matrix:
                    matrix[t] = dict.fromkeys(job_group)
                try:
                    state = sanitize_state(r['status'])
                except KeyError:
                    continue   # e.g. state "SKIPPED"
                matrix[t][job_group] = state

        # Count statistical measure of the results
        for k,v in matrix.items():
            try:
                stdev = statistics.pstdev([i for i in v.values() if i is not None])
            except statistics.StatisticsError:
                stdev = None
            v['stdev'] = stdev

        print("Legend:\n    0 ... PASSED or FIXED\n    1 ... FAILED or REGRESSION\n    Population standard deviation, 0 is best (stable), 0.5 is worst (unstable)")
        headers = ['test'] + list(job_groups) + ['pstdev (all)']
        matrix_flat = []
        for k,v in matrix.items():
            v_list = []
            for job_group in job_groups:
                if job_group in v:
                    v_list.append(v[job_group])
                else:
                    v_list.append(None)
            matrix_flat.append([k]+v_list+[v['stdev']])
        self._table(
            matrix_flat,
            headers=headers,
            floatfmt=".3f"
        )

    def handle_args(self):
        parser = argparse.ArgumentParser(description='Manipulate Jenkins claims with grace')

        # Actions
        parser.add_argument('--clean-cache', action='store_true',
                            help='Cleans cache for job group provided by "--job-group" option (default: latest)')
        parser.add_argument('--show-failed', action='store_true',
                            help='Show all failed tests')
        parser.add_argument('--show-claimed', action='store_true',
                            help='Show claimed tests')
        parser.add_argument('--show-unclaimed', action='store_true',
                            help='Show failed and not yet claimed tests')
        parser.add_argument('--show-claimable', action='store_true',
                            help='Show failed, not yet claimed but claimable tests')
        parser.add_argument('--show', action='store',
                            help='Show detailed info about given test case')
        parser.add_argument('--claim', action='store_true',
                            help='Claim claimable tests')
        parser.add_argument('--stats', action='store_true',
                            help='Show stats for selected job group')
        parser.add_argument('--history', action='store_true',
                            help='Show how tests results and duration evolved')
        parser.add_argument('--timegraph', action='store_true',
                            help='Generate time graph')

        # Modifiers
        parser.add_argument('--job-group', action='store',
                            help='Specify group of jobs to perform the action with (default: latest)')
        parser.add_argument('--grep-results', action='store', metavar='REGEXP',
                            help='Only work with tests, whose "className+name" matches the regexp')
        parser.add_argument('--grep-rules', action='store', metavar='REGEXP',
                            help='Only work with rules, whose reason matches the regexp')
        parser.add_argument('--output', action='store', choices=['simple', 'csv', 'html'], default='simple',
                            help='Format tables as plain, csv or html (default: simple)')
        parser.add_argument('-d', '--debug', action='store_true',
                            help='Show also debug messages')

        args = parser.parse_args()
        print(args)

        # Handle "--debug"
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug mode enabled")

        # Handle "--job-group something"
        if args.job_group:
            self.job_group = args.job_group
        logging.debug("Job group we are going to work with is %s" % self.job_group)

        # Handle "--grep-results something"
        if args.grep_results:
            self.grep_results = args.grep_results
            logging.debug("Going to consider only results matching %s" % self.grep_results)

        # Handle "--grep-rules something"
        if args.grep_rules:
            self.grep_rules = args.grep_rules
            logging.debug("Going to consider only rules matching %s" % self.grep_rules)

        # Handle "--output something"
        self.output = args.output
        logging.debug("Using output type %s" % self.output)

        # Actions

        # Clean cache
        if args.clean_cache:
            self.clean_cache()

        # Show failed
        if args.show_failed:
            self.show_failed()

        # Show claimed
        elif args.show_claimed:
            self.show_claimed()

        # Show unclaimed
        elif args.show_unclaimed:
            self.show_unclaimed()

        # Show claimable
        elif args.show_claimable:
            self.show_claimable()

        # Show test details
        elif args.show:
            self.grep_results = None   # to be sure we will not be missing the test because of filtering
            class_name = '.'.join(args.show.split('.')[:-1])
            name = args.show.split('.')[-1]
            self.show(class_name, name)

        # Do a claim work
        elif args.claim:
            self.claim()

        # Show statistics
        elif args.stats:
            self.stats()

        # Show tests history
        elif args.history:
            self.history()

        return 0

def main():
    """Main program"""
    return ClaimsCli().handle_args()

if __name__ == "__main__":
    main()

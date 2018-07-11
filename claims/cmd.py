#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import argparse
import re
import tabulate

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
            self._results = lib.Report(self.job_group)
            if self.grep_results:
                self._results = [r for r in self._results if re.search(self.grep_results, "%s.%s" % (r['className'], r['name']))]
        return self._results

    def show_failed(self):
        print(tabulate.tabulate(
            [[r['testName']] for r in self.results if r['status'] in lib.Case.FAIL_STATUSES],
            headers=['failed test name'], tablefmt=self.output))

    def show_claimed(self):
        print(tabulate.tabulate(
            [[r['testName'], r['testActions'][0].get('reason')] for r in self.results if r['status'] in lib.Case.FAIL_STATUSES and r['testActions'][0].get('reason')],
            headers=['claimed test name', 'claim reason'], tablefmt=self.output))

    def show_unclaimed(self):
        print(tabulate.tabulate(
            [[r['testName']] for r in self.results if r['status'] in lib.Case.FAIL_STATUSES and not r['testActions'][0].get('reason')],
            headers=['unclaimed test name'], tablefmt=self.output))

    def handle_args(self):
        parser = argparse.ArgumentParser(description='Manipulate Jenkins claims with grace')

        # Actions
        parser.add_argument('--clean-cache', action='store_true',
                            help='Cleans cache for latest job group. If you want to clean cache for older job group, use rm in .cache directory')
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

        # Show failed
        if args.show_failed:
            self.show_failed()
            return 0

        # Show claimed
        if args.show_claimed:
            self.show_claimed()
            return 0

        # Show unclaimed
        if args.show_unclaimed:
            self.show_unclaimed()
            return 0

        return 0

def main():
    """Main program"""
    return ClaimsCli().handle_args()

if __name__ == "__main__":
    main()

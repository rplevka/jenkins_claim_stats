#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import claims

reports = claims.fetch_all_reports()
reports = claims.flatten_reports(reports)
reports = claims.filter_fails(reports)
reports = claims.filter_not_claimed(reports)

rules = claims.load_rules()

claims.claim_by_rules(reports, rules, dryrun=True)

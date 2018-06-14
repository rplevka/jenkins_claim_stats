#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import claims

report = claims.Report()
rules = claims.Ruleset()

claims.claim_by_rules(report, rules, dryrun=True)

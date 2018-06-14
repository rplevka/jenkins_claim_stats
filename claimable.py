#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import claims

results = claims.Report()
rules = claims.Ruleset()

claims.claim_by_rules(results, rules, dryrun=False)

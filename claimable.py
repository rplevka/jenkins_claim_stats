#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import claims

config = claims.Config()
jenkins = claims.Jenkins(config)
results = claims.Report(config, jenkins).get_failed().get_unclaimed()
rules = claims.Ruleset()

results.claim_by_rules(rules, dryrun=False)

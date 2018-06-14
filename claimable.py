#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import claims

config = claims.Config()
jenkins = claims.Jenkins(config)
results = claims.Results(config, jenkins).get_failed().get_unclaimed()
rules = claims.Rules()

results.claim_by_rules(rules, dryrun=False)

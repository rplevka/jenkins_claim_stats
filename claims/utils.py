#!/usr/bin/env python3

from __future__ import division
import os
import logging
import urllib3
import requests

from .config import config
from .case import Case


def request_get(url, params=None, expected_codes=[200], cached=True, stream=False):
    # If available, read it from cache
    if cached and not stream and os.path.isfile(cached):
        with open(cached, 'r') as fp:
            return fp.read()

    # Get the response from the server
    urllib3.disable_warnings()
    response = requests.get(
        url,
        auth=requests.auth.HTTPBasicAuth(
            config['usr'], config['pwd']),
        params=params,
        verify=False
    )

    # Check we got expected exit code
    if response.status_code not in expected_codes:
        raise requests.HTTPError("Failed to get %s with %s" % (url, response.status_code))

    # If we were streaming file
    if stream:
        with open(cached, 'w+b') as fp:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:   # filter out keep-alive new chunks
                    fp.write(chunk)
            fp.close()
        return

    # In some cases 404 just means "we have nothing"
    if response.status_code == 404:
        return ''

    # If cache was configured, dump data in there
    if cached:
        os.makedirs(os.path.dirname(cached), exist_ok=True)
        with open(cached, 'w') as fp:
            fp.write(response.text)

    return response.text


def claim_by_rules(report, rules, dryrun=False):
    claimed = []
    for rule in rules:
        for case in [i for i in report if i['status'] in Case.FAIL_STATUSES and not i['testActions'][0].get('reason')]:
            if case.matches_to_rule(rule):
                logging.debug(u"{0}::{1} matching pattern for '{2}' on {3}".format(case['className'], case['name'], rule['reason'], case['url']))
                if not dryrun:
                    case.push_claim(rule['reason'])
                claimed.append(case)
    return claimed

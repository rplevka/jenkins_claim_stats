#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import tempfile
import pytest

import claims.lib

class TestClaimsRequestWrapper():

    def test_get_sanity(self):
        a = claims.lib.request_get('http://inecas.fedorapeople.org/fakerepos/zoo3/repodata/repomd.xml', cached=False)
        b = claims.lib.request_get('http://inecas.fedorapeople.org/fakerepos/zoo3/repodata/repomd.xml', params=None, expected_codes=[200], cached=False)
        assert a == b
        with pytest.raises(requests.HTTPError) as e:
            claims.lib.request_get('http://inecas.fedorapeople.org/fakerepos/zoo3/repodata/repomd.xml', params=None, expected_codes=[404], cached=False)

    def test_get_caching(self):
        fp, fname = tempfile.mkstemp()
        a = claims.lib.request_get('http://inecas.fedorapeople.org/fakerepos/zoo3/repodata/repomd.xml', cached=fname)
        b = claims.lib.request_get('http://inecas.fedorapeople.org/fakerepos/zoo3/repodata/repomd.xml', cached=fname)
        assert a == b

#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import pytest

import io
from contextlib import redirect_stdout

import claims.cmd

class TestClaimsCli(object):

    def test_help(self):
        sys.argv = ['./something.py', '--help']
        f = io.StringIO()
        with pytest.raises(SystemExit) as e:
            with redirect_stdout(f):
                claims.cmd.main()
        assert e.value.code == 0
        assert 'Manipulate Jenkins claims with grace' in f.getvalue()
        assert 'optional arguments:' in f.getvalue()

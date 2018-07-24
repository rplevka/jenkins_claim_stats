
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pytest

import claims.timegraph

class TestTimegraph():

    def test_overlaps(self):
        assert claims.timegraph.overlaps((1, 3), (2, 10)) == True
        assert claims.timegraph.overlaps((1, 3), (5, 10)) == False

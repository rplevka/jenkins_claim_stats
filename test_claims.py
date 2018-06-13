#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import claims

checkme = {
    'greeting': 'Hello world',
    'area': 'IT Crowd',
}

assert claims.rule_matches(checkme, {'field': 'greeting', 'pattern': 'Hel+o'}) == True
assert claims.rule_matches(checkme, {'field': 'greeting', 'pattern': 'This is not there'}) == False
assert claims.rule_matches(checkme, {'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'field': 'greeting', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}]}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}]}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}]}) == False
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'IT'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'This is not there'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'This is not there'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'IT'}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'OR': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}, {'AND': [{'field': 'area', 'pattern': 'IT'}]}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'AND': [{'field': 'area', 'pattern': 'IT'}]}]}) == True
assert claims.rule_matches(checkme, {'OR': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'AND': [{'field': 'area', 'pattern': 'This is not there'}]}]}) == False
assert claims.rule_matches(checkme, {'OR': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'OR': [{'field': 'greeting', 'pattern': 'Hel*o'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
assert claims.rule_matches(checkme, {'AND': [{'OR': [{'field': 'greeting', 'pattern': 'Hel*o'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'IT'}]}) == True
assert claims.rule_matches(checkme, {'AND': [{'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'IT'}]}) == True

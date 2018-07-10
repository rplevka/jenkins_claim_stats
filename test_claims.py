#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import claims

def test_rule_matches():
    checkme = {
        'name': 'test',
        'greeting': 'Hello world',
        'area': 'IT Crowd',
    }
    result = claims.Case(checkme)

    assert result.matches_to_rule({'field': 'greeting', 'pattern': 'Hel+o'}) == True
    assert result.matches_to_rule({'field': 'greeting', 'pattern': 'This is not there'}) == False
    assert result.matches_to_rule({'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}]}) == True
    assert result.matches_to_rule({'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}) == True
    assert result.matches_to_rule({'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}) == True
    assert result.matches_to_rule({'AND': [{'field': 'greeting', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'AND': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}]}]}) == True
    assert result.matches_to_rule({'AND': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}]}) == True
    assert result.matches_to_rule({'AND': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}]}) == True
    assert result.matches_to_rule({'AND': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}]}]}) == False
    assert result.matches_to_rule({'AND': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}]}) == False
    assert result.matches_to_rule({'AND': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}]}) == False
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'IT'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'IT'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}, {'field': 'area', 'pattern': 'This is not there'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'This is not there'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'IT'}]}) == True
    assert result.matches_to_rule({'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'OR': [{'AND': [{'field': 'greeting', 'pattern': 'Hel+o'}, {'field': 'greeting', 'pattern': 'world'}]}, {'AND': [{'field': 'area', 'pattern': 'IT'}]}]}) == True
    assert result.matches_to_rule({'OR': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'AND': [{'field': 'area', 'pattern': 'IT'}]}]}) == True
    assert result.matches_to_rule({'OR': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'AND': [{'field': 'area', 'pattern': 'This is not there'}]}]}) == False
    assert result.matches_to_rule({'OR': [{'AND': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'AND': [{'OR': [{'field': 'greeting', 'pattern': 'Hel*o'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'This is not there'}]}) == False
    assert result.matches_to_rule({'AND': [{'OR': [{'field': 'greeting', 'pattern': 'Hel*o'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'IT'}]}) == True
    assert result.matches_to_rule({'AND': [{'OR': [{'field': 'greeting', 'pattern': 'This is not there'}, {'field': 'greeting', 'pattern': 'world'}]}, {'field': 'area', 'pattern': 'IT'}]}) == True

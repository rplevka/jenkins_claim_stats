import collections
import json


class Ruleset(collections.UserList):

    def __init__(self):
        with open('kb.json', 'r') as fp:
            self.data = json.loads(fp.read())

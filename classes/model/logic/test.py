import sys

class Model_Logic_Test:
    def __init__(self, name):
        self.name = name;
    def test (self, args):
        return self.name;
    def error1 (self, args):
        return 'error';
# coding=utf-8
import sys

class Sample_Basic_Test:
    def __init__(self, name):
        self.name = name;
    def greet (self, greet):
        return greet + ' ' + self.name;
    def add (self, x, y):
        return x + y;
    def ok (self):
        return {'err':'ok', 'msg':unicode("测试", "gbk")};
    def arr (self):
        return [1,2,3,4];

    def obj(self):
        return self;

    @classmethod
    def greet_static(cls):
        return "Hello World";
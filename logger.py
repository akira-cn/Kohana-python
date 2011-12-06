# coding=utf-8

import logging
import logging.handlers
import datetime

logging.basicConfig()

class logger():
    def __init__(self, name = 'default'):
        self.name = name
    def instance(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(thread)d %(asctime)s %(levelname)s %(message)s')
        filehandler = logging.handlers.TimedRotatingFileHandler(
            "logs/log", 'D', 1, 0)
        filehandler.suffix = "%Y-%m-%d"
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)
        return logger
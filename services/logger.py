#!/usr/bin/python
# coding: utf8

import sys
import os
import logging
import logging.config
from config import configs

logging_config = dict(
    version=1,
    formatters={
        'default': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'access': {
            'format': '%(message)s'
        }
    },
    handlers={
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout,
            'level': 'DEBUG',
        },
        'error_log': {
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'default',
            'filename': "%s/app.error.log" % configs["LOG_DIR"],
            'level': 'WARNING',
        },
        'log': {
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'default',
            'filename': '%s/app.info.log' % configs["LOG_DIR"],
            'level': 'INFO',
        }

    },
    loggers={
        'db': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        },
        'uicr': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        },
        'docker': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        },
        'rabbitmq': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        },
        'minio': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        },
        'launcher': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        },
        'execute': {
            'handlers': ['stdout', 'error_log', 'log'],
            'level': "DEBUG",
            'propagate': 0
        }
    },
    root={
        'handlers': ['stdout', 'error_log', 'log'],
        'level': 'DEBUG',
    },
)


class Logger:
    def __init__(self, logger=None):
        os.makedirs(configs["LOG_DIR"], exist_ok=True)
        logging.config.dictConfig(logging_config)
        self.logger = logging.getLogger(logger)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

    def exception(self, msg):
        self.logger.exception(msg)


if __name__ == '__main__':
    logger = Logger("db")
    logger.debug("test db debug logger...")
    logger.info("test db info logger...")
    logger.warning("test db warning logger...")
    logger.error("test db error logger...")

import logging
from logstash_async.handler import AsynchronousLogstashHandler
from config import LOGS_CONFIG


class CustomLoggerFilter(logging.Filter):
    def filter(self, log):
        return True


def create_logger(name, level=LOGS_CONFIG["base_level"]):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addFilter(CustomLoggerFilter())
        add_console_logger(logger)

        if LOGS_CONFIG["logstash"]["enabled"]:
            add_logstash_logger(logger)

    logger.propagate = False
    return logger


def add_console_logger(logger, level=LOGS_CONFIG["base_level"]):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOGS_CONFIG["console"]["format"]))
    logger.addHandler(console_handler)


def add_logstash_logger(logger, level=LOGS_CONFIG["base_level"]):
    logstash_handler = AsynchronousLogstashHandler(
        host=LOGS_CONFIG["logstash"]["host"],
        port=LOGS_CONFIG["logstash"]["port"],
        version=LOGS_CONFIG["logstash"]["version"],
        level=level,
    )
    logger.addHandler(logstash_handler)

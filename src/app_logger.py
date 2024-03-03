import logging
from logging.handlers import TimedRotatingFileHandler

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

log_level = logging.INFO
loggers = []
log_rotation_handler = TimedRotatingFileHandler('/var/log/pyalerts/execution.log', when="midnight", interval=1, backupCount=10, encoding='utf-8')
log_rotation_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
log_rotation_handler.setLevel(logging.DEBUG)


def set_log_level(level):
    global log_level
    log_level = level
    for logger in loggers:
        logger.setLevel(log_level)


def get(name):
    global log_level
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    loggers.append(logger)
    return logger


def get_persistent(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        logger.removeHandler(handler)
    logger.addHandler(log_rotation_handler)
    return logger

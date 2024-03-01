import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

log_level = logging.INFO
loggers = []


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

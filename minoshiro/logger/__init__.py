"""
A basic logger
"""
from logging import Formatter, INFO, StreamHandler, getLogger


def get_default_logger():
    """
    Return a basic default logger.

    :return:
        A basic logger with a `StreamHandler` attatched and with level `INFO`
    """
    logger = getLogger('minoshiro')
    console_handler = StreamHandler()
    console_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s')
    )
    logger.addHandler(console_handler)
    logger.setLevel(INFO)
    return logger

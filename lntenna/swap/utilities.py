import logging
import time
import functools
from secrets import token_hex

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


def create_random_message():
    return str(token_hex(64))


def clock(func):
    @functools.wraps(func)
    def clocked(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - t0
        name = func.__name__
        logger.debug("[%0.8fs] to complete %s()" % (elapsed, name))
        return result

    return clocked

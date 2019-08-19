import functools
import logging
import time
from secrets import token_hex

from lntenna.server.config import FORMAT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


def create_random_message():
    msg = str(token_hex(64))
    logger.debug(f"Created random message: {msg}")
    return msg


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


def try_json(func):
    """Try to return the .json() version of the response
    """
    @functools.wraps(func)
    def _try_json(*args, **kwargs):
        result = func(*args, **kwargs)
        if hasattr(result, "status_code"):
            _result = {"status_code": result.status_code}
        if hasattr(result, "text"):
            try:
                _result["response"] = result.json()
            except Exception:
                _result["response"] = result.text
            return _result
        return result

    return _try_json

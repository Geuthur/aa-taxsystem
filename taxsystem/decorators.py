"""
Decorators
"""

import time
from functools import wraps

from allianceauth.services.hooks import get_extension_logger
from app_utils.esi import EsiDailyDowntime, fetch_esi_status

from taxsystem.app_settings import IS_TESTING

logger = get_extension_logger(__name__)


def when_esi_is_available(func):
    """Make sure the decorated task only runs when esi is available.

    Raise exception when ESI is offline.
    Complete the task without running it when downtime is detected.

    Automatically disabled during tests.
    """

    @wraps(func)
    def outer(*args, **kwargs):
        if IS_TESTING is not True:
            try:
                fetch_esi_status().raise_for_status()
            except EsiDailyDowntime:
                logger.info("Daily Downtime detected. Aborting.")
                return None  # function will not run

        return func(*args, **kwargs)

    return outer


def log_timing(logs):
    """
    A Decirator to log the time a function takes to run.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logs.debug(
                "TIME: %s run for %s seconds with args: %s",
                end_time - start_time,
                func.__name__,
                args,
            )
            return result

        return wrapper

    return decorator

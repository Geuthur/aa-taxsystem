# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.decorators import (
    log_timing,
)
from taxsystem.providers import AppLogger
from taxsystem.tests import NoSocketsTestCase

DECORATOR_PATH = "taxsystem.decorators."


class TestDecorators(NoSocketsTestCase):
    def test_log_timing(self):
        """
        Test should log execution time of decorated function.
        """
        # given
        logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)

        @log_timing(logger)
        def trigger_log_timing():
            return "Log Timing"

        # when
        result = trigger_log_timing()
        # then
        self.assertEqual(result, "Log Timing")

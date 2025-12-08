"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPClientError,
    HTTPServerError,
)

# AA TaxSystem
from taxsystem.providers import retry_task_on_esi_error
from taxsystem.tests import NoSocketsTestCase


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestRetryTaskOnESIError(NoSocketsTestCase):
    """Tests for retry_task_on_esi_error context manager."""

    def setUp(self):
        """
        Set up test case with a mock Celery task.
        """
        super().setUp()
        self.task = MagicMock()
        self.task.request.retries = 1
        self.task.retry = MagicMock(side_effect=Exception("Retry called"))

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_esi_error_limit_exception(self, mock_random):
        """
        Test should retry task when ESI error limit is reached.
        """
        # given
        mock_random.return_value = 3.0  # Fixed jitter for testing
        reset_time = 60.0
        exc = ESIErrorLimitException(reset_time)

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called with correct countdown
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 63)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_esi_bucket_limit_exception(self, mock_random):
        """
        Test should retry task when ESI bucket limit is reached.
        """
        # given
        mock_random.return_value = 4.0  # Fixed jitter for testing
        reset_time = 30.0
        bucket_name = "test_bucket"
        exc = ESIBucketLimitException(bucket=bucket_name, reset=reset_time)

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called with correct countdown
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 34)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_http_502_error(self, mock_random):
        """
        Test should retry task on HTTP 502 Bad Gateway error.
        """
        # given
        mock_random.return_value = 2.5  # Fixed jitter for testing
        exc = HTTPServerError(502, {}, b"Bad Gateway")

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called with 60 second countdown + jitter
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 62)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_http_503_error(self, mock_random):
        """
        Test should retry task on HTTP 503 Service Unavailable error.
        """
        # given
        mock_random.return_value = 3.5  # Fixed jitter for testing
        exc = HTTPServerError(503, {}, b"Service Unavailable")

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 63)

    @patch("skillfarm.providers.random.uniform")
    def test_should_retry_on_http_504_error(self, mock_random):
        """
        Test should retry task on HTTP 504 Gateway Timeout error.
        """
        # given
        mock_random.return_value = 2.0  # Fixed jitter for testing
        exc = HTTPServerError(504, {}, b"Gateway Timeout")

        # when/then
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was called
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 62)

    def test_should_not_retry_on_http_404_error(self):
        """
        Test should not retry task on HTTP 404 error (client error).
        """
        # given
        exc = HTTPClientError(404, {}, b"Not Found")

        # when/then
        with self.assertRaises(HTTPClientError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was NOT called
        self.task.retry.assert_not_called()
        self.assertEqual(context.exception.status_code, 404)

    def test_should_not_retry_on_http_400_error(self):
        """
        Test should not retry task on HTTP 400 error (client error).
        """
        # given
        exc = HTTPClientError(400, {}, b"Bad Request")

        # when/then
        with self.assertRaises(HTTPClientError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was NOT called
        self.task.retry.assert_not_called()
        self.assertEqual(context.exception.status_code, 400)

    @patch("skillfarm.providers.random.uniform")
    def test_should_apply_backoff_jitter_on_retries(self, mock_random):
        """
        Test should apply exponential backoff jitter based on retry count.
        """
        # given
        mock_random.return_value = 4.0
        self.task.request.retries = 2  # Third attempt
        reset_time = 60.0
        exc = ESIErrorLimitException(reset_time)

        # when/then
        with self.assertRaises(Exception):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify countdown uses exponential backoff
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 76)

    def test_should_pass_through_on_success(self):
        """
        Test should pass through when no exception is raised.
        """
        # when
        with retry_task_on_esi_error(self.task):
            result = "success"

        # then
        self.assertEqual(result, "success")
        self.task.retry.assert_not_called()

    def test_should_pass_through_unhandled_exceptions(self):
        """
        Test should pass through exceptions that are not ESI-related.
        """
        # given
        exc = ValueError("Some other error")

        # when/then
        with self.assertRaises(ValueError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Verify retry was NOT called
        self.task.retry.assert_not_called()
        self.assertEqual(str(context.exception), "Some other error")

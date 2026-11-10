"""Helpers for ESI tests with pook."""

# Standard Library
from http import HTTPStatus

# Third Party
from aiopenapi3 import RequestError

# Django
from django.core.cache import cache

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)
from esi.rate_limiting import ESIRateLimitBucket

# AA TaxSystem
from taxsystem.errors import DownTimeError

ESI_BASE_URL = "https://esi.evetech.net"


def divisions_url(owner) -> str:
    """Return the ESI URL of the wallet division names of a corporation owner."""
    return (
        f"{ESI_BASE_URL}/corporations/{owner.eve_corporation.corporation_id}/divisions"
    )


def corp_wallet_bucket_key(token) -> str:
    """Return the cache key of the corp-wallet bucket of a token."""
    return f"esi:bucket:corp-wallet:{token.character_id}"


def clear_esi_limits(token) -> None:
    """Remove the ESI error limit and the corp-wallet bucket of a token from the cache."""
    cache.delete("esi_error_limit_reset")
    cache.delete(corp_wallet_bucket_key(token))


def retryable_errors() -> list[Exception]:
    """Errors on which `retry_task_on_esi_error` retries the task."""
    return [
        ESIErrorLimitException(reset=60),
        ESIBucketLimitException(ESIRateLimitBucket("corp-wallet:1", 300, 900), 60),
        HTTPServerError(HTTPStatus.BAD_GATEWAY, {}, b"Bad Gateway"),
        HTTPServerError(HTTPStatus.SERVICE_UNAVAILABLE, {}, b"Service Unavailable"),
        HTTPServerError(HTTPStatus.GATEWAY_TIMEOUT, {}, b"Gateway Timeout"),
        RequestError(
            operation=None, request=None, data="Request failed", parameters={}
        ),
        DownTimeError("ESI is in daily downtime"),
    ]

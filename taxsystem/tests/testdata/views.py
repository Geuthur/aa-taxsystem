# Standard Library
from unittest.mock import Mock

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.urls import reverse

# AA TaxSystem
from taxsystem.views import add_alliance, add_corp


def _call_unwrapped_view(view, url_name, user, token):
    """Call the view behind its decorators with a prepared request."""
    request = RequestFactory().get(reverse(url_name))
    request.user = user
    request.token = token
    middleware = SessionMiddleware(Mock())
    middleware.process_request(request)
    orig_view = view.__wrapped__.__wrapped__.__wrapped__
    return orig_view(request, token)


def add_corporation(user, token):
    """Call the add_corp view without its decorators."""
    return _call_unwrapped_view(add_corp, "taxsystem:add_corp", user, token)


def add_alliance_view(user, token):
    """Call the add_alliance view without its decorators."""
    return _call_unwrapped_view(add_alliance, "taxsystem:add_alliance", user, token)

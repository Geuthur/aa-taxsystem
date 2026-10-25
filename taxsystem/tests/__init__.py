# Standard Library
import socket
from unittest.mock import Mock

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA TaxSystem
from taxsystem.tests.testdata.factory import EveCorporationInfoFactory, UserMainFactory
from taxsystem.views import add_alliance, add_corp


class SocketAccessError(Exception):
    """Error raised when a test script accesses the network"""


class NoSocketsTestCase(TestCase):
    """Variation of Django's TestCase class that prevents any network use.

    Example:

        .. code-block:: python

            class TestMyStuff(BaseTestCase):
                def test_should_do_what_i_need(self): ...

    """

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


class TaxSystemTestCase(NoSocketsTestCase):
    """
    Preloaded Testcase class for TaxSystem tests without Network access.

    Pre-Load:
        * Alliance Auth Characters, Corporation, Alliance Data

    Available Request Factory:
        `self.factory`

    Available test users:
        * `user` User with standard TaxSystem access.
            * 'taxsystem.basic_access' Permission
        * `superuser` Superuser.
            * Access to whole Application

    Example:
        .. code-block:: python

            class TestMyTaxSystemStuff(TaxSystemTestCase):
                def test_should_do_what_i_need(self):
                    user = self.user
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corp = EveCorporationInfoFactory(
            corporation_id=98_000_000, corporation_name="Test Corporation"
        )

        # Request Factory
        cls.factory = RequestFactory()

        # User with Standard Access
        cls.user = UserMainFactory(main_character__corporation=cls.corp)
        cls.user_character = cls.user.profile.main_character

        # User with Superuser Access
        cls.superuser = UserMainFactory()
        cls.superuser.is_superuser = True
        cls.superuser.save()
        cls.superuser_character = cls.superuser.profile.main_character

    def _add_corporation(self, user, token):
        request = self.factory.get(reverse("taxsystem:add_corp"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_corp.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def _add_alliance(self, user, token):
        request = self.factory.get(reverse("taxsystem:add_alliance"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_alliance.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def _middleware_process_request(self, request: WSGIRequest):
        """Helper method to process middleware for a request."""
        session_middleware = SessionMiddleware(Mock())
        session_middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)

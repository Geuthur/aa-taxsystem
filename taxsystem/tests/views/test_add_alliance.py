"""TestView class for add_alliance."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse
from taxsystem.views import add_alliance

MODULE_PATH = "taxsystem.views"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddAllianceView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.create_access",
            ],
        )
        cls.audit = create_corporation_owner_from_user(cls.user)

    def _add_alliance(self, user, token):
        request = self.factory.get(reverse("taxsystem:add_alliance"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_alliance.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def test_add_alliance(self, mock_tasks, mock_messages):
        # given
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_alliance(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("taxsystem:index"))
        self.assertTrue(mock_tasks.update_alliance.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            AllianceOwner.objects.filter(eve_alliance__alliance_id=3001).exists()
        )

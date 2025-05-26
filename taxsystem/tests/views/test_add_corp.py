"""TestView class."""

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
from taxsystem.models.tax import OwnerAudit
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse
from taxsystem.views import add_corp

MODULE_PATH = "taxsystem.views"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddCorpView(TestCase):
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

    def _add_corporation(self, user, token):
        request = self.factory.get(reverse("taxsystem:add_corp"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_corp.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def test_add_corp(self, mock_tasks, mock_messages):
        # given
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_corporation(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("taxsystem:index"))
        self.assertTrue(mock_tasks.update_corporation.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            OwnerAudit.objects.filter(corporation__corporation_id=2001).exists()
        )

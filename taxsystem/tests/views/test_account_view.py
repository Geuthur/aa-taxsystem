"""TestView class."""

# Standard Library
import json
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem import views
from taxsystem.models.corporation import CorporationPaymentAccount, CorporationPayments
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment,
    create_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestAccountView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            character_id=1001,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_own_corp",
            ],
        )
        cls.audit = create_owneraudit_from_user(cls.user)
        cls.no_audit_user, _ = create_user_from_evecharacter(
            character_id=1002,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_own_corp",
            ],
        )
        cls.no_permission_user, _ = create_user_from_evecharacter(
            character_id=1003,
            permissions=[
                "taxsystem.basic_access",
            ],
        )
        cls.payment_system = create_payment_system(
            name=cls.user.username,
            owner=cls.audit,
            user=cls.user,
        )
        cls.payment_system_inactive = create_payment_system(
            name=cls.no_permission_user.username,
            owner=cls.audit,
            user=cls.no_permission_user,
            status=CorporationPaymentAccount.Status.DEACTIVATED,
        )

    @patch(MODULE_PATH + ".messages")
    def test_should_be_ok(self, mock_messages):
        """Test account view."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:account",
            )
        )

        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.account(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.error.assert_not_called()

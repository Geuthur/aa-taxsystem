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
    create_corporation_owner_from_user,
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
        cls.audit = create_corporation_owner_from_user(cls.user)
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
        cls.no_permission_owner = create_corporation_owner_from_user(
            cls.no_permission_user
        )
        cls.payment_system = create_payment_system(
            name=cls.user.username,
            owner=cls.audit,
            user=cls.user,
        )
        cls.payment_system_inactive = create_payment_system(
            name=cls.no_permission_user.username,
            owner=cls.no_permission_owner,
            user=cls.no_permission_user,
            status=CorporationPaymentAccount.Status.MISSING,
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

    @patch(MODULE_PATH + ".messages")
    def test_account_no_payment_user(self, mock_messages):
        """Test account view when no payment user found."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:account",
            )
        )

        request.user = self.no_audit_user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.account(request, owner_id=2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "No Payment System User found.")

    @patch(MODULE_PATH + ".messages")
    def test_account_with_missing_status(self, mock_messages):
        """Test account view with missing payment status."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:account",
            )
        )

        request.user = self.no_permission_user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.account(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.error.assert_not_called()
        # Check that N/A values are shown for missing status
        self.assertContains(response, "N/A")

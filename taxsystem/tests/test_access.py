"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem import views

# AA Taxsystem
from taxsystem.models.corporation import CorporationPaymentAccount
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.generate_payments import create_payment_system

INDEX_PATH = "taxsystem.views"


class TestViewAccess(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_corporation_owner_from_user(cls.user)
        cls.audit_2 = create_corporation_owner_from_user(cls.superuser)
        cls.manage_audit = create_corporation_owner_from_user(cls.manage_own_user)
        cls.payment_account = create_payment_system(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=500,
        )

    def test_view_index(self):
        """Test view taxsystem index."""
        # given
        request = self.factory.get(reverse("taxsystem:index"))
        request.user = self.user
        # when
        response = views.index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_view_administration(self):
        """Test view administration."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:manage_owner",
                args=[2001],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_own_user
        # when
        response = views.manage_owner(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    def test_view_payments(self):
        """Test view payments."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:payments",
                args=[2001],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.payments(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Payments")

    def test_view_own_payments(self):
        """Test view own payments."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:own_payments",
                args=[2001],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.own_payments(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Own Payments")

    def test_view_faq(self):
        """Test view FAQ."""
        # given
        request = self.factory.get(reverse("taxsystem:faq"))
        request.user = self.user
        # when
        response = views.faq(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "FAQ")
        self.assertContains(response, "FAQ")

    @patch(INDEX_PATH + ".messages")
    def test_view_account(self, mock_messages):
        """Test view account."""
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
        self.assertFalse(mock_messages.error.called)

    def test_view_manage_filters(self):
        """Test view manage filters."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.get(
            reverse(
                "taxsystem:manage_filter",
                args=[2001],
            )
        )
        request.user = self.superuser
        # when
        response = views.manage_filter(request, owner_id=2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Manage Filters")

    @patch(INDEX_PATH + ".messages")
    def test_view_payments_no_owner(self, mock_messages):
        """Test view payments when owner not found."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:payments",
                args=[999999],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.payments(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found")

    @patch(INDEX_PATH + ".messages")
    def test_view_payments_no_permission(self, mock_messages):
        """Test view payments when no permission."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:payments",
                args=[2003],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.payments(request, 2003)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied")

    @patch(INDEX_PATH + ".messages")
    def test_view_own_payments_no_owner(self, mock_messages):
        """Test view own payments when owner not found."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:own_payments",
                args=[999999],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.own_payments(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found")

    @patch(INDEX_PATH + ".messages")
    def test_view_own_payments_no_permission(self, mock_messages):
        """Test view own payments when no permission."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:own_payments",
                args=[2003],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.own_payments(request, 2003)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied")

    @patch(INDEX_PATH + ".messages")
    def test_view_faq_no_owner(self, mock_messages):
        """Test view FAQ when owner not found."""
        # given
        request = self.factory.get(reverse("taxsystem:faq", args=[999999]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.faq(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found")

    @patch(INDEX_PATH + ".messages")
    def test_view_account_no_owner(self, mock_messages):
        """Test view account when owner not found."""
        # given
        request = self.factory.get(reverse("taxsystem:account", args=[999999]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.account(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found")

    @patch(INDEX_PATH + ".messages")
    def test_view_account_no_permission(self, mock_messages):
        """Test view account when no permission."""
        # given
        request = self.factory.get(reverse("taxsystem:account", args=[2003, 1001]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user_2
        # when
        response = views.account(request, 2003, 1001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied")

    @patch(INDEX_PATH + ".messages")
    def test_view_manage_owner_no_owner(self, mock_messages):
        """Test view manage owner when owner not found."""
        # given
        request = self.factory.get(reverse("taxsystem:manage_owner", args=[999999]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_own_user
        # when
        response = views.manage_owner(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found")

    @patch(INDEX_PATH + ".messages")
    def test_view_manage_owner_no_permission(self, mock_messages):
        """Test view manage owner when no permission."""
        # given
        request = self.factory.get(reverse("taxsystem:manage_owner", args=[2003]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_own_user
        # when
        response = views.manage_owner(request, 2003)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Verify the exact error message is "Permission Denied" (not "Owner not Found")
        mock_messages.error.assert_called_with(request, "Permission Denied")

    @patch(INDEX_PATH + ".messages")
    def test_view_manage_filter_no_permission(self, mock_messages):
        """Test view manage filter when no permission."""
        # given
        request = self.factory.get(reverse("taxsystem:manage_filter", args=[2001]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.manage_filter(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called()

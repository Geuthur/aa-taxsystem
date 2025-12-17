"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

# AA TaxSystem
from taxsystem import views

# AA Taxsystem
from taxsystem.models.helpers.textchoices import AccountStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import create_owner_from_user, create_tax_account

INDEX_PATH = "taxsystem.views"


class TestViewAccess(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(cls.user)
        cls.audit_2 = create_owner_from_user(cls.superuser)
        cls.manage_audit = create_owner_from_user(cls.manage_own_user)
        cls.tax_account = create_tax_account(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=AccountStatus.ACTIVE,
            deposit=500,
        )

    def test_should_access_index(self):
        """Test that a user with 'basic_access' can see the index page."""
        # given
        request = self.factory.get(reverse("taxsystem:index"))
        request.user = self.user
        # when
        response = views.index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_should_access_manage_owner(self):
        """Test that a user with 'manage_own_corp' can manage own corporation."""
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
        self.assertContains(response, "Accounts")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_access_manage_owner(self, mock_messages):
        """Test that a user without 'manage_own_corp' cannot access manage owner."""
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
        request.user = self.user
        # when
        response = views.manage_owner(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    def test_should_access_payments(self):
        """Test that a user with 'basic_access' can view payments."""
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

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_payments_when_owner_not_found(self, mock_messages):
        """Test that a user with 'basic_access' is redirected when owner not found."""
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
        mock_messages.error.assert_called_with(request, "Owner not Found.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_payments_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access foreign owner."""
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
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    def test_should_access_my_payments(self):
        """Test that a user with 'basic_access' can view own payments."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:my_payments",
                args=[2001],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.my_payments(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Own Payments")

    def test_should_access_faq(self):
        """Test that a user with 'basic_access' can view FAQ."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:faq",
                args=[2001],
            )
        )
        request.user = self.user
        # when
        response = views.faq(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "FAQ")
        self.assertContains(response, "FAQ")

    @patch(INDEX_PATH + ".messages")
    def test_should_access_account(self, mock_messages):
        """Test that a user with 'basic_access' can view account."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:account",
                args=[2001, 1001],
            )
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.account(request, 2001, 1001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(mock_messages.error.called)

    def test_should_access_manage_filters(self):
        """Test that a user with 'manage_own_corporation' can access manage filters."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:manage_filter",
                args=[2001],
            )
        )
        request.user = self.manage_own_user
        # when
        response = views.manage_filter(request, owner_id=2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Manage Filters")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_my_payments_when_owner_not_found(self, mock_messages):
        """Test that a user with 'basic_access' is redirected when owner not found."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:my_payments",
                args=[999999],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.my_payments(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_my_payments_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access foreign owner."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:my_payments",
                args=[2003],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.my_payments(request, 2003)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_faq_when_owner_not_found(self, mock_messages):
        """Test that a user with 'basic_access' is redirected when owner not found."""
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
        mock_messages.error.assert_called_with(request, "Owner not Found.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_account_when_owner_not_found(self, mock_messages):
        """Test that a user with 'basic_access' is redirected when owner not found."""
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
        mock_messages.error.assert_called_with(request, "Owner not Found.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_account_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access foreign corporation."""
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
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_manage_owner_when_owner_not_found(self, mock_messages):
        """Test that a user with 'basic_access' is redirected when owner not found."""
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
        mock_messages.error.assert_called_with(request, "Owner not Found.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_manage_owner_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access manage_owner."""
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
        # Verify the exact error message is "Permission Denied." (not "Owner not Found")
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_manage_filter_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access manage_filter."""
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

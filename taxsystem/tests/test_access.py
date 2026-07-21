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
from taxsystem.tests.testdata.factory import (
    CorporationOwnerFactory,
    CorporationTaxAccountFactory,
    UserMainFactory,
)

INDEX_PATH = "taxsystem.views"


class TestViewAccess(TaxSystemTestCase):
    """Test View General Access Permissions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.audit_2 = CorporationOwnerFactory(user=cls.superuser)

        cls.manage_own_user = UserMainFactory(
            permissions__=["taxsystem.manage_own_corp"]
        )
        cls.manage_audit = CorporationOwnerFactory(user=cls.manage_own_user)

        cls.tax_account = CorporationTaxAccountFactory(
            name=cls.user_character.character_name,
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
                args=[self.manage_audit.eve_corporation.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_own_user
        # when
        response = views.manage_owner(
            request, self.manage_audit.eve_corporation.corporation_id
        )
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
                args=[self.audit.eve_corporation.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.manage_owner(
            request, self.audit.eve_corporation.corporation_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    def test_should_access_payments(self):
        """Test that a user with 'basic_access' can view payments."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:payments",
                args=[self.user_character.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.payments(request, self.user_character.corporation_id)
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
                args=[self.audit_2.eve_corporation.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.payments(request, self.audit_2.eve_corporation.corporation_id)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    def test_should_access_my_payments(self):
        """Test that a user with 'basic_access' can view own payments."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:my_payments",
                args=[self.user_character.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.my_payments(request, self.user_character.corporation_id)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Own Payments")

    def test_should_access_faq(self):
        """Test that a user with 'basic_access' can view FAQ."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:faq",
                args=[self.user_character.corporation_id],
            )
        )
        request.user = self.user
        # when
        response = views.faq(request, self.user_character.corporation_id)
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
                args=[
                    self.user_character.corporation_id,
                    self.user_character.character_id,
                ],
            )
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.account(
            request,
            self.user_character.corporation_id,
            self.user_character.character_id,
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(mock_messages.error.called)

    def test_should_access_manage_filters(self):
        """Test that a user with 'manage_own_corporation' can access manage filters."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:manage_filter",
                args=[self.manage_audit.eve_corporation.corporation_id],
            )
        )
        request.user = self.manage_own_user
        # when
        response = views.manage_filter(
            request, owner_id=self.manage_audit.eve_corporation.corporation_id
        )
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
                args=[self.user_character.corporation_id],
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
                args=[self.audit_2.eve_corporation.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.my_payments(
            request, self.audit_2.eve_corporation.corporation_id
        )
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
        response = views.account(request, 999999, self.user_character.character_id)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_account_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access foreign corporation."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:account",
                args=[
                    self.user_character.corporation_id,
                    self.user_character.character_id,
                ],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = UserMainFactory()
        # when
        response = views.account(
            request,
            self.user_character.corporation_id,
            self.user_character.character_id,
        )
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
        request = self.factory.get(
            reverse("taxsystem:manage_owner", args=[self.user_character.corporation_id])
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_own_user
        # when
        response = views.manage_owner(request, self.user_character.corporation_id)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Verify the exact error message is "Permission Denied." (not "Owner not Found")
        mock_messages.error.assert_called_with(request, "Permission Denied.")

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_manage_filter_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access manage_filter."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:manage_filter", args=[self.user_character.corporation_id]
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.manage_filter(request, self.user_character.corporation_id)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called()

    def test_should_access_admin_history(self):
        """Test that a user with 'manage_own_corp' can access admin history."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:admin_history",
                args=[self.manage_audit.eve_corporation.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_own_user
        # when
        response = views.admin_history(
            request, owner_id=self.manage_audit.eve_corporation.corporation_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(INDEX_PATH + ".messages")
    def test_should_not_show_admin_history_when_no_permission(self, mock_messages):
        """Test that a user with 'basic_access' can not access admin history."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:admin_history",
                args=[self.user_character.corporation_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.admin_history(request, self.user_character.corporation_id)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Permission Denied.")

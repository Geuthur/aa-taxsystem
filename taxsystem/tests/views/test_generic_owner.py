"""Test generic_manage_owner view."""

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
from taxsystem.tests.testdata.generate_owneraudit import (
    create_alliance_owner_from_user,
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestGenericManageOwner(TestCase):
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
                "taxsystem.manage_own_alliance",
            ],
        )
        cls.no_audit_user, cls.character_ownership = create_user_from_evecharacter(
            character_id=1000,
            permissions=[],
        )
        cls.corp_owner = create_corporation_owner_from_user(cls.user)
        cls.alliance_owner = create_alliance_owner_from_user(cls.user)

    @patch(MODULE_PATH + ".messages")
    def test_generic_manage_owner_corp_no_default(self, mock_messages):
        """Test generic_manage_owner when no default corporation found."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:manage_owner",
                args=[self.alliance_owner.eve_alliance.alliance_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        # Remove main character to trigger "No default Corporation found"
        request.user = self.no_audit_user
        request.user.profile.main_character = None
        # when
        response = views.generic_manage_owner(
            request, owner_id=None, owner_type="corporation"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "No default Corporation found.")

    @patch(MODULE_PATH + ".messages")
    def test_generic_manage_owner_alliance_no_default(self, mock_messages):
        """Test generic_manage_owner when no default alliance found."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:manage_owner",
                args=[self.alliance_owner.eve_alliance.alliance_id],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.no_audit_user
        # when
        response = views.generic_manage_owner(
            request, owner_id=None, owner_type="alliance"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "No default Alliance found.")

    @patch(MODULE_PATH + ".messages")
    def test_generic_manage_owner_no_permission(self, mock_messages):
        """Test generic_manage_owner when no permission."""
        # given
        request = self.factory.get(reverse("taxsystem:manage_owner", args=[2001]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.no_audit_user
        # when
        response = views.generic_manage_owner(
            request, owner_id=2001, owner_type="corporation"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(
            request, "You do not have permission to manage this corporation."
        )

    @patch(MODULE_PATH + ".messages")
    def test_generic_manage_owner_corporation_not_found(self, mock_messages):
        """Test generic_manage_owner when corporation not found."""
        # given
        request = self.factory.get(reverse("taxsystem:manage_owner", args=[999999]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.generic_manage_owner(
            request, owner_id=999999, owner_type="corporation"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Corporation not Found.")


class TestGenericOwnerPayments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            character_id=1001,
            permissions=["taxsystem.basic_access"],
        )
        cls.corp_owner = create_corporation_owner_from_user(cls.user)
        cls.alliance_owner = create_alliance_owner_from_user(cls.user)

    @patch(MODULE_PATH + ".messages")
    def test_generic_owner_payments_no_default_corp(self, mock_messages):
        """Test generic_owner_payments when no default corporation found."""
        # given
        request = self.factory.get(reverse("taxsystem:payments", args=[2001]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        request.user.profile.main_character = None
        # when
        response = views.generic_owner_payments(
            request, owner_id=None, owner_type="corporation"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called()

    @patch(MODULE_PATH + ".messages")
    def test_generic_owner_payments_owner_not_found(self, mock_messages):
        """Test generic_owner_payments when owner not found."""
        # given
        request = self.factory.get(reverse("taxsystem:payments", args=[999999]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.generic_owner_payments(
            request, owner_id=999999, owner_type="corporation"
        )
        # then
        # No redirect, just error message
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestGenericOwnerOwnPayments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            character_id=1001,
            permissions=["taxsystem.basic_access"],
        )
        cls.corp_owner = create_corporation_owner_from_user(cls.user)
        cls.alliance_owner = create_alliance_owner_from_user(cls.user)

    @patch(MODULE_PATH + ".messages")
    def test_generic_owner_own_payments_no_default(self, mock_messages):
        """Test generic_owner_own_payments when no default found."""
        # given
        request = self.factory.get(reverse("taxsystem:own_payments", args=[2001]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        request.user.profile.main_character = None
        # when
        response = views.generic_owner_own_payments(
            request, owner_id=None, owner_type="corporation"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called()

    @patch(MODULE_PATH + ".messages")
    def test_generic_owner_own_payments_owner_not_found(self, mock_messages):
        """Test generic_owner_own_payments when owner not found."""
        # given
        request = self.factory.get(reverse("taxsystem:own_payments", args=[999999]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.user
        # when
        response = views.generic_owner_own_payments(
            request, owner_id=999999, owner_type="corporation"
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called()

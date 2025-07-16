"""TestView class."""

# Standard Library
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

# AA Taxsystem
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
    create_user_from_evecharacter_with_access,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

INDEX_PATH = "taxsystem.views"


@patch(INDEX_PATH + ".messages")
class TestViewAdministrationAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1002
        )
        cls.superuser, cls.character_ownership = (
            create_user_from_evecharacter_with_access(1001)
        )

    def test_admin(self, mock_messages):
        """Test admin access."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()

        request = self.factory.get(reverse("taxsystem:admin"))
        request.user = self.superuser
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    def test_admin_no_access(self, mock_messages):
        """Test admin access."""
        # given
        request = self.factory.get(reverse("taxsystem:admin"))
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.error.called)

    def test_admin_clear_all_etags(self, mock_messages):
        """Test clear all etags."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"), data={"run_clear_etag": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(request, "Queued Clear All ETags")

    def test_force_refresh(self, mock_messages):
        """Test force refresh."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"), data={"force_refresh": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_run_taxsystem_updates(self, mock_messages):
        """Test run char updates."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"), data={"run_taxsystem_updates": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(
            request, "Queued Update All Taxsystem"
        )


class TestViewAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

        cls.superuser, cls.character_ownership = (
            create_user_from_evecharacter_with_access(1002)
        )

        cls.manage_user = create_user_from_evecharacter(
            1003,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_own_corp",
            ],
        )[0]

        cls.audit = create_owneraudit_from_user(cls.user)

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
                "taxsystem:administration",
                args=[2003],
            )
        )
        request.user = self.manage_user
        # when
        response = views.administration(request, 2003)
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
        request.user = self.user
        # when
        response = views.own_payments(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Own Payments")

    def test_view_faq(self):
        """Test view FAQ."""
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

    def test_view_account(self):
        """Test view account."""
        # given
        request = self.factory.get(
            reverse(
                "taxsystem:account",
                args=[2001],
            )
        )
        request.user = self.user
        # when
        response = views.account(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Account")

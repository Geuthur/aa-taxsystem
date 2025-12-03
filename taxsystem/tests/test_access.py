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
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
    create_user_from_evecharacter_with_access,
)
from taxsystem.tests.testdata.generate_payments import create_payment_system
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
        cls.manage_user, cls.character_ownership_manage = create_user_from_evecharacter(
            character_id=1003,
            permissions=["taxsystem.basic_access", "taxsystem.manage_own_corp"],
        )
        cls.audit = create_corporation_owner_from_user(cls.user)
        cls.audit_2 = create_corporation_owner_from_user(cls.superuser)
        cls.audit_3 = create_corporation_owner_from_user(cls.manage_user)

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

    def test_run_corporation_updates_all(self, mock_messages):
        """Test run corporation updates for all corporations."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"),
            data={"run_taxsystem_corporation_updates": True},
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_with(
            request, "Queued Update All Taxsystem Corporations"
        )

    def test_run_corporation_updates_specific(self, mock_messages):
        """Test run corporation updates for a specific corporation."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"),
            data={"run_taxsystem_corporation_updates": True, "corporation_id": "2001"},
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_run_corporation_updates_invalid_id(self, mock_messages):
        """Test run corporation updates with invalid ID."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"),
            data={
                "run_taxsystem_corporation_updates": True,
                "corporation_id": "999999",
            },
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.error.assert_called_with(
            request, "Corporation with ID 999999 not found"
        )

    def test_run_alliance_updates_all(self, mock_messages):
        """Test run alliance updates for all alliances."""
        # given
        # AA TaxSystem
        from taxsystem.tests.testdata.generate_owneraudit import (
            create_alliance_owner_from_user,
        )

        create_alliance_owner_from_user(self.user)
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"),
            data={"run_taxsystem_alliance_updates": True},
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_with(
            request, "Queued Update All Taxsystem Alliances"
        )

    def test_run_alliance_updates_specific(self, mock_messages):
        """Test run alliance updates for a specific alliance."""
        # given
        # AA TaxSystem
        from taxsystem.tests.testdata.generate_owneraudit import (
            create_alliance_owner_from_user,
        )

        alliance_owner = create_alliance_owner_from_user(self.user)
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"),
            data={
                "run_taxsystem_alliance_updates": True,
                "alliance_id": str(alliance_owner.eve_alliance.alliance_id),
            },
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_run_alliance_updates_invalid_id(self, mock_messages):
        """Test run alliance updates with invalid ID."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("taxsystem:admin"),
            data={"run_taxsystem_alliance_updates": True, "alliance_id": "999999"},
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = views.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.error.assert_called_with(
            request, "Alliance with ID 999999 not found"
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
        cls.user_no_permission = create_user_from_evecharacter_with_access(1004)[0]

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

        cls.audit = create_corporation_owner_from_user(cls.user)
        cls.audit_2 = create_corporation_owner_from_user(cls.superuser)
        cls.manage_audit = create_corporation_owner_from_user(cls.manage_user)
        cls.payment_account = create_payment_system(
            name=cls.character_ownership.character.character_name,
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
                args=[2003],
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_user
        # when
        response = views.manage_owner(request, 2003)
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
        request.user = self.user_no_permission
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
        request.user = self.manage_user
        # when
        response = views.manage_owner(request, 999999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(request, "Owner not Found")

    @patch(INDEX_PATH + ".messages")
    def test_view_manage_owner_no_permission(self, mock_messages):
        """Test view manage owner when no permission."""
        # given
        request = self.factory.get(reverse("taxsystem:manage_owner", args=[2001]))
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        MessageMiddleware(Mock()).process_request(request)
        request.user = self.manage_user
        # when
        response = views.manage_owner(request, 2001)
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

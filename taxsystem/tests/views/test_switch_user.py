"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem import views
from taxsystem.models.tax import Payments, PaymentSystem
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


class TestSwitchUser(TestCase):
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
            status=PaymentSystem.Status.DEACTIVATED,
        )

    def test_switch_user_from_active_to_inactive(self):
        """Test switching user for an active user."""
        corporation_id = self.audit.corporation.corporation_id
        payment_system_pk = self.payment_system.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "user": payment_system_pk,
        }

        request = self.factory.post(
            reverse("taxsystem:switch_user", args=[corporation_id, payment_system_pk]),
            data=form_data,
        )

        request.user = self.user

        response = views.switch_user(
            request, corporation_id=corporation_id, payment_system_pk=payment_system_pk
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"Payment System User: {self.payment_system.user.username} deactivated",
        )

    def test_switch_user_from_inactive_to_active(self):
        """Test approving a payment with status rejected."""
        corporation_id = self.audit.corporation.corporation_id
        payment_system_pk = self.payment_system_inactive.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "user": payment_system_pk,
        }

        request = self.factory.post(
            reverse("taxsystem:switch_user", args=[corporation_id, payment_system_pk]),
            data=form_data,
        )

        request.user = self.user

        response = views.switch_user(
            request, corporation_id=corporation_id, payment_system_pk=payment_system_pk
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"Payment System User: {self.payment_system_inactive.user.username} activated",
        )

    def test_no_permission(self):
        """Test try undo a payment without permission."""
        corporation_id = self.audit.corporation.corporation_id
        payment_system_pk = self.payment_system.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "user": payment_system_pk,
        }

        request = self.factory.post(
            reverse("taxsystem:switch_user", args=[corporation_id, payment_system_pk]),
            data=form_data,
        )

        request.user = self.no_audit_user

        response = views.switch_user(
            request, corporation_id=corporation_id, payment_system_pk=payment_system_pk
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test undo payment without managing permission."""
        corporation_id = self.audit.corporation.corporation_id
        payment_system_pk = self.payment_system.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "user": payment_system_pk,
        }

        request = self.factory.post(
            reverse("taxsystem:switch_user", args=[corporation_id, payment_system_pk]),
            data=form_data,
        )

        request.user = self.no_permission_user

        response = views.switch_user(
            request, corporation_id=corporation_id, payment_system_pk=payment_system_pk
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

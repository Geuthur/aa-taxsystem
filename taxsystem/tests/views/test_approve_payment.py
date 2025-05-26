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


class TestApprovePayment(TestCase):
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
        cls.payment = create_payment(
            name=cls.payment_system.name,
            entry_id=1,
            account=cls.payment_system,
            amount=1000,
        )

    def test_approve_payment(self):
        """Test approving a payment."""
        corporation_id = self.audit.corporation.corporation_id
        payment_id = self.payment.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("taxsystem:approve_payment", args=[corporation_id, payment_id]),
            data=form_data,
        )

        request.user = self.user

        response = views.approve_payment(
            request, corporation_id=corporation_id, payment_pk=payment_id
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"Payment ID: {self.payment.pk} - Amount: 1,000 - Name: Gneuten approved",
        )

    def test_no_permission(self):
        """Test try approve a payment without permission."""
        corporation_id = self.audit.corporation.corporation_id
        payment_id = self.payment.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("taxsystem:approve_payment", args=[corporation_id, payment_id]),
            data=form_data,
        )

        request.user = self.no_audit_user

        response = views.approve_payment(
            request, corporation_id=corporation_id, payment_pk=payment_id
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test approve payment without managing permission."""
        corporation_id = self.audit.corporation.corporation_id
        payment_id = self.payment.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("taxsystem:approve_payment", args=[corporation_id, payment_id]),
            data=form_data,
        )

        request.user = self.no_permission_user

        response = views.approve_payment(
            request, corporation_id=corporation_id, payment_pk=payment_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

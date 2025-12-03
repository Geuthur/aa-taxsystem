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
from taxsystem.models.corporation import CorporationPayments
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


class TestDeletePayment(TestCase):
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
        cls.payment_system = create_payment_system(
            name=cls.user.username,
            owner=cls.audit,
            user=cls.user,
        )
        cls.payment = create_payment(
            name=cls.payment_system.name,
            entry_id=None,
            account=cls.payment_system,
            amount=1000,
        )
        cls.payment_esi = create_payment(
            name=cls.payment_system.name,
            entry_id=1,
            account=cls.payment_system,
            amount=2000,
        )

    def test_delete_payment(self):
        """Test deleting a payment."""
        # given
        corporation_id = self.audit.eve_corporation.corporation_id
        form_data = {
            "corporation_id": corporation_id,
            "delete_reason": "This is a test deletion",
        }
        request = self.factory.post(
            reverse("taxsystem:delete_payment", args=[corporation_id, self.payment.pk]),
            data=form_data,
        )
        request.user = self.user
        # when
        response = views.delete_payment(
            request, owner_id=corporation_id, payment_pk=self.payment.pk
        )
        response_data = json.loads(response.content)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"Payment ID: {self.payment.pk} - Amount: 1,000 - Name: Gneuten deleted - This is a test deletion",
        )

    def test_delete_payment_esi(self):
        """Test deleting esi a payment."""
        # given
        corporation_id = self.audit.eve_corporation.corporation_id
        form_data = {
            "corporation_id": corporation_id,
            "delete_reason": "This is a test deletion",
        }
        request = self.factory.post(
            reverse(
                "taxsystem:delete_payment", args=[corporation_id, self.payment_esi.pk]
            ),
            data=form_data,
        )
        request.user = self.user
        # when
        response = views.delete_payment(
            request, owner_id=corporation_id, payment_pk=self.payment_esi.pk
        )
        response_data = json.loads(response.content)
        # then
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"Payment ID: {self.payment_esi.pk} - Amount: 2,000 - Name: Gneuten deletion failed - ESI imported payments cannot be deleted",
        )

    def test_no_permission(self):
        """Test try deleting a payment without permission."""
        # given
        corporation_id = self.audit.eve_corporation.corporation_id
        form_data = {
            "corporation_id": corporation_id,
            "delete_reason": "This is a test deletion",
        }
        request = self.factory.post(
            reverse("taxsystem:delete_payment", args=[corporation_id, self.payment.pk]),
            data=form_data,
        )
        request.user = self.no_audit_user
        # when
        response = views.delete_payment(
            request, owner_id=corporation_id, payment_pk=self.payment.pk
        )
        response_data = json.loads(response.content)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test reject payment without managing permission."""
        # given
        corporation_id = self.audit.eve_corporation.corporation_id
        form_data = {
            "corporation_id": corporation_id,
            "delete_reason": "This is a test deletion",
        }
        # when
        request = self.factory.post(
            reverse("taxsystem:delete_payment", args=[corporation_id, self.payment.pk]),
            data=form_data,
        )
        request.user = self.no_permission_user
        # then
        response = views.delete_payment(
            request, owner_id=corporation_id, payment_pk=self.payment.pk
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

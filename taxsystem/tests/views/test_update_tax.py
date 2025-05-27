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
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestUpdateTaxPeriod(TestCase):
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

    def test_update_tax_period(self):
        """Test update tax period."""
        corporation_id = self.audit.corporation.corporation_id

        form_data = {
            "corporation_id": corporation_id,
            "value": 30,
        }

        request = self.factory.post(
            reverse("taxsystem:update_tax_period", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user

        response = views.update_tax_period(request, corporation_id=corporation_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response_data["message"],
            f"Tax Period from {self.audit.corporation.corporation_name} updated to 30",
        )

    def test_no_permission(self):
        """Test update tax period without permission."""
        corporation_id = self.audit.corporation.corporation_id

        form_data = {
            "corporation_id": corporation_id,
            "value": 30,
        }

        request = self.factory.post(
            reverse("taxsystem:update_tax_period", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.no_audit_user

        response = views.update_tax_period(request, corporation_id=corporation_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test update tax period without managing permission."""
        corporation_id = self.audit.corporation.corporation_id

        form_data = {
            "corporation_id": corporation_id,
            "value": 30,
        }

        request = self.factory.post(
            reverse("taxsystem:update_tax_period", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.no_permission_user

        response = views.update_tax_period(request, corporation_id=corporation_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class TestUpdateTaxAmount(TestCase):
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

    def test_update_tax_amount(self):
        """Test update tax amount."""
        corporation_id = self.audit.corporation.corporation_id

        form_data = {
            "corporation_id": corporation_id,
            "value": 100000000,
        }

        request = self.factory.post(
            reverse("taxsystem:update_tax_amount", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user

        response = views.update_tax_amount(request, corporation_id=corporation_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response_data["message"],
            f"Tax Amount from {self.audit.corporation.corporation_name} updated to 100000000.0",
        )

    def test_no_permission(self):
        """Test update tax amount without permission."""
        corporation_id = self.audit.corporation.corporation_id

        form_data = {
            "corporation_id": corporation_id,
            "value": 100000000,
        }

        request = self.factory.post(
            reverse("taxsystem:update_tax_amount", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.no_audit_user

        response = views.update_tax_amount(request, corporation_id=corporation_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test update tax amount without managing permission."""
        corporation_id = self.audit.corporation.corporation_id

        form_data = {
            "corporation_id": corporation_id,
            "value": 100000000,
        }

        request = self.factory.post(
            reverse("taxsystem:update_tax_amount", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.no_permission_user

        response = views.update_tax_amount(request, corporation_id=corporation_id)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

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
from taxsystem.models.corporation import CorporationFilter
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestDeleteFilter(TestCase):
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

        cls.filter_set = create_filterset(
            owner=cls.audit,
            name="100m",
            description="Filter for payments over 100m",
        )

        cls.filter_amount = create_filter(
            filter_set=cls.filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000,
        )

    def test_delete_filter(self):
        """Test delete filter."""
        corporation_id = self.audit.eve_corporation.corporation_id
        filter_id = self.filter_amount.id

        form_data = {
            "confirm": "yes",
            "delete_reason": "Test reason",
        }

        request = self.factory.post(
            reverse("taxsystem:delete_filter", args=[corporation_id, filter_id]),
            data=form_data,
        )
        request.user = self.user

        response = views.delete_filter(
            request, owner_id=corporation_id, filter_pk=filter_id
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"{self.filter_amount.filter_type}({self.filter_amount.value}) from {self.filter_amount.filter_set} deleted - {form_data['delete_reason']}",
        )

    def test_no_permission(self):
        """Test try undo a payment without permission."""
        corporation_id = self.audit.eve_corporation.corporation_id
        filter_id = self.filter_amount.id

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "delete_reason": "Test reason",
        }

        request = self.factory.post(
            reverse("taxsystem:delete_filter", args=[corporation_id, filter_id]),
            data=form_data,
        )

        request.user = self.no_audit_user

        response = views.delete_filter(
            request, owner_id=corporation_id, filter_pk=filter_id
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test undo payment without managing permission."""
        corporation_id = self.audit.eve_corporation.corporation_id
        filter_id = self.filter_amount.id

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "delete_reason": "Test reason",
        }

        request = self.factory.post(
            reverse("taxsystem:delete_filter", args=[corporation_id, filter_id]),
            data=form_data,
        )

        request.user = self.no_permission_user

        response = views.delete_filter(
            request, owner_id=corporation_id, filter_pk=filter_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

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
from taxsystem.models.tax import Members
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.generate_payments import create_member
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestDeleteMember(TestCase):
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
        cls.member = create_member(
            character_name="Gneuten",
            character_id=1001,
            owner=cls.audit,
            status=Members.States.MISSING,
        )

    def test_delete_member(self):
        """Test delete member."""
        corporation_id = self.audit.corporation.corporation_id
        member_pk = self.member.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "delete_reason": "Test reason",
        }

        request = self.factory.post(
            reverse("taxsystem:delete_member", args=[corporation_id, member_pk]),
            data=form_data,
        )

        request.user = self.user

        response = views.delete_member(
            request, corporation_id=corporation_id, member_pk=member_pk
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"Member {self.member.character_name} deleted - Test reason",
        )

    def test_no_permission(self):
        """Test try undo a payment without permission."""
        corporation_id = self.audit.corporation.corporation_id
        member_pk = self.member.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "delete_reason": "Test reason",
        }

        request = self.factory.post(
            reverse("taxsystem:delete_member", args=[corporation_id, member_pk]),
            data=form_data,
        )

        request.user = self.no_audit_user

        response = views.delete_member(
            request, corporation_id=corporation_id, member_pk=member_pk
        )

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_no_manage_permission(self):
        """Test undo payment without managing permission."""
        corporation_id = self.audit.corporation.corporation_id
        member_pk = self.member.pk

        form_data = {
            "corporation_id": corporation_id,
            "confirm": "yes",
            "delete_reason": "Test reason",
        }

        request = self.factory.post(
            reverse("taxsystem:delete_member", args=[corporation_id, member_pk]),
            data=form_data,
        )

        request.user = self.no_permission_user

        response = views.delete_member(
            request, corporation_id=corporation_id, member_pk=member_pk
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

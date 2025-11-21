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
from taxsystem.models.corporation import CorporationFilter
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestDeleteSetFilter(TestCase):
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

    def _message_middleware(self, request):
        """Middleware to add a message to the response."""
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

    @patch(MODULE_PATH + ".messages")
    def test_delete_filterset(self, mock_messages):
        """Test delete filter."""
        corporation_id = self.audit.eve_corporation.corporation_id
        filterset_id = self.filter_set.id

        request = self.factory.get(
            reverse("taxsystem:delete_filterset", args=[corporation_id, filterset_id]),
        )
        request.user = self.user

        self._message_middleware(request)

        response = views.delete_filterset(
            request, owner_id=corporation_id, filter_set_id=filterset_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.success.assert_called_once_with(
            request, "Filter set deleted successfully."
        )

    @patch(MODULE_PATH + ".messages")
    def test_no_permission(self, mock_messages):
        """Test try delete without permission."""
        corporation_id = self.audit.eve_corporation.corporation_id
        filterset_id = self.filter_set.id

        request = self.factory.get(
            reverse("taxsystem:delete_filterset", args=[corporation_id, filterset_id]),
        )

        request.user = self.no_audit_user

        self._message_middleware(request)

        response = views.delete_filterset(
            request, owner_id=corporation_id, filter_set_id=filterset_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(
            request, "You do not have permission to manage this owner."
        )

    def test_no_manage_permission(self):
        """Test delete without managing permission."""
        corporation_id = self.audit.eve_corporation.corporation_id
        filterset_id = self.filter_set.id

        request = self.factory.get(
            reverse("taxsystem:delete_filterset", args=[corporation_id, filterset_id]),
        )

        request.user = self.no_permission_user

        response = views.delete_filterset(
            request, owner_id=corporation_id, filter_set_id=filterset_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

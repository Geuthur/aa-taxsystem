"""Test manage_filter view."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem import forms, views
from taxsystem.tests.testdata.generate_filter import create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.views"


class TestManageFilter(TestCase):
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
        cls.no_permission_user, cls.character_ownership_no_permission = (
            create_user_from_evecharacter(
                character_id=1002,
                permissions=[],
            )
        )
        cls.audit = create_corporation_owner_from_user(cls.user)
        cls.filter_set = create_filterset(
            cls.audit, name="Test Filter Set", description="Test"
        )

    @patch(MODULE_PATH + ".messages")
    def test_manage_filter_add_filter_valid(self, mock_messages):
        """Test manage filter with valid filter form."""
        # given
        request = self.factory.post(
            reverse("taxsystem:manage_filter", args=[2001]),
            data={
                "filter_set": self.filter_set.id,
                "filter_type": "amount",
                "value": "1000",
            },
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.manage_filter(request, owner_id=2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(MODULE_PATH + ".messages")
    @patch("taxsystem.models.CorporationFilter.objects.create")
    def test_manage_filter_add_filter_integrity_error(self, mock_create, mock_messages):
        """Test manage filter with IntegrityError."""
        # given
        mock_create.side_effect = IntegrityError
        request = self.factory.post(
            reverse("taxsystem:manage_filter", args=[2001]),
            data={
                "filter_set": self.filter_set.id,
                "filter_type": "amount",
                "value": "1000",
            },
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.manage_filter(request, owner_id=2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_with(
            request, "A filter with this name already exists."
        )

    @patch(MODULE_PATH + ".messages")
    def test_manage_filter_add_filter_exception(self, mock_messages):
        """Test manage filter with general exception."""
        # given
        request = self.factory.post(
            reverse("taxsystem:manage_filter", args=[2001]),
            data={
                "filter_set": self.filter_set.id,
                "filter_type": "amount",
                "value": "1000",
            },
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # Mock the create to raise generic Exception
        with patch.object(
            self.audit.filter_class.objects,
            "create",
            side_effect=Exception("Test error"),
        ):
            # when
            response = views.manage_filter(request, owner_id=2001)
            # then
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
            mock_messages.error.assert_called_with(
                request, "Something went wrong, please try again later."
            )

    @patch(MODULE_PATH + ".messages")
    def test_manage_filter_add_filter_set_valid(self, mock_messages):
        """Test manage filter with valid filter set form."""
        # given
        request = self.factory.post(
            reverse("taxsystem:manage_filter", args=[2001]),
            data={
                "name": "New Filter Set",
                "description": "Test Description",
            },
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # when
        response = views.manage_filter(request, owner_id=2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(MODULE_PATH + ".messages")
    def test_manage_filter_add_filter_set_integrity_error(self, mock_messages):
        """Test manage filter with IntegrityError on filter set."""
        # given
        request = self.factory.post(
            reverse("taxsystem:manage_filter", args=[2001]),
            data={
                "name": "New Filter Set",
                "description": "Test Description",
            },
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # Mock the create to raise IntegrityError
        with patch.object(
            self.audit.filterset_class.objects, "create", side_effect=IntegrityError
        ):
            # when
            response = views.manage_filter(request, owner_id=2001)
            # then
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
            mock_messages.error.assert_called_with(
                request, "A filter set with this name already exists."
            )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".logger")
    def test_manage_filter_add_filter_set_exception(self, mock_logger, mock_messages):
        """Test manage filter with general exception on filter set."""
        # given
        request = self.factory.post(
            reverse("taxsystem:manage_filter", args=[2001]),
            data={
                "name": "New Filter Set",
                "description": "Test Description",
            },
        )
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        # Mock the create to raise generic Exception
        with patch.object(
            self.audit.filterset_class.objects,
            "create",
            side_effect=Exception("Test error"),
        ):
            # when
            response = views.manage_filter(request, owner_id=2001)
            # then
            self.assertEqual(response.status_code, HTTPStatus.OK)
            mock_messages.error.assert_called_with(
                request, "Something went wrong, please try again later."
            )
            # Check that logger.error was called with the right format string
            self.assertTrue(mock_logger.error.called)
            call_args = mock_logger.error.call_args
            self.assertEqual(call_args[0][0], "Error creating journal filter set: %s")
            self.assertIsInstance(call_args[0][1], Exception)

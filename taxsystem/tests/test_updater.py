"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock

# Third Party
import pydantic

# Django
from django.test import override_settings

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA TaxSystem
from taxsystem.models.corporation import CorporationUpdateStatus
from taxsystem.models.general import UpdateSectionResult, _NeedsUpdate
from taxsystem.models.helpers.textchoices import (
    CorporationUpdateSection,
)
from taxsystem.models.helpers.updater import UpdateManager
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import create_owner_from_user, create_update_status


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestUpdateManager(TaxSystemTestCase):
    """
    Tests for the UpdateManager class.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.updater = UpdateManager

    def test_init(self):
        """
        Test the initialization of the UpdateManager.
        """
        # Test Data
        mock_owner = MagicMock()
        mock_update_section = MagicMock()
        mock_update_status = MagicMock()

        # Test Action
        manager = self.updater(
            owner=mock_owner,
            update_section=mock_update_section,
            update_status=mock_update_status,
        )

        # Expected Results
        self.assertEqual(manager.owner, mock_owner)
        self.assertEqual(manager.update_section, mock_update_section)
        self.assertEqual(manager.update_status, mock_update_status)

    def test_calc_update_needed(self):
        """
        Test the calc_update_needed method.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        # Test Action
        needs_update = manager.calc_update_needed()

        # Expected Results
        self.assertIsInstance(needs_update, _NeedsUpdate)
        self.assertIsInstance(needs_update.section_map, dict)
        for section, needs in needs_update.section_map.items():
            self.assertIsInstance(section, str)
            self.assertIsInstance(needs, bool)

    def test_reset_update_status(self):
        """
        Test the reset_update_status method.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        section_to_reset = CorporationUpdateSection.WALLET

        # Test Action
        manager.reset_update_status(section_to_reset)

        status_obj = CorporationUpdateStatus.objects.get(
            owner=self.audit,
            section=section_to_reset,
        )

        # Expected Results
        self.assertTrue(status_obj.need_update())

    def test_reset_has_token_error(self):
        """
        Test the reset_has_token_error method.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        create_update_status(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
            has_token_error=True,
        )

        # Test Action
        manager.reset_has_token_error()
        updated_status_obj = CorporationUpdateStatus.objects.get(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        # Expected Results
        self.assertFalse(updated_status_obj.has_token_error)

    def test_update_section_if_changed_success(self):
        """
        Test the update_section_if_changed method for a successful update.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        def mock_fetch_func(owner=None, force_refresh=False):
            return {"key": "value"}

        # Test Action
        result = manager.update_section_if_changed(
            section=CorporationUpdateSection.WALLET,
            fetch_func=mock_fetch_func,
            force_refresh=False,
        )

        # Expected Results
        self.assertIsInstance(result, UpdateSectionResult)
        self.assertTrue(result.is_changed)
        self.assertTrue(result.is_updated)
        self.assertEqual(result.data, {"key": "value"})

    def test_update_section_if_changed_token_error(self):
        """
        Test the update_section_if_changed method for a token error scenario.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        class MockHTTPClientError(HTTPClientError):
            status_code = 403

        def mock_fetch_func(owner=None, force_refresh=False):
            raise MockHTTPClientError(status_code=403, headers={}, data=None)

        # Test Action
        result = manager.update_section_if_changed(
            section=CorporationUpdateSection.WALLET,
            fetch_func=mock_fetch_func,
            force_refresh=False,
        )

        # Expected Results
        self.assertIsInstance(result, UpdateSectionResult)
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertTrue(result.has_token_error)
        self.assertIsNotNone(result.error_message)

    def test_update_section_if_changed_no_change(self):
        """
        Test the update_section_if_changed method for no change scenario.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        def mock_fetch_func(owner=None, force_refresh=False):
            raise HTTPNotModified(status_code=304, headers={})

        # Test Action
        result = manager.update_section_if_changed(
            section=CorporationUpdateSection.WALLET,
            fetch_func=mock_fetch_func,
            force_refresh=False,
        )

        # Expected Results
        self.assertIsInstance(result, UpdateSectionResult)
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)

    def test_update_section_log_is_updated(self):
        """
        Test the update_section_log method for an updated section.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
        )

        # Test Action
        manager.update_section_log(
            section=CorporationUpdateSection.WALLET,
            result=result,
        )

        status_obj = CorporationUpdateStatus.objects.get(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        # Expected Results
        self.assertTrue(status_obj.is_success)
        self.assertFalse(status_obj.has_token_error)
        self.assertEqual(status_obj.error_message, "")

    def test_update_section_log_token_error(self):
        """
        Test the update_section_log method for a section with token error.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        result = UpdateSectionResult(
            is_changed=False,
            is_updated=False,
            has_token_error=True,
            error_message="Token error occurred.",
        )

        # Test Action
        manager.update_section_log(
            section=CorporationUpdateSection.WALLET,
            result=result,
        )

        status_obj = CorporationUpdateStatus.objects.get(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        # Expected Results
        self.assertFalse(status_obj.is_success)
        self.assertTrue(status_obj.has_token_error)
        self.assertEqual(status_obj.error_message, "Token error occurred.")

    def test_perform_update_status(self):
        """
        Test the perform_update_status method.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        create_update_status(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        def mock_update_method(owner, force_refresh=False):
            return UpdateSectionResult(
                is_changed=True,
                is_updated=True,
                has_token_error=False,
            )

        # Test Action
        result = manager.perform_update_status(
            section=CorporationUpdateSection.WALLET,
            method=mock_update_method,
            owner=self.audit,
            force_refresh=False,
        )

        # Expected Results (perform_update_status returns the result; persistence
        # is handled by update_section_log and is tested separately)
        self.assertIsInstance(result, UpdateSectionResult)
        self.assertTrue(result.is_changed)
        self.assertTrue(result.is_updated)

    def test_perform_update_status_token_error(self):
        """
        Test the perform_update_status method for token error scenario.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        status_obj = create_update_status(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        def mock_update_method(owner, force_refresh=False):
            raise ValueError("Token error occurred.")

        # Test Action: perform_update_status should persist an error and re-raise
        with self.assertRaises(ValueError):
            manager.perform_update_status(
                section=CorporationUpdateSection.WALLET,
                method=mock_update_method,
                owner=self.audit,
                force_refresh=False,
            )

        # Expected Results: status object updated due to the exception
        status_obj = CorporationUpdateStatus.objects.get(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )
        self.assertFalse(status_obj.is_success)
        self.assertFalse(status_obj.has_token_error)
        self.assertIn("ValueError: Token error occurred.", status_obj.error_message)

    def test_perform_update_Status_httpserver_error(self):
        """
        Test the perform_update_status method for HTTPServerError scenario.
        """
        # Test Data
        self.audit = create_owner_from_user(self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        status_obj = create_update_status(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        def mock_update_method(owner, force_refresh=False):
            raise HTTPServerError(status_code=500, headers={}, data=None)

        # Test Action: perform_update_status should persist an error and re-raise
        with self.assertRaises(HTTPServerError):
            manager.perform_update_status(
                section=CorporationUpdateSection.WALLET,
                method=mock_update_method,
                owner=self.audit,
                force_refresh=False,
            )

        # Expected Results: status object updated due to the exception
        status_obj = CorporationUpdateStatus.objects.get(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )
        self.assertFalse(status_obj.is_success)
        self.assertFalse(status_obj.has_token_error)

"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock

# Third Party
import pydantic

# Django
from django.test import override_settings

# Alliance Auth
from esi.errors import TokenError
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA TaxSystem
from taxsystem.models.corporation import CorporationUpdateStatus
from taxsystem.models.general import UpdateSectionResult, _NeedsUpdate
from taxsystem.models.helpers.update_manager import (
    AllianceUpdateSection,
    CorporationUpdateSection,
    UpdateManager,
    UpdateSection,
    UpdateStatus,
)
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationOwnerFactory,
    CorporationUpdateStatusFactory,
)


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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        CorporationUpdateStatusFactory(
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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
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
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        CorporationUpdateStatusFactory(
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
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        CorporationUpdateStatusFactory(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
        )

        def mock_update_method(owner, force_refresh=False):
            raise TokenError("Token error occurred.")

        # Test Action
        result = manager.perform_update_status(
            section=CorporationUpdateSection.WALLET,
            method=mock_update_method,
            owner=self.audit,
            force_refresh=False,
        )

        # Expected Results
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertTrue(result.has_token_error)
        self.assertIn("TokenError: Token error occurred.", result.error_message)

    def test_perform_update_Status_httpserver_error(self):
        """
        Test the perform_update_status method for HTTPServerError scenario.
        """
        # Test Data
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        CorporationUpdateStatusFactory(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
            has_token_error=False,
            is_success=False,
        )

        def mock_update_method(owner, force_refresh=False):
            raise HTTPServerError(status_code=500, headers={}, data=None)

        # Test Action
        result = manager.perform_update_status(
            section=CorporationUpdateSection.WALLET,
            method=mock_update_method,
            owner=self.audit,
            force_refresh=False,
        )

        # Expected Results
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertFalse(result.has_token_error)
        self.assertIn("500", result.error_message)

    def test_get_sections_to_update_when_force_refresh_should_return_all(self):
        """Test that get_sections_to_update returns all sections on force refresh."""
        # Test Data
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        CorporationUpdateStatusFactory(
            owner=self.audit,
            section=CorporationUpdateSection.WALLET,
            has_token_error=True,
        )

        # Test Action
        sections = manager.get_sections_to_update(force_refresh=True)

        # Expected Result
        self.assertEqual(sections, list(CorporationUpdateSection.get_sections()))
        status = CorporationUpdateStatus.objects.get(
            owner=self.audit, section=CorporationUpdateSection.WALLET
        )
        self.assertFalse(status.has_token_error)

    def test_get_sections_to_update_when_needed_should_return_stale_sections(self):
        """Test that get_sections_to_update returns sections needing update."""
        # Test Data
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

        # Test Action
        sections = manager.get_sections_to_update(force_refresh=False)

        # Expected Result
        self.assertEqual(len(sections), len(CorporationUpdateSection.get_sections()))

    def test_execute_section_should_call_owner_method_and_log_success(self):
        """Test that execute_section successfully runs owner method and records log."""
        # Test Data
        self.audit = CorporationOwnerFactory(user=self.user)
        manager = self.updater(
            owner=self.audit,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )
        expected_result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
            error_message="",
            data={"test": "data"},
        )
        self.audit.update_wallet = MagicMock(return_value=expected_result)

        # Test Action
        result = manager.execute_section(
            CorporationUpdateSection.WALLET, force_refresh=True
        )

        # Expected Result
        self.assertEqual(result, expected_result)
        self.audit.update_wallet.assert_called_once()
        status = CorporationUpdateStatus.objects.get(
            owner=self.audit, section=CorporationUpdateSection.WALLET
        )
        self.assertTrue(status.is_success)
        self.assertFalse(status.has_token_error)


class TestUpdateStatusAndSections(TaxSystemTestCase):
    """Tests for UpdateSection, CorporationUpdateSection, AllianceUpdateSection, and UpdateStatus."""

    def test_update_section_should_return_sections_and_method_names(self):
        # Test Data
        corp_sections = CorporationUpdateSection
        alliance_sections = AllianceUpdateSection

        # Test Action
        corp_list = corp_sections.get_sections()
        alliance_list = alliance_sections.get_sections()

        # Expected Result
        self.assertIn("wallet", corp_list)
        self.assertIn("divisions", corp_list)
        self.assertIn("members", corp_list)
        self.assertEqual(corp_sections.WALLET.method_name, "update_wallet")
        self.assertEqual(corp_sections.DIVISIONS.method_name, "update_divisions")

        self.assertIn("tax_accounts", alliance_list)
        self.assertIn("payments", alliance_list)
        self.assertIn("deadlines", alliance_list)
        self.assertEqual(alliance_sections.PAYMENTS.method_name, "update_payments")

    def test_update_status_bootstrap_icon_should_render_html_span(self):
        # Test Data
        statuses = [
            (UpdateStatus.DISABLED, "text-muted", "Update is disabled"),
            (
                UpdateStatus.TOKEN_ERROR,
                "text-warning",
                "One section has a token error during update",
            ),
            (UpdateStatus.ERROR, "text-danger", "An error occurred during update"),
            (UpdateStatus.OK, "text-success", "Updates completed successfully"),
            (
                UpdateStatus.INCOMPLETE,
                "text-warning",
                "One or more sections have not been updated",
            ),
            (UpdateStatus.IN_PROGRESS, "text-info", "Update is in progress"),
        ]

        # Test Action & Expected Result
        for status, expected_class, expected_desc in statuses:
            # Test Action
            icon_html = status.bootstrap_icon()

            # Expected Result
            self.assertIn(f"class='{expected_class}'", icon_html)
            self.assertIn(f"title='{expected_desc}'", icon_html)
            self.assertIn("data-bs-tooltip='aa-taxsystem'", icon_html)
            self.assertIn("⬤", icon_html)

    def test_update_status_bootstrap_text_style_class_should_return_correct_class(self):
        # Test Data
        expected_styles = {
            UpdateStatus.DISABLED: "text-muted",
            UpdateStatus.TOKEN_ERROR: "text-warning",
            UpdateStatus.INCOMPLETE: "text-warning",
            UpdateStatus.IN_PROGRESS: "text-info",
            UpdateStatus.ERROR: "text-danger",
            UpdateStatus.OK: "text-success",
        }

        # Test Action & Expected Result
        for status, expected_style in expected_styles.items():
            # Test Action
            style = status.bootstrap_text_style_class()

            # Expected Result
            self.assertEqual(style, expected_style)

    def test_update_status_description_should_return_human_readable_string(self):
        # Test Data
        statuses = [
            UpdateStatus.DISABLED,
            UpdateStatus.TOKEN_ERROR,
            UpdateStatus.ERROR,
            UpdateStatus.OK,
            UpdateStatus.INCOMPLETE,
            UpdateStatus.IN_PROGRESS,
        ]

        # Test Action & Expected Result
        for status in statuses:
            # Test Action
            desc = status.description()

            # Expected Result
            self.assertIsInstance(desc, str)
            self.assertTrue(len(desc) > 0)

"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.alliance import AllianceUpdateStatus
from taxsystem.models.corporation import CorporationUpdateStatus
from taxsystem.models.general import UpdateSectionResult
from taxsystem.tasks import (
    _update_ally_section,
    _update_corp_section,
    update_all_taxsytem,
    update_alliance,
    update_corporation,
)
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import create_owner_from_user, create_update_status

TASKS_PATH = "taxsystem.tasks"
MANAGERS_PATH = "taxsystem.managers"
MODELS_PATH = "taxsystem.models"


class TestTasks(TaxSystemTestCase):
    """
    Tests for taxsystem tasks.
    """

    @patch(TASKS_PATH + ".update_corporation", spec=True)
    @patch(TASKS_PATH + ".update_alliance", spec=True)
    def test_update_all_taxsystem(
        self,
        mock_update_alliance: MagicMock,
        mock_update_corporation: MagicMock,
    ):
        """
        Test 'update_all_taxsytem' task.

        # Test Scenarios:
            1. Task queues update tasks for all active corporation and alliance owners.
        """
        # Test Data
        create_owner_from_user(user=self.user)
        create_owner_from_user(user=self.user, tax_type="alliance")

        # Test Action
        update_all_taxsytem(force_refresh=False)

        # Expected Result
        self.assertTrue(mock_update_corporation.apply_async.called)
        self.assertTrue(mock_update_alliance.apply_async.called)

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    @patch(TASKS_PATH + ".logger")
    @patch(TASKS_PATH + ".update_corp_wallet")
    @patch(TASKS_PATH + ".CorporationUpdateSection.get_sections", lambda: ["wallet"])
    def test_update_corporation(
        self, mock_update_corp_wallet: MagicMock, mock_logger: MagicMock
    ):
        """
        Test 'update_corporation' task.

        # Test Scenarios:
            1. Task updates corporation owner data (only wallet).
            2. Task no need update when data is fresh.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user)

        # Test Action
        update_corporation(owner_pk=owner.pk, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.name
        )

        # Setup for Scenario 2: No update needed
        mock_update_corp_wallet.reset_mock()
        create_update_status(
            owner=owner,
            section="wallet",
            is_success=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_corporation(owner_pk=owner.pk, force_refresh=False)

        # Expected Result
        mock_logger.info.assert_called_with("No updates needed for %s", owner.name)
        mock_update_corp_wallet.assert_not_called()
        # Ensure update manager reports no update needed
        self.assertFalse(owner.update_manager.calc_update_needed())

    @patch(MODELS_PATH + ".CorporationOwner.objects.get")
    def test_update_corp_section(self, mock_corp_owner_get):
        """
        Test update of a corporation section.

        Results:
            - CorporationUpdateStatus is created/updated correctly.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user)
        dummy_result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
            error_message="",
            data="Dummy Data",
        )
        update_status = CorporationUpdateStatus.objects.filter(
            owner=owner, section="wallet"
        ).first()

        mock_corp_owner_get.return_value = owner
        mock_corp_owner_get.update_manager = MagicMock()
        mock_update_manager = mock_corp_owner_get.update_manager
        mock_update_manager.perform_update_status.return_value = MagicMock()
        mock_update_manager.update_section_log.return_value = dummy_result

        # Test Action
        _update_corp_section(owner_pk=owner.pk, section="wallet", force_refresh=False)

        # Expected Results
        new_update_status = CorporationUpdateStatus.objects.get(
            owner=owner, section="wallet"
        )
        self.assertEqual(update_status, None)
        self.assertEqual(new_update_status.has_token_error, False)
        self.assertEqual(new_update_status.is_success, True)

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    @patch(TASKS_PATH + ".logger")
    @patch(TASKS_PATH + ".update_ally_deadlines")
    @patch(TASKS_PATH + ".AllianceUpdateSection.get_sections", lambda: ["deadlines"])
    def test_update_alliance(
        self, mock_update_deadlines: MagicMock, mock_logger: MagicMock
    ):
        """
        Test 'update_alliance' task.

        # Test Scenarios:
            1. Task updates alliance owner data (only deadlines).
            2. Task no need update when data is fresh.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user, tax_type="alliance")

        # Test Action
        update_alliance(owner_pk=owner.pk, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.name
        )

        # Setup for Scenario 2: No update needed
        mock_update_deadlines.reset_mock()
        create_update_status(
            owner=owner,
            tax_type="alliance",
            section="deadlines",
            is_success=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_alliance(owner_pk=owner.pk, force_refresh=False)

        # Expected Result
        mock_logger.info.assert_called_with("No updates needed for %s", owner.name)
        mock_update_deadlines.assert_not_called()
        # Ensure update manager reports no update needed
        self.assertFalse(owner.update_manager.calc_update_needed())

    @patch(MODELS_PATH + ".AllianceOwner.objects.get")
    def test_update_alliance_section(self, mock_owner_get):
        """
        Test update of a alliance section.

        Results:
            - AllianceUpdateStatus is created/updated correctly.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user, tax_type="alliance")
        dummy_result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
            error_message="",
            data="Dummy Data",
        )
        update_status = AllianceUpdateStatus.objects.filter(
            owner=owner, section="deadlines"
        ).first()

        mock_owner_get.return_value = owner
        mock_owner_get.update_manager = MagicMock()
        mock_update_manager = mock_owner_get.update_manager
        mock_update_manager.perform_update_status.return_value = MagicMock()
        mock_update_manager.update_section_log.return_value = dummy_result

        # Test Action
        _update_ally_section(
            owner_pk=owner.pk, section="deadlines", force_refresh=False
        )

        # Expected Results
        new_update_status = AllianceUpdateStatus.objects.get(
            owner=owner, section="deadlines"
        )
        self.assertEqual(update_status, None)
        self.assertEqual(new_update_status.has_token_error, False)
        self.assertEqual(new_update_status.is_success, True)

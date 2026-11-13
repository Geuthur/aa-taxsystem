"""Tests for the providers module."""

# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, PropertyMock, patch

# Third Party
import pook
from aiopenapi3 import RequestError
from celery import states
from celery.exceptions import Retry
from celery.result import EagerResult

# Django
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone

# Alliance Auth
from allianceauth.groupmanagement.models import Group
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)

# AA TaxSystem
from taxsystem import tasks
from taxsystem.errors import DownTimeError
from taxsystem.models.alliance import AllianceUpdateStatus
from taxsystem.models.corporation import CorporationOwner, CorporationUpdateStatus
from taxsystem.models.helpers.update_manager import (
    CorporationUpdateSection,
    UpdateSectionResult,
)
from taxsystem.providers import DOWNTIME_TIMER
from taxsystem.tasks import (
    _send_alliance_notification,
    _send_corporation_notification,
    _update_ally_section,
    _update_corp_section,
    check_account_deposit,
    update_all_taxsytem,
    update_alliance,
    update_corporation,
)
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.esi import (
    clear_esi_limits,
    corp_wallet_bucket_key,
    divisions_url,
)
from taxsystem.tests.testdata.factory import (
    AllianceGroupFactory,
    AllianceOwnerFactory,
    AllianceTaxAccountFactory,
    AllianceUpdateStatusFactory,
    CorporationGroupFactory,
    CorporationOwnerFactory,
    CorporationTaxAccountFactory,
    CorporationUpdateStatusFactory,
    UserMainFactory,
)

TASKS_PATH = "taxsystem.tasks"
MANAGERS_PATH = "taxsystem.managers"
MODELS_PATH = "taxsystem.models"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestTasks(AuthTestCase):
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
        CorporationOwnerFactory(user=self.user)
        AllianceOwnerFactory(user=self.user)

        # Test Action
        update_all_taxsytem(force_refresh=False)

        # Expected Result
        self.assertTrue(mock_update_corporation.apply_async.called)
        self.assertTrue(mock_update_alliance.apply_async.called)

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
        owner = CorporationOwnerFactory(user=self.user)

        # Test Action
        update_corporation(owner_eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.name
        )

        # Setup for Scenario 2: No update needed
        mock_update_corp_wallet.reset_mock()
        CorporationUpdateStatusFactory(
            owner=owner,
            section="wallet",
            is_success=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_corporation(owner_eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.info.assert_called_with("No updates needed for %s", owner.name)
        mock_update_corp_wallet.assert_not_called()
        # Ensure update manager reports no update needed
        self.assertFalse(owner.update_manager.calc_update_needed())

    @patch(MODELS_PATH + ".CorporationOwner.update_manager", new_callable=PropertyMock)
    @patch(MODELS_PATH + ".CorporationOwner.objects.get")
    def test_update_corp_section(
        self, mock_corp_owner_get, mock_update_manager_property
    ):
        """
        Test update of a corporation section.

        Results:
            - CorporationUpdateStatus is created/updated correctly.
        """
        # Test Data
        owner = CorporationOwnerFactory(user=self.user)
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
        mock_update_manager = MagicMock()
        mock_update_manager_property.return_value = mock_update_manager

        def _mock_execute_section(section, force_refresh=False):
            CorporationUpdateStatusFactory(
                owner=owner,
                section=section,
                has_token_error=dummy_result.has_token_error,
                is_success=not dummy_result.has_token_error,
                error_message=dummy_result.error_message,
            )
            return dummy_result

        mock_update_manager.execute_section.side_effect = _mock_execute_section

        # Test Action
        _update_corp_section(
            owner_eve_id=owner.eve_id,
            section="wallet",
            force_refresh=False,
        )

        # Expected Results
        mock_update_manager.execute_section.assert_called_once_with(
            "wallet", force_refresh=False
        )
        new_update_status = CorporationUpdateStatus.objects.get(
            owner=owner, section="wallet"
        )
        self.assertEqual(update_status, None)
        self.assertEqual(new_update_status.has_token_error, False)
        self.assertEqual(new_update_status.is_success, True)

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
        owner = AllianceOwnerFactory(user=self.user)

        # Test Action
        update_alliance(owner_eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.name
        )

        # Setup for Scenario 2: No update needed
        mock_update_deadlines.reset_mock()
        AllianceUpdateStatusFactory(
            owner=owner,
            section="deadlines",
            is_success=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_alliance(owner_eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.info.assert_called_with("No updates needed for %s", owner.name)
        mock_update_deadlines.assert_not_called()
        # Ensure update manager reports no update needed
        self.assertFalse(owner.update_manager.calc_update_needed())

    @patch(MODELS_PATH + ".AllianceOwner.update_manager", new_callable=PropertyMock)
    @patch(MODELS_PATH + ".AllianceOwner.objects.get")
    def test_update_alliance_section(
        self, mock_owner_get, mock_update_manager_property
    ):
        """
        Test update of a alliance section.

        Results:
            - AllianceUpdateStatus is created/updated correctly.
        """
        # Test Data
        owner = AllianceOwnerFactory(user=self.user)
        token = self.user.token_set.first()
        owner.get_token = MagicMock(return_value=token)
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
        mock_update_manager = MagicMock()
        mock_update_manager_property.return_value = mock_update_manager

        def _mock_execute_section(section, force_refresh=False):
            AllianceUpdateStatusFactory(
                owner=owner,
                section=section,
                has_token_error=dummy_result.has_token_error,
                is_success=not dummy_result.has_token_error,
                error_message=dummy_result.error_message,
            )
            return dummy_result

        mock_update_manager.execute_section.side_effect = _mock_execute_section
        # Test Action
        _update_ally_section(
            owner_eve_id=owner.eve_id,
            section="deadlines",
            force_refresh=False,
        )

        # Expected Results
        mock_update_manager.execute_section.assert_called_once_with(
            "deadlines", force_refresh=False
        )
        new_update_status = AllianceUpdateStatus.objects.get(
            owner=owner, section="deadlines"
        )
        self.assertEqual(update_status, None)
        self.assertEqual(new_update_status.has_token_error, False)
        self.assertEqual(new_update_status.is_success, True)

    @patch(TASKS_PATH + "._send_corporation_notification", return_value=None)
    @patch(TASKS_PATH + "._send_alliance_notification", return_value=None)
    @patch(TASKS_PATH + ".logger")
    def test_check_accounts_deposit(
        self,
        mock_logger,
        mock_send_alliance_notification,
        mock_send_corporation_notification,
    ):
        """
        Test the deposit check for tax accounts.

        Results:
            - Sent notifications for accounts with insufficient deposit.
        """
        # Test Data
        audit = AllianceOwnerFactory(user=self.user)

        AllianceTaxAccountFactory(
            owner=audit, name="Test Account", user=self.user, deposit=-1000
        )
        # Test Action
        check_account_deposit()

        # Expected Result
        mock_logger.info.assert_called_with(
            "Queued %s notification tasks for overdue payments", 2
        )

    @patch(TASKS_PATH + ".send_user_notification")
    def test_send_corporation_notification(self, mock_send):
        """
        Test sending corporation notification.

        Results:
            - Corporation notification is sent correctly.
        """
        # Test Data
        audit = CorporationOwnerFactory(user=self.user)
        CorporationTaxAccountFactory(
            owner=audit,
            name="Test Account",
            user=self.user,
            deposit=-1000,
            status="active",
        )

        # Test Action
        _send_corporation_notification(
            owner_eve_id=audit.eve_corporation.corporation_id
        )

        # Expected Result
        mock_send.assert_called()

    @patch(TASKS_PATH + ".send_user_notification")
    def test_send_alliance_notification(self, mock_send):
        """
        Test sending alliance notification.

        Results:
            - Alliance notification is sent correctly.
        """
        # Test Data
        audit = AllianceOwnerFactory(user=self.user)
        AllianceTaxAccountFactory(
            owner=audit,
            name="Test Account",
            user=self.user,
            deposit=-1000,
            status="active",
        )

        # Test Action
        _send_alliance_notification(owner_eve_id=audit.eve_alliance.alliance_id)

        # Expected Result
        mock_send.assert_called()

    @patch(TASKS_PATH + ".send_user_notification")
    def test_send_corporation_notification_should_skip_tax_free_group_members(
        self, mock_send
    ):
        """
        Test that members of a tax-free group get no corporation notification.

        Results:
            - Only the member outside the tax-free group is notified.
        """
        # Test Data
        audit = CorporationOwnerFactory(user=self.user)
        CorporationTaxAccountFactory(
            owner=audit, user=self.user, deposit=-1000, status="active"
        )
        tax_free_user = UserMainFactory()
        tax_free_group = Group.objects.create(name="Tax Free Corporation Group")
        tax_free_group.user_set.add(tax_free_user)
        CorporationGroupFactory(owner=audit, groups=[tax_free_group])
        CorporationTaxAccountFactory(
            owner=audit, user=tax_free_user, deposit=-1000, status="active"
        )

        # Test Action
        _send_corporation_notification(
            owner_eve_id=audit.eve_corporation.corporation_id
        )

        # Expected Result
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs["user_id"], self.user.pk)

    @patch(TASKS_PATH + ".send_user_notification")
    def test_send_alliance_notification_should_skip_tax_free_group_members(
        self, mock_send
    ):
        """
        Test that members of a tax-free group get no alliance notification.

        Results:
            - Only the member outside the tax-free group is notified.
        """
        # Test Data
        audit = AllianceOwnerFactory(user=self.user)
        AllianceTaxAccountFactory(
            owner=audit, user=self.user, deposit=-1000, status="active"
        )
        tax_free_user = UserMainFactory()
        tax_free_group = Group.objects.create(name="Tax Free Alliance Group")
        tax_free_group.user_set.add(tax_free_user)
        AllianceGroupFactory(owner=audit, groups=[tax_free_group])
        AllianceTaxAccountFactory(
            owner=audit, user=tax_free_user, deposit=-1000, status="active"
        )

        # Test Action
        _send_alliance_notification(owner_eve_id=audit.eve_alliance.alliance_id)

        # Expected Result
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs["user_id"], self.user.pk)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(
    TASKS_PATH + ".CorporationUpdateSection.get_sections", lambda: ["division_names"]
)
@patch.object(tasks.update_corporation, "retry", side_effect=Retry)
class TestUpdateCorporationEsiErrors(AuthTestCase):
    """ESI errors of a section reach `retry_task_on_esi_error` through the UpdateManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CorporationOwnerFactory(user=cls.user)
        cls.token = cls.user.token_set.first()

    def setUp(self):
        super().setUp()
        clear_esi_limits(self.token)
        self.addCleanup(clear_esi_limits, self.token)
        patcher = patch.object(
            CorporationOwner, "get_token", return_value=self.token, autospec=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _assert_retried(self, mock_retry, exc_type, countdown_min: float):
        mock_retry.assert_called_once()
        kwargs = mock_retry.call_args.kwargs
        self.assertIsInstance(kwargs["exc"], exc_type)
        self.assertGreaterEqual(kwargs["countdown"], countdown_min)
        status = CorporationUpdateStatus.objects.get(
            owner=self.owner, section=CorporationUpdateSection.DIVISION_NAMES
        )
        self.assertFalse(status.is_success)
        self.assertTrue(status.error_message.startswith(exc_type.__name__))

    def test_should_retry_on_esi_server_errors(self, mock_retry):
        for status_code in [
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                mock_retry.reset_mock()
                pook.get(
                    divisions_url(self.owner),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                with self.assertRaises(Retry):
                    tasks.update_corporation(self.owner.eve_id)

                # Expected Result
                self._assert_retried(mock_retry, HTTPServerError, DOWNTIME_TIMER)

    @pook.on
    def test_should_retry_on_the_esi_error_limit(self, mock_retry):
        # Test Data
        pook.get(
            divisions_url(self.owner),
            reply=420,
            response_json={"error": "Error limited"},
            response_headers={"X-RateLimit-Reset": "30"},
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_corporation(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, ESIErrorLimitException, 30)

    @pook.on
    def test_should_retry_on_the_esi_bucket_limit(self, mock_retry):
        # Test Data: the corp-wallet bucket of the token is used up
        cache.set(corp_wallet_bucket_key(self.token), 0, timeout=900)

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_corporation(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, ESIBucketLimitException, 1)

    @pook.on
    @patch("esi.app_settings.ESI_SERVER_ERROR_MAX_RETRIES", 1)
    def test_should_retry_on_request_errors(self, mock_retry):
        # Test Data
        pook.get(divisions_url(self.owner)).error(ConnectionError("Connection reset"))

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_corporation(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, RequestError, DOWNTIME_TIMER)

    @patch.object(CorporationOwner, "update_division_names", autospec=True)
    def test_should_retry_on_downtime_errors_of_a_section(
        self, mock_update_division_names, mock_retry
    ):
        # Test Data
        mock_update_division_names.side_effect = DownTimeError(
            "ESI is in daily downtime"
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_corporation(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, DownTimeError, DOWNTIME_TIMER)

    def test_should_record_other_esi_errors_without_retry(self, mock_retry):
        for status_code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.NOT_FOUND]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                pook.get(
                    divisions_url(self.owner),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                result = tasks.update_corporation(self.owner.eve_id)

                # Expected Result
                self.assertTrue(result)
                mock_retry.assert_not_called()
                status = CorporationUpdateStatus.objects.get(
                    owner=self.owner, section=CorporationUpdateSection.DIVISION_NAMES
                )
                self.assertFalse(status.is_success)
                self.assertIn(str(status_code.value), status.error_message)

    def test_section_task_should_retry_on_its_own(self, mock_retry):
        """A section task queued on its own retries itself."""
        with (
            pook.use(),
            patch.object(
                tasks.update_corp_division_names, "retry", side_effect=Retry
            ) as mock_section_retry,
        ):
            # Test Data
            pook.get(
                divisions_url(self.owner),
                reply=HTTPStatus.BAD_GATEWAY,
                response_json={"error": "Bad Gateway"},
            )

            # Test Action
            with self.assertRaises(Retry):
                tasks.update_corp_division_names(
                    owner_eve_id=self.owner.eve_id, force_refresh=False
                )

        # Expected Result
        mock_section_retry.assert_called_once()
        self.assertIsInstance(
            mock_section_retry.call_args.kwargs["exc"], HTTPServerError
        )
        mock_retry.assert_not_called()


@patch("celery.app.task.Task.apply_async")
class TestOwnerTasksRunOnce(AuthTestCase):
    """Owner tasks are queued only once per `owner_eve_id` (QueueOnce)."""

    OWNER_TASKS = [
        (tasks.update_corporation, {"force_refresh": False}),
        (tasks.update_corp_wallet, {"force_refresh": False}),
        (tasks.update_corp_payments, {"force_refresh": False}),
        (tasks.update_alliance, {"force_refresh": False}),
        (tasks.update_ally_payments, {"force_refresh": False}),
        (tasks._send_corporation_notification, {}),
    ]

    def _lock_key(self, task, owner_eve_id: int, kwargs: dict) -> str:
        key = task.get_key(args=[owner_eve_id], kwargs=kwargs)
        self.addCleanup(task.once_backend.clear_lock, key)
        return key

    def test_should_skip_second_apply_async_for_the_same_owner(self, mock_apply_async):
        for task, kwargs in self.OWNER_TASKS:
            with self.subTest(task=task.name):
                # Test Data
                mock_apply_async.reset_mock()
                self._lock_key(task, 1001, kwargs)

                # Test Action
                task.apply_async(args=[1001], kwargs=kwargs)
                result = task.apply_async(args=[1001], kwargs=kwargs)

                # Expected Result
                mock_apply_async.assert_called_once()
                self.assertEqual(result.state, "REJECTED")

    def test_should_mark_second_apply_async_as_skipped(self, mock_apply_async):
        # Test Data
        task = tasks.update_corporation
        self._lock_key(task, 1001, {"force_refresh": False})

        # Test Action
        first = task.apply_async(args=[1001], kwargs={"force_refresh": False})
        second = task.apply_async(args=[1001], kwargs={"force_refresh": False})

        # Expected Result
        self.assertFalse(tasks.is_task_skipped(first))
        self.assertTrue(tasks.is_task_skipped(second))

    def test_should_skip_update_all_gracefully_when_requested(self, mock_apply_async):
        """`update_all_taxsytem` is not graceful by default, the API passes `once`."""
        # Test Data
        task = tasks.update_all_taxsytem
        key = task.get_key(kwargs={"force_refresh": False})
        self.addCleanup(task.once_backend.clear_lock, key)
        task.apply_async(kwargs={"force_refresh": False})

        # Test Action
        result = task.apply_async(
            kwargs={"force_refresh": False}, once={"graceful": True}
        )

        # Expected Result
        mock_apply_async.assert_called_once()
        self.assertTrue(tasks.is_task_skipped(result))

    def test_should_queue_tasks_for_other_owners(self, mock_apply_async):
        for task, kwargs in self.OWNER_TASKS:
            with self.subTest(task=task.name):
                # Test Data
                mock_apply_async.reset_mock()
                self._lock_key(task, 1001, kwargs)
                self._lock_key(task, 1002, kwargs)

                # Test Action
                task.apply_async(args=[1001], kwargs=kwargs)
                task.apply_async(args=[1002], kwargs=kwargs)

                # Expected Result
                self.assertEqual(mock_apply_async.call_count, 2)

    def test_should_queue_retries_while_locked(self, mock_apply_async):
        """`self.retry` queues with `retries` set, which skips the lock."""
        # Test Data
        task = tasks.update_corporation
        self._lock_key(task, 1001, {})
        task.apply_async(args=[1001])

        # Test Action
        task.apply_async(args=[1001], retries=1)

        # Expected Result
        self.assertEqual(mock_apply_async.call_count, 2)

    @patch(TASKS_PATH + "._update_corp_section", return_value=True)
    def test_should_run_direct_calls_while_locked(
        self, mock_update_corp_section, mock_apply_async
    ):
        """`update_corporation` calls its section tasks directly, without the lock."""
        # Test Data
        task = tasks.update_corp_payments
        kwargs = {"force_refresh": False}
        self._lock_key(task, 1001, kwargs)
        task.apply_async(args=[1001], kwargs=kwargs)

        # Test Action
        result = task(owner_eve_id=1001, force_refresh=False)

        # Expected Result
        self.assertTrue(result)
        mock_update_corp_section.assert_called_once()


class TestIsTaskSkipped(AuthTestCase):
    def test_is_task_skipped_should_return_true_for_rejected_result(self):
        self.assertTrue(tasks.is_task_skipped(EagerResult(None, None, states.REJECTED)))

    def test_is_task_skipped_should_return_false_for_queued_result(self):
        self.assertFalse(tasks.is_task_skipped(EagerResult("id", None, states.SUCCESS)))
        self.assertFalse(tasks.is_task_skipped(MagicMock()))
        self.assertFalse(tasks.is_task_skipped(None))

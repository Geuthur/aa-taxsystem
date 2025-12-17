# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.alliance import (
    AllianceFilter,
    AlliancePaymentAccount,
)
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_filter,
    create_filterset,
    create_owner_from_user,
    create_payment,
    create_tax_account,
)

MODULE_PATH = "taxsystem.managers.alliance_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAllianceManager(TaxSystemTestCase):
    """Test Alliance Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(cls.user, tax_type="alliance")

        cls.filter_set = create_filterset(
            owner=cls.audit,
            name="100m",
            description="Filter for payments over 100m",
        )

        cls.filter_amount = create_filter(
            filter_set=cls.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            value=1000,
        )

    def test_update_tax_account(self):
        """
        Test updating alliance tax accounts payments.
        This test should change 2 Payments in the payment system depending on the given filters.

        Results:
            1. Approve a payment as APPROVED depending to the filter.
            2. Mark a payment as NEEDS_APPROVAL.
        """
        # Test Data
        self.tax_account = create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Approved Payment
        self.payments = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Needs Approval Payment
        self.payments2 = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            entry_id=2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Mining Stuff",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Test Action
        self.audit.update_payment_system(force_refresh=False)
        # Expected Results
        self.assertSetEqual(
            set(
                self.tax_account.ts_alliance_payments.values_list("entry_id", flat=True)
            ),
            {1, 2},
        )
        obj = self.tax_account.ts_alliance_payments.get(entry_id=1)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.APPROVED)

        obj = self.tax_account.ts_alliance_payments.get(entry_id=2)
        self.assertEqual(obj.amount, 6000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.NEEDS_APPROVAL)

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing(self, mock_logger):
        """Test should mark tax account as missing."""
        # Test Data
        self.tax_account = create_tax_account(
            name=self.user_2_character.character.character_name,
            owner=self.audit,
            user=self.user_2,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )
        # Test Action
        self.audit.update_payment_system(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user_2)
        self.assertEqual(tax_account.status, AccountStatus.MISSING)
        mock_logger.info.assert_any_call(
            "Marked Tax Account %s as MISSING",
            self.tax_account.name,
        )

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing_and_move_to_new_alliance(
        self, mock_logger
    ):
        """Test should mark tax account as missing and move to new alliance."""
        # Test Data
        self.audit_2 = create_owner_from_user(self.user_2, tax_type="alliance")
        self.tax_account = create_tax_account(
            name=self.user_2_character.character.character_name,
            owner=self.audit,
            user=self.user_2,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Test Action
        self.audit.update_payment_system(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user_2)
        self.assertEqual(tax_account.status, AccountStatus.ACTIVE)
        self.assertEqual(tax_account.owner, self.audit_2)
        mock_logger.info.assert_any_call(
            "Moved Tax Account %s to Alliance %s",
            self.tax_account.name,
            self.audit_2.eve_alliance.alliance_name,
        )

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_reset_a_returning_user(self, mock_logger):
        """Test should reset a tax account after a user returning to previous alliance."""
        # Test Data
        self.tax_account = create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.MISSING,
            deposit=10000,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Test Action
        self.audit.update_payment_system(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user)
        self.assertEqual(tax_account.deposit, 0)
        self.assertEqual(tax_account.status, AccountStatus.ACTIVE)
        self.assertEqual(tax_account.owner, self.audit)
        mock_logger.info.assert_any_call(
            "Reset Tax Account %s",
            self.tax_account.name,
        )

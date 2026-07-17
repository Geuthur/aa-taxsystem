# Standard Library
from unittest.mock import patch

# Django
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.alliance import (
    AllianceFilter,
    AlliancePaymentAccount,
    AlliancePayments,
)
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    FilterMatchType,
    PaymentRequestStatus,
)
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceFilterFactory,
    AllianceFilterSetFactory,
    AllianceOwnerFactory,
    AlliancePaymentsFactory,
    AllianceTaxAccountFactory,
    CorporationJournalFactory,
    DivisionFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.managers.alliance_manager"


class TestAllianceManager(TaxSystemTestCase):
    """Test Alliance Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = AllianceOwnerFactory(user=cls.user)

        cls.filter_set = AllianceFilterSetFactory(
            owner=cls.audit,
            name="Test Filter Set",
            description="Filter Set for Testing Alliance Manager",
            enabled=True,
        )
        cls.division = DivisionFactory(
            corporation=cls.audit.corporation,
            name="Main Division",
            balance=1000000,
            division_id=1,
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
        tax_account = AllianceTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        journal_entry = CorporationJournalFactory(
            division=self.division,
            amount=1000,
        )

        journal_entry2 = CorporationJournalFactory(
            division=self.division,
            amount=6000,
        )

        AllianceFilterFactory(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            match_type=FilterMatchType.EXACT,
            value="1000",
        )

        # Approved Payment
        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry,
            amount=1000,
            request_status=PaymentRequestStatus.PENDING,
        )

        # Needs Approval Payment
        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry2,
            amount=6000,
            request_status=PaymentRequestStatus.PENDING,
        )

        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)
        # Expected Results
        self.assertSetEqual(
            set(
                self.audit.ts_alliance_payments.values_list(
                    "journal__entry_id", flat=True
                )
            ),
            {journal_entry.entry_id, journal_entry2.entry_id},
        )
        obj: AlliancePayments = self.audit.ts_alliance_payments.get(
            journal__entry_id=journal_entry.entry_id
        )
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.APPROVED)

        obj: AlliancePayments = self.audit.ts_alliance_payments.get(
            journal__entry_id=journal_entry2.entry_id
        )
        self.assertEqual(obj.amount, 6000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.NEEDS_APPROVAL)

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing(self, mock_logger):
        """
        Test should mark tax account as missing.

        Results:
            1. Mark a tax account as MISSING when the user is no longer in the alliance.
        """
        # Test Data
        missing_user = UserMainFactory()
        missing_user_character = missing_user.profile.main_character

        AllianceTaxAccountFactory(
            name=missing_user_character.character_name,
            owner=self.audit,
            user=missing_user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )
        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=missing_user)
        self.assertEqual(tax_account.status, AccountStatus.MISSING)
        mock_logger.info.assert_any_call(
            "Marked Tax Account %s as MISSING",
            tax_account.name,
        )

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing_and_move_to_new_alliance(
        self, mock_logger
    ):
        """
        Test should mark tax account as missing and move to new alliance.

        Results:
            1. Move a tax account to a new alliance when the user has changed alliance.
        """
        # Test Data
        missing_user = UserMainFactory()
        missing_user_character = missing_user.profile.main_character
        audit_2 = AllianceOwnerFactory(user=missing_user)

        AllianceTaxAccountFactory(
            name=missing_user_character.character_name,
            owner=self.audit,
            user=missing_user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=missing_user)

        self.assertEqual(tax_account.status, AccountStatus.ACTIVE)
        self.assertEqual(tax_account.owner, audit_2)
        mock_logger.info.assert_any_call(
            "Moved Tax Account %s to Alliance %s",
            tax_account.name,
            audit_2.eve_alliance.alliance_name,
        )

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_reset_a_returning_user(self, mock_logger):
        """
        Test should reset a tax account after a user returning to previous alliance.

        Results:
            1. Reset a tax account when the user was missing and has returned to the previous alliance.
        """
        # Test Data
        AllianceTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.MISSING,
            deposit=10000,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user)
        self.assertEqual(tax_account.deposit, 0)
        self.assertEqual(tax_account.status, AccountStatus.ACTIVE)
        self.assertEqual(tax_account.owner, self.audit)
        mock_logger.info.assert_any_call(
            "Reset Tax Account %s",
            tax_account.name,
        )

    def test_payment_deadlines(self):
        """
        Test payment deadlines processing for alliance tax accounts.
        This test should process the payment deadlines for alliance tax accounts, deducting the tax amount from the deposit.

        Results:
            1. Tax Account deposit is reduced by the tax amount on payment deadlines.
            2. New users within the free period are not charged.
        """
        # Test Data
        self.audit.tax_amount = 1000
        AllianceTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=1000,
            last_paid=(timezone.now() - timezone.timedelta(days=60)),
        )
        self.new_user = UserMainFactory()

        # 1 Month is free for new users
        AllianceTaxAccountFactory(
            name=self.new_user.profile.main_character.character_name,
            owner=self.audit,
            user=self.new_user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=None,
        )

        # Test Action
        self.audit.update_deadlines(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user)
        self.assertEqual(tax_account.deposit, 0)
        tax_account_2 = AlliancePaymentAccount.objects.get(user=self.new_user)
        self.assertEqual(tax_account_2.deposit, 0)

    def test_update_tax_accounts_approve_with_1_filter_sets(self):
        """
        Test should approve payments with the given automatic payment filters.

        # Test Scenarios:
            1. First Payment match in Filter Set and will be approved.
            2. Second Payment does not match Filter Set and will be marked as needs approval.
        """
        # Test Data
        tax_account = AllianceTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        AllianceFilterFactory(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.REASON,
            match_type=FilterMatchType.CONTAINS,
            value="Payments",
        )

        AllianceFilterFactory(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            match_type=FilterMatchType.EXACT,
            value=1000,
        )

        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            reason="Approved Payments",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            reason="Other Reason",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user)
        approved_payment = AlliancePayments.objects.get(reason="Approved Payments")
        needs_approval = AlliancePayments.objects.get(reason="Other Reason")
        self.assertEqual(approved_payment.request_status, PaymentRequestStatus.APPROVED)
        self.assertEqual(tax_account.deposit, 1000)
        self.assertEqual(
            needs_approval.request_status, PaymentRequestStatus.NEEDS_APPROVAL
        )

    def test_update_tax_accounts_approve_with_2_filter_sets(self):
        """
        Test should approve payments with the given automatic payment filters.

        # Test Scenarios:
            1. First Payment match in Filter Set 1 and will be approved.
            2. Second Payment match in Filter Set 2 and will be approved.
            3. Third Payment does not match any filter set filters and will be marked as needs approval.
        """
        # Test Data
        tax_account = AllianceTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        filter_set2 = AllianceFilterSetFactory(
            owner=self.audit,
            name="Test Filter Set 2",
            description="Second Filter Set for Testing Alliance Manager",
            enabled=True,
        )

        AllianceFilterFactory(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.REASON,
            match_type=FilterMatchType.CONTAINS,
            value="Payments",
        )

        AllianceFilterFactory(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            match_type=FilterMatchType.EXACT,
            value=1000,
        )

        AllianceFilterFactory(
            filter_set=filter_set2,
            filter_type=AllianceFilter.FilterType.REASON,
            match_type=FilterMatchType.CONTAINS,
            value="Reason",
        )

        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            reason="Approved Payments",
            request_status=PaymentRequestStatus.PENDING,
        )

        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            reason="Other Reason",
            request_status=PaymentRequestStatus.PENDING,
        )

        AlliancePaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            reason="2025",
            request_status=PaymentRequestStatus.PENDING,
        )

        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user)
        approved_payment = AlliancePayments.objects.get(reason="Approved Payments")
        approved_payment2 = AlliancePayments.objects.get(reason="Other Reason")
        needs_approval = AlliancePayments.objects.get(reason="2025")
        self.assertEqual(approved_payment.request_status, PaymentRequestStatus.APPROVED)
        self.assertEqual(
            approved_payment2.request_status, PaymentRequestStatus.APPROVED
        )
        self.assertEqual(
            needs_approval.request_status, PaymentRequestStatus.NEEDS_APPROVAL
        )
        self.assertEqual(tax_account.deposit, 2000)

    def test_update_payments(self):
        """
        Test update corporation payments.
        This test should update or create corporation payments based on wallet journal entries.

        Results:
            1. Existing payment is updated.
            2. New payments are created based on wallet journal entries.
            3. Payments with missing parties are skipped.
        """
        # Test Data
        AllianceTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        journal = CorporationJournalFactory(
            ref_type="player_donation",
        )

        # The second journal entry should not create a payment because it doesn't have a first_party
        error_journal = CorporationJournalFactory(
            first_party=None,
        )
        # Test Action
        self.audit.update_payments(force_refresh=False)

        # Expected Results
        obj = self.audit.ts_alliance_payments.get(journal__entry_id=journal.entry_id)
        self.assertEqual(obj.amount, journal.amount)
        self.assertEqual(obj.request_status, PaymentRequestStatus.PENDING)

        # The second journal entry should not create a payment because it doesn't have a first_party
        with self.assertRaises(AlliancePayments.DoesNotExist):
            self.audit.ts_alliance_payments.get(
                journal__entry_id=error_journal.entry_id
            )

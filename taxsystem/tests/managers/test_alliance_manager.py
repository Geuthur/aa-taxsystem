# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.alliance import (
    AllianceFilter,
    AlliancePaymentAccount,
    AlliancePayments,
)
from taxsystem.models.general import EveEntity
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    FilterMatchType,
    PaymentRequestStatus,
)
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_division,
    create_filter,
    create_filterset,
    create_owner_from_user,
    create_payment,
    create_tax_account,
    create_user_from_evecharacter,
    create_wallet_journal_entry,
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
            name="Test Filter Set",
            description="Filter Set for Testing Alliance Manager",
        )

        cls.division = create_division(
            corporation=cls.audit.corporation,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

        cls.eve_character_first_party = EveEntity.objects.get(id=1002)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

    def test_update_tax_account(self):
        """
        Test updating alliance tax accounts payments.
        This test should change 2 Payments in the payment system depending on the given filters.

        Results:
            1. Approve a payment as APPROVED depending to the filter.
            2. Mark a payment as NEEDS_APPROVAL.
        """
        # Test Data
        tax_account = create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.eve_character_first_party,
            second_party=self.eve_character_second_party,
            description="Test Description",
        )

        journal_entry2 = create_wallet_journal_entry(
            division=self.division,
            entry_id=2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Mining Stuff",
            ref_type="tax_payment",
            first_party=self.eve_character_first_party,
            second_party=self.eve_character_second_party,
            description="Test Description 2",
        )

        create_filter(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            match_type=FilterMatchType.EXACT,
            value="1000",
        )

        # Approved Payment
        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Needs Approval Payment
        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Mining Stuff",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
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
            {1, 2},
        )
        obj = self.audit.ts_alliance_payments.get(journal__entry_id=1)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.APPROVED)

        obj = self.audit.ts_alliance_payments.get(journal__entry_id=2)
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
        create_tax_account(
            name=self.user2_character.character.character_name,
            owner=self.audit,
            user=self.user2,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )
        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user2)
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
        audit_2 = create_owner_from_user(self.user2, tax_type="alliance")
        create_tax_account(
            name=self.user2_character.character.character_name,
            owner=self.audit,
            user=self.user2,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)

        # Expected Results
        tax_account = AlliancePaymentAccount.objects.get(user=self.user2)
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
        create_tax_account(
            name=self.user_character.character.character_name,
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
        create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=1000,
            last_paid=(timezone.now() - timezone.timedelta(days=60)),
        )
        self.new_user, self.new_user_character = create_user_from_evecharacter(
            character_id=1006,
            permissions=["taxsystem.basic_access"],
        )

        # 1 Month is free for new users
        create_tax_account(
            name=self.new_user_character.character.character_name,
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
        tax_account = create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        create_filter(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.REASON,
            match_type=FilterMatchType.CONTAINS,
            value="Payments",
        )

        create_filter(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            match_type=FilterMatchType.EXACT,
            value=1000,
        )

        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Approved Payments",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
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
        tax_account = create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        filter_set2 = create_filterset(
            owner=self.audit,
            name="Test Filter Set 2",
            description="Second Filter Set for Testing Alliance Manager",
        )

        create_filter(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.REASON,
            match_type=FilterMatchType.CONTAINS,
            value="Payments",
        )

        create_filter(
            filter_set=self.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            match_type=FilterMatchType.EXACT,
            value=1000,
        )

        create_filter(
            filter_set=filter_set2,
            filter_type=AllianceFilter.FilterType.REASON,
            match_type=FilterMatchType.CONTAINS,
            value="Reason",
        )

        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Approved Payments",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Other Reason",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        create_payment(
            name=self.user_character.character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="2025",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
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

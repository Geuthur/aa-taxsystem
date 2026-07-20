# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Third Party
import pook

# Django
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationPaymentAccount,
    CorporationPayments,
    Members,
)
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationFilterFactory,
    CorporationFilterSetFactory,
    CorporationJournalFactory,
    CorporationOwnerFactory,
    CorporationPaymentsFactory,
    CorporationTaxAccountFactory,
    DivisionFactory,
    MembersFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.managers.corporation_manager"


class TestCorporationManager(TaxSystemTestCase):
    """Test Corporation Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = CorporationOwnerFactory(user=cls.user)

        cls.filter_set = CorporationFilterSetFactory(
            owner=cls.audit,
            name="100m",
            description="Filter for payments over 100m",
            enabled=True,
        )

        cls.filter_amount = CorporationFilterFactory(
            filter_set=cls.filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000,
        )

        cls.division = DivisionFactory(
            corporation=cls.audit,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

    def test_update_tax_account(self):
        """
        Test updating corporation tax accounts payments.
        This test should change 2 Payments in the payment system depending on the given filters.

        Results:
            1. Approve a payment as APPROVED depending to the filter.
            2. Mark a payment as NEEDS_APPROVAL.
        """
        # Test Data
        tax_account = CorporationTaxAccountFactory(
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

        # Approved Payment
        CorporationPaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0),
            request_status=PaymentRequestStatus.PENDING,
        )

        # Needs Approval Payment
        CorporationPaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0),
            request_status=PaymentRequestStatus.PENDING,
        )
        print("before: %s", self.audit.ts_corporation_payments)
        # Test Action
        self.audit.update_tax_accounts(force_refresh=False)
        print("after: %s", self.audit.ts_corporation_payments)
        # Expected Results
        self.assertSetEqual(
            set(
                self.audit.ts_corporation_payments.values_list(
                    "journal__entry_id", flat=True
                )
            ),
            {journal_entry.entry_id, journal_entry2.entry_id},
        )
        obj = self.audit.ts_corporation_payments.get(
            journal__entry_id=journal_entry.entry_id
        )
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.APPROVED)

        obj = self.audit.ts_corporation_payments.get(
            journal__entry_id=journal_entry2.entry_id
        )
        self.assertEqual(obj.amount, 6000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.NEEDS_APPROVAL)

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing(self, mock_logger):
        """Test should mark tax account as missing.

        Results:
            1. Mark a tax account as MISSING when the user is no longer in the corporation.
        """
        # Test Data
        missing_user = UserMainFactory()
        missing_user_character = missing_user.profile.main_character
        tax_account = CorporationTaxAccountFactory(
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
        tax_account = CorporationPaymentAccount.objects.get(user=missing_user)
        self.assertEqual(tax_account.status, AccountStatus.MISSING)
        mock_logger.info.assert_any_call(
            "Marked Tax Account %s as MISSING",
            tax_account.name,
        )

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing_and_move_to_new_corporation(
        self, mock_logger
    ):
        """
        Test should mark tax account as missing and move to new corporation.

        Results:
            1. Move a tax account to a new corporation when the user has changed corporation.
        """
        # Test Data
        missing_user = UserMainFactory()
        missing_user_character = missing_user.profile.main_character
        audit_2 = CorporationOwnerFactory(user=missing_user)
        tax_account = CorporationTaxAccountFactory(
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
        tax_account = CorporationPaymentAccount.objects.get(user=missing_user)
        self.assertEqual(tax_account.status, AccountStatus.ACTIVE)
        self.assertEqual(tax_account.owner, audit_2)
        mock_logger.info.assert_any_call(
            "Moved Tax Account %s to Corporation %s",
            tax_account.name,
            audit_2.eve_corporation.corporation_name,
        )

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_reset_a_returning_user(self, mock_logger):
        """
        Test should reset a tax account after a user returning to previous corporation.

        Results:
            1. Reset a tax account when the user was missing and has returned to the previous corporation.
        """
        # Test Data
        tax_account = CorporationTaxAccountFactory(
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
        tax_account = CorporationPaymentAccount.objects.get(user=self.user)
        self.assertEqual(tax_account.deposit, 0)
        self.assertEqual(tax_account.status, AccountStatus.ACTIVE)
        self.assertEqual(tax_account.owner, self.audit)
        mock_logger.info.assert_any_call(
            "Reset Tax Account %s",
            tax_account.name,
        )

    def test_payment_deadlines(self):
        """
        Test payment deadlines processing for corporation tax accounts.
        This test should process the payment deadlines for corporation tax accounts, deducting the tax amount from the deposit.

        Results:
            1. Tax Account deposit is reduced by the tax amount on payment deadlines.
            2. New users within the free period are not charged.
        """
        # Test Data
        self.audit.tax_amount = 1000
        tax_account = CorporationTaxAccountFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=1000,
            last_paid=(timezone.now() - timezone.timedelta(days=60)),
        )
        new_user = UserMainFactory()

        # 1 Month is free for new users
        tax_account_2 = CorporationTaxAccountFactory(
            name=new_user.profile.main_character.character_name,
            owner=self.audit,
            user=new_user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=None,
        )

        # Test Action
        self.audit.update_deadlines(force_refresh=False)

        # Expected Results
        tax_account = CorporationPaymentAccount.objects.get(user=self.user)
        self.assertEqual(tax_account.deposit, 0)
        tax_account_2 = CorporationPaymentAccount.objects.get(user=new_user)
        self.assertEqual(tax_account_2.deposit, 0)

    @patch(MODULE_PATH + ".EveEntity.objects.bulk_resolve_names")
    @patch(MODULE_PATH + ".logger")
    @pook.on
    def test_update_members(self, mock_logger, mock_bulk_resolve):
        """
        Test update corporation members.
        This test should update or create corporation members based on ESI data.

        Results:
            1. Existing member is updated.
            2. New members are created based on ESI data.
            3. Missing members are identified.

            2 New Members created, 1 Existing updated, 1 Missing
        """
        # Test Data
        MembersFactory(
            owner=self.audit,
            character_id=1001,
            character_name="Member 1",
            status=Members.States.ACTIVE,
        )

        MembersFactory(
            owner=self.audit,
            character_id=1004,
            character_name="Member 4",
            status=Members.States.ACTIVE,
        )

        # Mock ESI response for roles
        pook.get(
            url=f"https://esi.evetech.net/characters/{self.user_character.character_id}/roles",
            reply=HTTPStatus.OK,
            response_json={
                "character_id": 1001,
                "roles": ["Director", "Accountant"],
                "grantable_roles": ["Director", "Accountant"],
            },
        )

        # Mock ESI response for corporation members
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/membertracking",
            reply=HTTPStatus.OK,
            response_json=[
                {
                    "base_id": 1001,
                    "character_id": 1001,
                    "location_id": 30004783,
                    "logoff_date": "2025-05-21T21:42:41Z",
                    "logon_date": "2025-05-21T17:46:43Z",
                    "ship_type_id": 603,
                    "start_date": "2017-10-28T12:45:00Z",
                },
                {
                    "base_id": 1002,
                    "character_id": 1002,
                    "location_id": 30004783,
                    "logoff_date": "2025-04-16T21:09:26Z",
                    "logon_date": "2025-04-16T21:08:43Z",
                    "ship_type_id": 670,
                    "start_date": "2019-07-14T19:39:00Z",
                },
                {
                    "base_id": 1003,
                    "character_id": 1003,
                    "location_id": 30004783,
                    "logoff_date": "2025-04-16T21:12:51Z",
                    "logon_date": "2025-04-16T21:11:46Z",
                    "ship_type_id": 670,
                    "start_date": "2019-07-25T14:27:00Z",
                },
            ],
        )

        mock_bulk_resolve.return_value.to_name.side_effect = (
            "Member 1",
            "Member 2",
            "Member 3",
        )

        # Test Action
        self.audit.update_members(force_refresh=False)

        # Expected Results
        obj = Members.objects.get(character_id=1001)
        self.assertEqual(obj.character_name, "Member 1")
        obj = Members.objects.get(character_id=1002)
        self.assertEqual(obj.character_name, "Member 2")
        obj = Members.objects.get(character_id=1003)
        self.assertEqual(obj.character_name, "Member 3")

        mock_logger.info.assert_called_with(
            "%s - Old Members: %s, New Members: %s, Missing: %s",
            self.audit.eve_corporation.corporation_name,
            1,
            2,
            1,
        )

    def test_update_payments(self):
        """
        Test update corporation payments.
        This test should update or create corporation payments based on wallet journal entries.

        Results:
            1. Existing payment is updated.
            2. New payments are created based on wallet journal entries.
        """
        # Test Data
        CorporationTaxAccountFactory(
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
            ref_type="player_donation",
        )

        journal_entry2 = CorporationJournalFactory(
            division=self.division,
            amount=1000,
            ref_type="player_donation",
        )
        # Test Action
        self.audit.update_payments(force_refresh=False)

        # Expected Results
        obj = self.audit.ts_corporation_payments.get(
            journal__entry_id=journal_entry.entry_id
        )
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.PENDING)

        # The second journal entry should not create a payment because it doesn't have a first_party
        with self.assertRaises(CorporationPayments.DoesNotExist):
            self.audit.ts_corporation_payments.get(
                journal__entry_id=journal_entry2.entry_id
            )

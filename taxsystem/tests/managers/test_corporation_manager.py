# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationPaymentAccount,
    Members,
)
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)
from taxsystem.tests.testdata.utils import (
    create_division,
    create_filter,
    create_filterset,
    create_member,
    create_owner_from_user,
    create_payment,
    create_tax_account,
    create_user_from_evecharacter,
    create_wallet_journal_entry,
)

MODULE_PATH = "taxsystem.managers.corporation_manager"

TEST_CORPORATION_MANAGER_ENDPOINTS = [
    EsiEndpoint(
        "Corporation", "GetCorporationsCorporationIdMembertracking", "corporation_id"
    ),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestCorporationManager(TaxSystemTestCase):
    """Test Corporation Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(cls.user)

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

        cls.division = create_division(
            corporation=cls.audit,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

        cls.eve_character_first_party = EveEntity.objects.get(id=1002)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

    def test_update_tax_account(self):
        """
        Test updating corporation tax accounts payments.
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
            {1, 2},
        )
        obj = self.audit.ts_corporation_payments.get(journal__entry_id=1)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.APPROVED)

        obj = self.audit.ts_corporation_payments.get(journal__entry_id=2)
        self.assertEqual(obj.amount, 6000)
        self.assertEqual(obj.request_status, PaymentRequestStatus.NEEDS_APPROVAL)

    @patch(f"{MODULE_PATH}.logger")
    def test_update_tax_accounts_mark_as_missing(self, mock_logger):
        """Test should mark tax account as missing.

        Results:
            1. Mark a tax account as MISSING when the user is no longer in the corporation.
        """
        # Test Data
        tax_account = create_tax_account(
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
        tax_account = CorporationPaymentAccount.objects.get(user=self.user2)
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
        audit_2 = create_owner_from_user(self.user2)
        tax_account = create_tax_account(
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
        tax_account = CorporationPaymentAccount.objects.get(user=self.user2)
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
        tax_account = create_tax_account(
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
        tax_account = create_tax_account(
            name=self.user_character.character.character_name,
            owner=self.audit,
            user=self.user,
            status=AccountStatus.ACTIVE,
            deposit=1000,
            last_paid=(timezone.now() - timezone.timedelta(days=60)),
        )
        new_user, new_user_character = create_user_from_evecharacter(
            character_id=1006,
            permissions=["taxsystem.basic_access"],
        )

        # 1 Month is free for new users
        tax_account_2 = create_tax_account(
            name=new_user_character.character.character_name,
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

    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".EveEntity.objects.bulk_resolve_names")
    @patch(MODULE_PATH + ".logger")
    def test_update_members(self, mock_logger, mock_bulk_resolve, mock_esi):
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
        self.member = create_member(
            owner=self.audit,
            character_id=1001,
            character_name="Member 1",
            status=Members.States.ACTIVE,
        )

        self.missing_member = create_member(
            owner=self.audit,
            character_id=1004,
            character_name="Member 4",
            status=Members.States.ACTIVE,
        )

        mock_esi.client = create_esi_client_stub(
            endpoints=TEST_CORPORATION_MANAGER_ENDPOINTS
        )

        mock_bulk_resolve.return_value.to_name.side_effect = (
            "Member 1",
            "Member 2",
            "Member 3",
        )

        # Test Action
        self.audit.update_members(force_refresh=False)

        # Expected Results
        obj = self.audit.ts_members.get(character_id=1001)
        self.assertEqual(obj.character_name, "Member 1")
        obj = self.audit.ts_members.get(character_id=1002)
        self.assertEqual(obj.character_name, "Member 2")
        obj = self.audit.ts_members.get(character_id=1003)
        self.assertEqual(obj.character_name, "Member 3")

        mock_logger.info.assert_called_with(
            "%s - Old Members: %s, New Members: %s, Missing: %s",
            self.audit.eve_corporation.corporation_name,
            1,
            2,
            1,
        )

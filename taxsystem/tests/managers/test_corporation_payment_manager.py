# Standard Library
from unittest.mock import MagicMock, patch
from urllib import request

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase, create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationPaymentAccount,
    CorporationPayments,
)
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_member,
    create_payment,
    create_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.managers.wallet_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestPaymentsManager(NoSocketsTestCase):
    """Test Payments Manager for Corporation Journal Entries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )

        cls.audit = create_corporation_owner_from_user(
            user=cls.user,
            tax_amount=1000,
            tax_period=30,
        )

        cls.payment_system = create_payment_system(
            name=cls.character_ownership.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        cls.payments = create_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=CorporationPayments.RequestStatus.PENDING,
            reviser="",
        )

        cls.payments2 = create_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            entry_id=2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Mining Stuff",
            request_status=CorporationPayments.RequestStatus.PENDING,
            reviser="",
        )

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

    def test_update_payments(self):
        # given

        self.audit.update_payment_system(force_refresh=False)

        self.assertSetEqual(
            set(
                self.payment_system.ts_corporation_payments.values_list(
                    "entry_id", flat=True
                )
            ),
            {1, 2},
        )
        obj = self.payment_system.ts_corporation_payments.get(entry_id=1)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, CorporationPayments.RequestStatus.APPROVED)

        obj = self.payment_system.ts_corporation_payments.get(entry_id=2)
        self.assertEqual(obj.amount, 6000)
        self.assertEqual(
            obj.request_status, CorporationPayments.RequestStatus.NEEDS_APPROVAL
        )


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestPaymentAccountManager(NoSocketsTestCase):
    """Test Payment Account Manager methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(1001)
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(1002)

        cls.audit = create_corporation_owner_from_user(
            user=cls.user,
            tax_amount=1000,
            tax_period=30,
        )

    def test_cleanup_orphaned_accounts(self):
        """Test that orphaned accounts are cleaned up."""
        # Create a payment account
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
        )

        # Remove the main character to make it orphaned
        self.user.profile.main_character = None
        self.user.profile.save()

        # Get empty auth accounts queryset
        auth_accounts = self.user.profile.__class__.objects.filter(
            main_character__isnull=False,
            main_character__corporation_id=self.audit.eve_corporation.corporation_id,
        )

        # Run cleanup
        CorporationPaymentAccount.objects._cleanup_orphaned_accounts(
            self.audit, auth_accounts
        )

        # Verify account was deleted
        self.assertFalse(
            CorporationPaymentAccount.objects.filter(pk=payment_account.pk).exists()
        )

    def test_process_accounts_creates_new_account(self):
        """Test that new payment accounts are created."""
        # Ensure no payment account exists
        CorporationPaymentAccount.objects.filter(user=self.user).delete()

        # Get auth accounts
        auth_accounts = self.user.profile.__class__.objects.filter(
            main_character__isnull=False,
            main_character__corporation_id=self.audit.eve_corporation.corporation_id,
        )

        # Process accounts
        new_accounts = CorporationPaymentAccount.objects._process_accounts(
            self.audit, auth_accounts
        )

        # Verify new account was created
        self.assertEqual(len(new_accounts), 1)
        self.assertEqual(new_accounts[0].user, self.user)
        self.assertEqual(
            new_accounts[0].status, CorporationPaymentAccount.Status.ACTIVE
        )

    def test_update_existing_account_owner_change(self):
        """Test that existing account is updated when owner changes."""
        # Create second corporation owner
        audit2 = create_corporation_owner_from_user(
            user=self.user2,
            tax_amount=2000,
            tax_period=30,
        )

        # Create payment account for first owner
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=audit2,
            user=self.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=500,
        )

        # Update to new owner
        CorporationPaymentAccount.objects._update_existing_account(
            self.audit,
            payment_account,
            self.character_ownership.character,
        )

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify owner changed and deposit reset
        self.assertEqual(payment_account.owner, self.audit)
        self.assertEqual(payment_account.deposit, 0)

    def test_handle_corporation_change_mark_missing(self):
        """Test that account is marked as missing when user leaves corporation."""
        # Create payment account
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
        )

        # Simulate corporation change
        different_corp_id = 2001
        CorporationPaymentAccount.objects._handle_corporation_change(
            payment_account, different_corp_id
        )

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify marked as missing
        self.assertEqual(
            payment_account.status, CorporationPaymentAccount.Status.MISSING
        )

    def test_reactivate_missing_account(self):
        """Test that missing account is reactivated correctly."""
        # Create missing payment account with data
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.MISSING,
            deposit=500,
            last_paid=timezone.now() - timezone.timedelta(days=10),
        )
        payment_account.notice = "User left corp"
        payment_account.save()

        # Reactivate
        CorporationPaymentAccount.objects._reactivate_missing_account(payment_account)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify reactivation
        self.assertEqual(
            payment_account.status, CorporationPaymentAccount.Status.ACTIVE
        )
        self.assertEqual(payment_account.deposit, 0)
        self.assertIsNone(payment_account.last_paid)
        self.assertIsNone(payment_account.notice)

    def test_check_payment_accounts_full_flow(self):
        """Test full payment account check flow."""
        # Ensure clean state
        CorporationPaymentAccount.objects.filter(owner=self.audit).delete()

        # Run check
        CorporationPaymentAccount.objects._check_payment_accounts(self.audit)

        # Verify new accounts were created (both user and user2 have main chars in same corp)
        payment_accounts = CorporationPaymentAccount.objects.filter(owner=self.audit)
        self.assertEqual(payment_accounts.count(), 2)

        # Verify first user account
        account1 = payment_accounts.get(user=self.user)
        self.assertEqual(account1.status, CorporationPaymentAccount.Status.ACTIVE)
        self.assertEqual(
            account1.name, self.character_ownership.character.character_name
        )

        # Verify second user account
        account2 = payment_accounts.get(user=self.user2)
        self.assertEqual(account2.status, CorporationPaymentAccount.Status.ACTIVE)
        self.assertEqual(
            account2.name, self.character_ownership2.character.character_name
        )

    def test_update_existing_account_reactivate_not_deactivated(self):
        """Test that inactive account is reactivated if not deactivated."""
        # Create inactive payment account
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.INACTIVE,
        )

        # Update account
        CorporationPaymentAccount.objects._update_existing_account(
            self.audit,
            payment_account,
            self.character_ownership.character,
        )

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify reactivation
        self.assertEqual(
            payment_account.status, CorporationPaymentAccount.Status.ACTIVE
        )

    def test_update_existing_account_keep_deactivated(self):
        """Test that deactivated account stays deactivated."""
        # Create deactivated payment account
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.DEACTIVATED,
        )

        # Update account
        CorporationPaymentAccount.objects._update_existing_account(
            self.audit,
            payment_account,
            self.character_ownership.character,
        )

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify stays deactivated
        self.assertEqual(
            payment_account.status, CorporationPaymentAccount.Status.DEACTIVATED
        )

    def test_handle_corporation_change_move_to_new_corp(self):
        """Test moving account to new corporation when user changes corps."""
        # Create second corporation
        audit2 = create_corporation_owner_from_user(
            user=self.user2,
            tax_amount=2000,
            tax_period=30,
        )

        # Create missing payment account for first corp
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.MISSING,
            deposit=500,
            last_paid=timezone.now(),
        )

        # Simulate moving to second corp
        CorporationPaymentAccount.objects._handle_corporation_change(
            payment_account,
            audit2.eve_corporation.corporation_id,
        )

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify moved to new corp
        self.assertEqual(payment_account.owner, audit2)
        self.assertEqual(
            payment_account.status, CorporationPaymentAccount.Status.ACTIVE
        )
        self.assertEqual(payment_account.deposit, 0)
        self.assertIsNone(payment_account.last_paid)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestPayDayManager(NoSocketsTestCase):
    """Test Pay Day Manager methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(1001)

        cls.audit = create_corporation_owner_from_user(
            user=cls.user,
            tax_amount=1000,
            tax_period=30,
        )

    def test_pay_day_first_period_free(self):
        """Test that first period is free (last_paid is set but no deduction)."""
        # Create payment account without last_paid
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=5000,
            last_paid=None,
        )

        # Run payday
        CorporationPaymentAccount.objects._pay_day(self.audit)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify first period is free
        self.assertIsNotNone(payment_account.last_paid)
        self.assertEqual(payment_account.deposit, 5000)  # No deduction

    def test_pay_day_deduct_tax(self):
        """Test that tax is deducted after period expires."""
        # Create payment account with expired last_paid
        old_date = timezone.now() - timezone.timedelta(days=31)
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=5000,
            last_paid=old_date,
        )

        # Run payday
        CorporationPaymentAccount.objects._pay_day(self.audit)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify tax was deducted
        self.assertEqual(payment_account.deposit, 4000)  # 5000 - 1000
        self.assertNotEqual(payment_account.last_paid, old_date)

    def test_pay_day_skip_inactive(self):
        """Test that inactive accounts are skipped."""
        # Create inactive payment account
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.INACTIVE,
            deposit=5000,
            last_paid=timezone.now() - timezone.timedelta(days=31),
        )

        # Run payday
        CorporationPaymentAccount.objects._pay_day(self.audit)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify no deduction for inactive account
        self.assertEqual(payment_account.deposit, 5000)

    def test_pay_day_not_expired(self):
        """Test that tax is not deducted if period hasn't expired."""
        # Create payment account with recent last_paid
        recent_date = timezone.now() - timezone.timedelta(days=15)
        payment_account = create_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.audit,
            user=self.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=5000,
            last_paid=recent_date,
        )

        # Run payday
        CorporationPaymentAccount.objects._pay_day(self.audit)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify no deduction
        self.assertEqual(payment_account.deposit, 5000)
        self.assertEqual(payment_account.last_paid, recent_date)

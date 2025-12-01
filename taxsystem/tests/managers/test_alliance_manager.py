# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase, create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.alliance import AlliancePaymentAccount, AlliancePayments
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    create_alliance_owner_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_alliance_payment,
    create_alliance_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAlliancePaymentAccountManager(NoSocketsTestCase):
    """Test Alliance Payment Account Manager methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        # Create users with alliance characters (1001 and 1004 both belong to alliance 3001)
        cls.user, cls.character_ownership = create_user_from_evecharacter(1001)
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(1004)

        cls.alliance = create_alliance_owner_from_user(
            user=cls.user,
            tax_amount=1000,
            tax_period=30,
        )

    def test_update_payment_accounts_creates_new_accounts(self):
        """Test that new payment accounts are created for alliance members."""
        # Ensure clean state
        AlliancePaymentAccount.objects.filter(owner=self.alliance).delete()

        # Run update
        AlliancePaymentAccount.objects._update_payment_accounts(self.alliance)

        # Verify accounts created for both users
        payment_accounts = AlliancePaymentAccount.objects.filter(owner=self.alliance)
        self.assertEqual(payment_accounts.count(), 2)

        # Verify first user account
        account1 = payment_accounts.get(user=self.user)
        self.assertEqual(account1.status, AlliancePaymentAccount.Status.ACTIVE)
        self.assertEqual(
            account1.name, self.character_ownership.character.character_name
        )

        # Verify second user account
        account2 = payment_accounts.get(user=self.user2)
        self.assertEqual(account2.status, AlliancePaymentAccount.Status.ACTIVE)

    def test_update_payment_accounts_moves_to_new_alliance(self):
        """Test that payment account is moved when user changes alliance."""
        # Create second alliance
        user3, _ = create_user_from_evecharacter(1003)
        alliance2 = create_alliance_owner_from_user(
            user=user3,
            tax_amount=2000,
            tax_period=30,
        )

        # Create payment account for first alliance
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=alliance2,
            user=self.user,
            status=AlliancePaymentAccount.Status.ACTIVE,
            deposit=500,
        )

        # Update to new alliance
        AlliancePaymentAccount.objects._update_payment_accounts(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify moved to new alliance and deposit reset
        self.assertEqual(payment_account.owner, self.alliance)
        self.assertEqual(payment_account.deposit, 0)

    def test_update_payment_accounts_reactivate_inactive(self):
        """Test that inactive accounts are reactivated."""
        # Create inactive payment account
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.INACTIVE,
        )

        # Update accounts
        AlliancePaymentAccount.objects._update_payment_accounts(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify reactivation
        self.assertEqual(payment_account.status, AlliancePaymentAccount.Status.ACTIVE)

    def test_update_payment_accounts_keep_deactivated(self):
        """Test that deactivated accounts stay deactivated."""
        # Create deactivated payment account
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.DEACTIVATED,
        )

        # Update accounts
        AlliancePaymentAccount.objects._update_payment_accounts(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify stays deactivated
        self.assertEqual(
            payment_account.status, AlliancePaymentAccount.Status.DEACTIVATED
        )

    def test_check_payment_accounts_mark_missing(self):
        """Test that accounts are marked missing when user leaves alliance."""
        # Create second alliance
        user3, char3 = create_user_from_evecharacter(1003)
        alliance2 = create_alliance_owner_from_user(
            user=user3,
            tax_amount=2000,
            tax_period=30,
        )

        # Create payment account for first alliance
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.ACTIVE,
        )

        # Move user to second alliance by getting accounts from alliance2
        # This simulates the user being in a different alliance
        accounts = self.user.profile.__class__.objects.filter(
            main_character__isnull=False,
            main_character__alliance_id=alliance2.eve_alliance.alliance_id,
        )

        # Run check - since user is now in alliance2, their account in alliance1 should be marked missing
        # But we need to check with the user in a different alliance
        # Simulate by temporarily changing the user's alliance
        original_alliance_id = self.user.profile.main_character.alliance_id
        self.user.profile.main_character.alliance_id = (
            alliance2.eve_alliance.alliance_id
        )
        self.user.profile.main_character.save()

        # Get accounts with the updated alliance
        accounts = self.user.profile.__class__.objects.filter(
            main_character__isnull=False,
            main_character__alliance_id=alliance2.eve_alliance.alliance_id,
        )

        # Run check
        AlliancePaymentAccount.objects._check_payment_accounts(self.alliance, accounts)

        # Restore original alliance
        self.user.profile.main_character.alliance_id = original_alliance_id
        self.user.profile.main_character.save()

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify marked as missing
        self.assertEqual(payment_account.status, AlliancePaymentAccount.Status.MISSING)

    def test_check_payment_accounts_reactivate_missing(self):
        """Test that missing accounts are reactivated when user returns."""
        # Create missing payment account with data
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.MISSING,
            deposit=500,
            last_paid=timezone.now() - timezone.timedelta(days=10),
        )
        payment_account.notice = "User left alliance"
        payment_account.save()

        # Get accounts queryset (user is back in alliance)
        accounts = self.user.profile.__class__.objects.filter(
            main_character__isnull=False,
            main_character__alliance_id=self.alliance.eve_alliance.alliance_id,
        )

        # Run check
        AlliancePaymentAccount.objects._check_payment_accounts(self.alliance, accounts)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify reactivation
        self.assertEqual(payment_account.status, AlliancePaymentAccount.Status.ACTIVE)
        self.assertEqual(payment_account.deposit, 0)
        self.assertIsNone(payment_account.last_paid)
        self.assertIsNone(payment_account.notice)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAlliancePayDayManager(NoSocketsTestCase):
    """Test Alliance Pay Day Manager methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(1001)

        cls.alliance = create_alliance_owner_from_user(
            user=cls.user,
            tax_amount=1000,
            tax_period=30,
        )

    def test_pay_day_first_period_free(self):
        """Test that first period is free (last_paid is set but no deduction)."""
        # Create payment account without last_paid
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.ACTIVE,
            deposit=5000,
            last_paid=None,
        )

        # Run payday
        AlliancePaymentAccount.objects._pay_day(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify first period is free
        self.assertIsNotNone(payment_account.last_paid)
        self.assertEqual(payment_account.deposit, 5000)  # No deduction

    def test_pay_day_deduct_tax(self):
        """Test that tax is deducted after period expires."""
        # Create payment account with expired last_paid
        old_date = timezone.now() - timezone.timedelta(days=31)
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.ACTIVE,
            deposit=5000,
            last_paid=old_date,
        )

        # Run payday
        AlliancePaymentAccount.objects._pay_day(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify tax was deducted
        self.assertEqual(payment_account.deposit, 4000)  # 5000 - 1000
        self.assertNotEqual(payment_account.last_paid, old_date)

    def test_pay_day_skip_inactive(self):
        """Test that inactive accounts are skipped."""
        # Create inactive payment account
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.INACTIVE,
            deposit=5000,
            last_paid=timezone.now() - timezone.timedelta(days=31),
        )

        # Run payday
        AlliancePaymentAccount.objects._pay_day(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify no deduction for inactive account
        self.assertEqual(payment_account.deposit, 5000)

    def test_pay_day_not_expired(self):
        """Test that tax is not deducted if period hasn't expired."""
        # Create payment account with recent last_paid
        recent_date = timezone.now() - timezone.timedelta(days=15)
        payment_account = create_alliance_payment_system(
            name=self.character_ownership.character.character_name,
            owner=self.alliance,
            user=self.user,
            status=AlliancePaymentAccount.Status.ACTIVE,
            deposit=5000,
            last_paid=recent_date,
        )

        # Run payday
        AlliancePaymentAccount.objects._pay_day(self.alliance)

        # Refresh from database
        payment_account.refresh_from_db()

        # Verify no deduction
        self.assertEqual(payment_account.deposit, 5000)
        self.assertEqual(payment_account.last_paid, recent_date)

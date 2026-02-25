# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
# deprecated with v3
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.alliance import AlliancePayments
from taxsystem.models.corporation import CorporationPayments
from taxsystem.models.helpers.textchoices import (
    PaymentRequestStatus,
)
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
    create_payment,
    create_tax_account,
    create_wallet_journal_entry,
)

MODULE_PATH = "taxsystem.models.tax"


class TestPaymentsModel(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(cls.user)
        cls.audit2 = create_owner_from_user(cls.superuser)

        cls.eve_character_first_party = EveEntity.objects.get(id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

        cls.division = create_division(
            corporation=cls.audit,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

        cls.journal_entry = create_wallet_journal_entry(
            division=cls.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Test Journal Entry",
            ref_type="tax_payment",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            description="Test Description",
        )

        cls.tax_account = create_tax_account(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            deposit=0,
        )

        cls.payments = create_payment(
            name="Gneuten",
            amount=1000,
            request_status="needs_approval",
            account=cls.tax_account,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reviser="Requires Auditor",
            journal=cls.journal_entry,
            owner=cls.audit,
        )

    def test_str(self):
        expected_str = CorporationPayments.objects.get(account=self.tax_account)
        self.assertEqual(self.payments, expected_str)

    def test_is_automatic(self):
        """Test if the payment is automatic."""
        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertFalse(payments.is_automatic)

    def test_is_pending(self):
        """Test if the payment is pending."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertTrue(payments.is_pending)

    def test_is_approved(self):
        """Test if the payment is approved."""
        self.payments.request_status = PaymentRequestStatus.APPROVED
        self.payments.save()

        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertFalse(payments.is_pending)
        self.assertTrue(payments.is_approved)

    def test_is_rejected(self):
        """Test if the payment is rejected."""
        self.payments.request_status = PaymentRequestStatus.REJECTED
        self.payments.save()

        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertFalse(payments.is_pending)
        self.assertTrue(payments.is_rejected)

    def test_character_id(self):
        """Test if the character_id is correct."""
        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertEqual(
            payments.character_id, self.user_character.character.character_id
        )

    def test_division(self):
        """Test if the division is correct."""
        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertEqual(payments.division_name, "Main Division")

    def test_access_no_perms(self):
        """Test should return only own corporation if basic_access is set."""
        corporation = CorporationPayments.objects.get_visible(user=self.user2)
        self.assertNotIn(self.payments, corporation)

    def test_access_perms_own_corp(self):
        """Test should return only own corporation if manage_own_corp is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_corp", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationPayments.objects.get_visible(user=self.user)
        self.assertIn(self.payments, corporation)

    def test_access_perms_manage_corps(self):
        """Test should return all corporations if manage_corps is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_corps", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationPayments.objects.get_visible(user=self.user)
        self.assertIn(self.payments, corporation)

    def test_open_invoices_count(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = CorporationPayments.objects.get_owner_open_invoices(
            user=self.superuser, owner=self.audit
        )
        self.assertEqual(open_invoices, 1)

    def test_open_invoices_count_is_none(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = CorporationPayments.objects.get_owner_open_invoices(
            user=self.user, owner=self.audit
        )
        self.assertEqual(open_invoices, 0)

    def test_get_visible_invoices(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = CorporationPayments.objects.get_visible_open_invoices(
            user=self.manage_own_user
        )
        self.assertEqual(open_invoices, 1)

    def test_get_visible_invoices_is_none(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = CorporationPayments.objects.get_visible_open_invoices(
            user=self.user2
        )
        self.assertEqual(open_invoices, 0)


class TestAlliancePaymentsModel(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corp_audit = create_owner_from_user(user=cls.user)
        cls.audit = create_owner_from_user(user=cls.user, tax_type="alliance")
        cls.audit2 = create_owner_from_user(user=cls.superuser, tax_type="alliance")

        cls.eve_character_first_party = EveEntity.objects.get(id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

        cls.division = create_division(
            corporation=cls.corp_audit,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

        cls.journal_entry = create_wallet_journal_entry(
            division=cls.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Test Journal Entry",
            ref_type="tax_payment",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            description="Test Description",
        )

        cls.tax_account = create_tax_account(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            deposit=0,
        )

        cls.payments = create_payment(
            name="Gneuten",
            amount=1000,
            request_status="needs_approval",
            account=cls.tax_account,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reviser="Requires Auditor",
            journal=cls.journal_entry,
            owner=cls.audit,
        )

    def test_str(self):
        expected_str = AlliancePayments.objects.get(account=self.tax_account)
        self.assertEqual(self.payments, expected_str)

    def test_is_automatic(self):
        """Test if the payment is automatic."""
        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertFalse(payments.is_automatic)

    def test_is_pending(self):
        """Test if the payment is pending."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertTrue(payments.is_pending)

    def test_is_approved(self):
        """Test if the payment is approved."""
        self.payments.request_status = PaymentRequestStatus.APPROVED
        self.payments.save()

        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertFalse(payments.is_pending)
        self.assertTrue(payments.is_approved)

    def test_is_rejected(self):
        """Test if the payment is rejected."""
        self.payments.request_status = PaymentRequestStatus.REJECTED
        self.payments.save()

        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertFalse(payments.is_pending)
        self.assertTrue(payments.is_rejected)

    def test_character_id(self):
        """Test if the character_id is correct."""
        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertEqual(
            payments.character_id, self.user_character.character.character_id
        )

    def test_division(self):
        """Test if the division is correct."""
        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertEqual(payments.division_name, "Main Division")

    def test_access_no_perms(self):
        """Test should return only own corporation if basic_access is set."""
        corporation = AlliancePayments.objects.get_visible(user=self.user2)
        self.assertNotIn(self.payments, corporation)

    def test_access_perms_own_alliance(self):
        """Test should return only own alliance if manage_own_alliance is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_alliance", self.user
        )
        self.user.refresh_from_db()
        corporation = AlliancePayments.objects.get_visible(user=self.user)
        self.assertIn(self.payments, corporation)

    def test_access_perms_manage_alliances(self):
        """Test should return all alliances if manage_alliances is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_alliances", self.user
        )
        self.user.refresh_from_db()
        corporation = AlliancePayments.objects.get_visible(user=self.user)
        self.assertIn(self.payments, corporation)

    def test_open_invoices_count(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = AlliancePayments.objects.get_owner_open_invoices(
            user=self.superuser, owner=self.audit
        )
        self.assertEqual(open_invoices, 1)

    def test_open_invoices_count_is_none(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = AlliancePayments.objects.get_owner_open_invoices(
            user=self.user, owner=self.audit
        )
        self.assertEqual(open_invoices, 0)

    def test_get_visible_invoices(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = AlliancePayments.objects.get_visible_open_invoices(
            user=self.manage_own_user
        )
        self.assertEqual(open_invoices, 1)

    def test_get_visible_invoices_is_none(self):
        """Test the count of open invoices."""
        self.payments.request_status = PaymentRequestStatus.PENDING
        self.payments.save()

        open_invoices = AlliancePayments.objects.get_visible_open_invoices(
            user=self.user2
        )
        self.assertEqual(open_invoices, 0)

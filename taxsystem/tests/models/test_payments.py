# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA TaxSystem
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
        )

        cls.tax_account = create_tax_account(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
        )

        cls.payments = create_payment(
            name="Gneuten",
            entry_id=1,
            account=cls.tax_account,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            request_status="needs_approval",
            reviser="Requires Auditor",
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

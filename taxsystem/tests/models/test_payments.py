# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.tax import Payments
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment,
    create_payment_system,
)
from taxsystem.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.models.tax"


class TestPaymentsModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["taxsystem.basic_access"]
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002, permissions=["taxsystem.basic_access"]
        )
        cls.audit = create_owneraudit_from_user(cls.user)
        cls.audit2 = create_owneraudit_from_user(cls.user2)

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

        cls.payment_system = create_payment_system(
            name=cls.character_ownership.character.character_name,
            owner=cls.audit,
            user=cls.user,
        )

        cls.payments = create_payment(
            name="Gneuten",
            entry_id=1,
            account=cls.payment_system,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            request_status="needs_approval",
            reviser="Requires Auditor",
        )

    def test_str(self):
        expected_str = Payments.objects.get(account=self.payment_system)
        self.assertEqual(self.payments, expected_str)

    def test_is_automatic(self):
        """Test if the payment is automatic."""
        payments = Payments.objects.get(account=self.payment_system)
        self.assertFalse(payments.is_automatic)

    def test_is_pending(self):
        """Test if the payment is pending."""
        self.payments.request_status = Payments.RequestStatus.PENDING
        self.payments.save()

        payments = Payments.objects.get(account=self.payment_system)
        self.assertTrue(payments.is_pending)

    def test_is_approved(self):
        """Test if the payment is approved."""
        self.payments.request_status = Payments.RequestStatus.APPROVED
        self.payments.save()

        payments = Payments.objects.get(account=self.payment_system)
        self.assertFalse(payments.is_pending)
        self.assertTrue(payments.is_approved)

    def test_is_rejected(self):
        """Test if the payment is rejected."""
        self.payments.request_status = Payments.RequestStatus.REJECTED
        self.payments.save()

        payments = Payments.objects.get(account=self.payment_system)
        self.assertFalse(payments.is_pending)
        self.assertTrue(payments.is_rejected)

    def test_character_id(self):
        """Test if the character_id is correct."""
        payments = Payments.objects.get(account=self.payment_system)
        self.assertEqual(
            payments.character_id, self.character_ownership.character.character_id
        )

    def test_division(self):
        """Test if the division is correct."""
        payments = Payments.objects.get(account=self.payment_system)
        self.assertEqual(payments.division, "Main Division")

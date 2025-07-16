# Django
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.tax import PaymentSystem
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth

MODULE_PATH = "taxsystem.models.tax"


class TestOwnerAuditModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["taxsystem.basic_access"]
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002, permissions=["taxsystem.basic_access"]
        )
        cls.audit = create_owneraudit_from_user(cls.user)
        cls.audit2 = create_owneraudit_from_user(cls.user2)

        cls.payment_system = create_payment_system(
            name=cls.user.username,
            owner=cls.audit,
            user=cls.user,
        )

    def test_str(self):
        expected_str = PaymentSystem.objects.get(owner=self.audit)
        self.assertEqual(self.payment_system, expected_str)

    def test_is_active(self):
        """Test if the payment system is active."""
        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertTrue(payment_system.is_active)

    def test_is_inactive(self):
        """Test if the payment system is inactive."""
        self.payment_system.status = PaymentSystem.Status.INACTIVE
        self.payment_system.save()

        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertFalse(payment_system.is_active)

    def test_is_deactivated(self):
        """Test if the payment system is deactivated."""
        self.payment_system.status = PaymentSystem.Status.DEACTIVATED
        self.payment_system.save()
        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertFalse(payment_system.is_active)

    def test_is_missing(self):
        """Test if the payment system is missing."""
        self.payment_system.status = PaymentSystem.Status.MISSING
        self.payment_system.save()

        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertFalse(payment_system.is_active)

    def test_has_paid(self):
        """Test if the payment system has paid."""
        self.payment_system.deposit = 1000
        self.payment_system.save()

        self.payment_system.date = timezone.now()

        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertTrue(payment_system.has_paid)

    def test_has_paid_icon(self):
        """Test the icon representation of has_paid."""
        self.payment_system.deposit = 1000
        self.payment_system.save()

        self.payment_system.date = timezone.now()

        payment_system = PaymentSystem.objects.get(owner=self.audit)

        self.assertIn(
            "fas fa-check",
            payment_system.has_paid_icon()["display"],
        )
        self.assertIn(
            "badge",
            payment_system.has_paid_icon(badge=True, text=True)["display"],
        )
        self.assertIn(
            "Paid",
            payment_system.has_paid_icon(badge=True, text=True)["display"],
        )

    def test_status_html(self):
        """Test the HTML representation of the payment system status."""
        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertIn(
            "bg-success",
            payment_system.Status(payment_system.status).html(),
        )

        self.assertIn(
            "Active",
            payment_system.Status(payment_system.status).html(text=True),
        )

    def test_status_color(self):
        """Test the color representation of the payment system status."""
        payment_system = PaymentSystem.objects.get(owner=self.audit)
        self.assertEqual(
            payment_system.Status(payment_system.status).color(), "success"
        )

    def test_status_icon(self):
        """Test the icon representation of the payment system status."""
        payment_system = PaymentSystem.objects.get(owner=self.audit)

        self.assertEqual(
            payment_system.Status(payment_system.status).icons(),
            "<i class='fas fa-check'></i>",
        )

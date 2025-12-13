# Django
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.corporation import CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import AccountStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment_system,
)

MODULE_PATH = "taxsystem.models.tax"


class TestPaymentSystemModel(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_corporation_owner_from_user(cls.user)
        cls.audit2 = create_corporation_owner_from_user(cls.superuser)

        cls.payment_system = create_payment_system(
            name=cls.user.username,
            owner=cls.audit,
            user=cls.user,
        )

    def test_str(self):
        expected_str = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertEqual(self.payment_system, expected_str)

    def test_is_active(self):
        """Test if the payment system is active."""
        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertTrue(payment_system.is_active)

    def test_is_inactive(self):
        """Test if the payment system is inactive."""
        self.payment_system.status = AccountStatus.INACTIVE
        self.payment_system.save()

        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertFalse(payment_system.is_active)

    def test_is_deactivated(self):
        """Test if the payment system is deactivated."""
        self.payment_system.status = AccountStatus.DEACTIVATED
        self.payment_system.save()
        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertFalse(payment_system.is_active)

    def test_is_missing(self):
        """Test if the payment system is missing."""
        self.payment_system.status = AccountStatus.MISSING
        self.payment_system.save()

        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertFalse(payment_system.is_active)

    def test_has_paid(self):
        """Test if the payment system has paid."""
        self.payment_system.deposit = 1000
        self.payment_system.save()

        self.payment_system.date = timezone.now()

        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertTrue(payment_system.has_paid)

    def test_has_paid_icon(self):
        """Test the icon representation of has_paid."""
        self.payment_system.deposit = 1000
        self.payment_system.save()

        self.payment_system.date = timezone.now()

        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)

        self.assertIn(
            "fas fa-check",
            payment_system.has_paid_icon(),
        )
        self.assertIn(
            "badge",
            payment_system.has_paid_icon(badge=True, text=True),
        )
        self.assertIn(
            "Paid",
            payment_system.has_paid_icon(badge=True, text=True),
        )
        self.assertNotIn(
            "badge",
            payment_system.has_paid_icon(badge=False, text=True),
        )

    def test_status_html(self):
        """Test the HTML representation of the payment system status."""
        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertIn(
            "bg-success",
            AccountStatus(payment_system.status).html(),
        )

        self.assertIn(
            "Active",
            AccountStatus(payment_system.status).html(text=True),
        )

    def test_status_color(self):
        """Test the color representation of the payment system status."""
        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertEqual(AccountStatus(payment_system.status).color(), "success")

    def test_status_icon(self):
        """Test the icon representation of the payment system status."""
        payment_system = CorporationPaymentAccount.objects.get(owner=self.audit)

        self.assertEqual(
            AccountStatus(payment_system.status).icon(),
            "<i class='fas fa-check'></i>",
        )

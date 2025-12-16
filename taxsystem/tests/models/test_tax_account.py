# Django
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.corporation import CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import AccountStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_owner_from_user,
    create_tax_account,
)

MODULE_PATH = "taxsystem.models.tax"


class TestPaymentSystemModel(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(cls.user)
        cls.audit2 = create_owner_from_user(cls.superuser)

        cls.tax_account = create_tax_account(
            name=cls.user.username,
            owner=cls.audit,
            user=cls.user,
        )

    def test_str(self):
        expected_str = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertEqual(self.tax_account, expected_str)

    def test_is_active(self):
        """Test if the tax account is active."""
        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertTrue(tax_account.is_active)

    def test_is_inactive(self):
        """Test if the tax account is inactive."""
        self.tax_account.status = AccountStatus.INACTIVE
        self.tax_account.save()

        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertFalse(tax_account.is_active)

    def test_is_deactivated(self):
        """Test if the tax account is deactivated."""
        self.tax_account.status = AccountStatus.DEACTIVATED
        self.tax_account.save()
        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertFalse(tax_account.is_active)

    def test_is_missing(self):
        """Test if the tax account is missing."""
        self.tax_account.status = AccountStatus.MISSING
        self.tax_account.save()

        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertFalse(tax_account.is_active)

    def test_has_paid(self):
        """Test if the tax account has paid."""
        self.tax_account.deposit = 1000
        self.tax_account.save()

        self.tax_account.date = timezone.now()

        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertTrue(tax_account.has_paid)

    def test_has_paid_icon(self):
        """Test the icon representation of has_paid."""
        self.tax_account.deposit = 1000
        self.tax_account.save()

        self.tax_account.date = timezone.now()

        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)

        self.assertIn(
            "fas fa-check",
            tax_account.has_paid_icon(),
        )
        self.assertIn(
            "badge",
            tax_account.has_paid_icon(badge=True, text=True),
        )
        self.assertIn(
            "Paid",
            tax_account.has_paid_icon(badge=True, text=True),
        )
        self.assertNotIn(
            "badge",
            tax_account.has_paid_icon(badge=False, text=True),
        )

    def test_status_html(self):
        """Test the HTML representation of the tax account status."""
        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertIn(
            "bg-success",
            AccountStatus(tax_account.status).html(),
        )

        self.assertIn(
            "Active",
            AccountStatus(tax_account.status).html(text=True),
        )

    def test_status_color(self):
        """Test the color representation of the tax account status."""
        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)
        self.assertEqual(AccountStatus(tax_account.status).color(), "success")

    def test_status_icon(self):
        """Test the icon representation of the tax account status."""
        tax_account = CorporationPaymentAccount.objects.get(owner=self.audit)

        self.assertEqual(
            AccountStatus(tax_account.status).icon(),
            "<i class='fas fa-check'></i>",
        )

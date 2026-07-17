# Django
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils

# AA TaxSystem
from taxsystem.models.alliance import AlliancePayments
from taxsystem.models.corporation import CorporationPayments
from taxsystem.models.helpers.textchoices import (
    PaymentRequestStatus,
)
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    AlliancePaymentsFactory,
    AllianceTaxAccountFactory,
    CorporationJournalFactory,
    CorporationOwnerFactory,
    CorporationPaymentsFactory,
    CorporationTaxAccountFactory,
    DivisionFactory,
    EveCharacterFactory,
    EveEntityFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.models.tax"


class TestPaymentsModel(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.audit2 = CorporationOwnerFactory(user=cls.superuser)
        cls.user2 = UserMainFactory()

        # Corporation Owner
        corp = EveCorporationInfo.objects.get(
            corporation_id=cls.user_character.corporation_id
        )
        cls.manage_own_corporation = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corp),
            permissions__=["taxsystem.manage_own_corp"],
        )

        cls.journal_entry = CorporationJournalFactory()
        cls.tax_account = CorporationTaxAccountFactory(
            name=cls.user_character.character_name,
            owner=cls.audit,
            user=cls.user,
        )
        cls.payments = CorporationPaymentsFactory(
            name="Gneuten",
            amount=1000,
            request_status="needs_approval",
            account=cls.tax_account,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0),
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
        self.assertEqual(payments.character_id, self.user_character.character_id)

    def test_division(self):
        """Test if the division is correct."""
        payments = CorporationPayments.objects.get(account=self.tax_account)
        self.assertEqual(payments.division_name, self.journal_entry.division.name)

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
            user=self.manage_own_corporation
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
        cls.corp_audit = CorporationOwnerFactory(user=cls.user)
        cls.audit = AllianceOwnerFactory(user=cls.user)
        cls.audit2 = AllianceOwnerFactory(user=cls.superuser)
        cls.user2 = UserMainFactory()

        # Alliance Owner
        corp = EveCorporationInfo.objects.get(
            corporation_id=cls.user_character.corporation_id
        )
        cls.manage_own_alliance = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corp),
            permissions__=["taxsystem.manage_own_alliance"],
        )

        cls.journal_entry = CorporationJournalFactory()
        cls.tax_account = AllianceTaxAccountFactory(
            name=cls.user_character.character_name,
            owner=cls.audit,
            user=cls.user,
        )
        cls.payments = AlliancePaymentsFactory(
            name="Gneuten",
            amount=1000,
            request_status="needs_approval",
            owner=cls.audit,
            account=cls.tax_account,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0),
            reviser="Requires Auditor",
            journal=cls.journal_entry,
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
        self.assertEqual(payments.character_id, self.user_character.character_id)

    def test_division(self):
        """Test if the division is correct."""
        payments = AlliancePayments.objects.get(account=self.tax_account)
        self.assertEqual(payments.division_name, self.journal_entry.division.name)

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
            user=self.manage_own_alliance
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

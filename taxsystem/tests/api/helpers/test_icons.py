# Django
from django.urls import reverse
from django.utils import timezone

# Alliance Auth (External Libs)
# deprecated with v3
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.api.helpers.icons import get_taxsystem_payments_action_icons
from taxsystem.models.helpers.textchoices import PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
    create_payment,
    create_tax_account,
    create_wallet_journal_entry,
)

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestPaymentsApiEndpoints(TaxSystemTestCase):
    """Test Payments API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(user=cls.user)

        cls.division = create_division(
            corporation=cls.audit, balance=0, division_id=1, name="Main Division"
        )

        cls.first_party = EveEntity.objects.get(id=1002)
        cls.second_party = EveEntity.objects.get(id=1001)

        cls.tax_account = create_tax_account(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status="active",
            deposit=0,
        )

    def test_get_taxsystem_payments_action_icons(self):
        """
        Test get_taxsystem_payments_action_icons function.

        Create a payment with different actions and verify the returned icons.

        # Test Szenarios:
            - Display approve and reject icons for pending payment.
            - Display Undo icon for approved payment.
            - Display Delete icon for non ESI payment.
        """
        # Test Data
        request = self.factory.get(reverse("taxsystem:index"))
        request.user = self.manage_user

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Pending Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        payment2 = create_payment(
            name="Second Payment",
            account=self.tax_account,
            owner=self.audit,
            journal=None,
            amount=500,
            date=timezone.datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment 2",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Test Action
        icons = get_taxsystem_payments_action_icons(request=request, payment=payment)

        # Exptected Results
        approve_icon = '<i class="fa-solid fa-check"></i>'
        reject_icon = '<i class="fa-solid fa-xmark"></i>'
        undo_icon = '<i class="fa-solid fa-undo"></i>'
        delete_icon = '<i class="fa-solid fa-trash"></i>'

        self.assertIn(approve_icon, icons)
        self.assertIn(reject_icon, icons)
        self.assertNotIn(undo_icon, icons)
        self.assertNotIn(delete_icon, icons)

        # Test Undo Icon for Approved Payment
        payment.request_status = PaymentRequestStatus.APPROVED
        payment.save()

        # Test Action
        icons = get_taxsystem_payments_action_icons(request=request, payment=payment)

        # Exptected Result
        self.assertIn(undo_icon, icons)

        # Test Action for Non ESI Payment
        icons = get_taxsystem_payments_action_icons(request=request, payment=payment2)

        # Exptected Result
        self.assertIn(delete_icon, icons)

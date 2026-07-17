# Django
from django.urls import reverse
from django.utils import timezone

# AA TaxSystem
from taxsystem.api.helpers.icons import get_taxsystem_payments_action_icons
from taxsystem.models.helpers.textchoices import PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import CorporationPaymentsFactory

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestPaymentsApiEndpoints(TaxSystemTestCase):
    """Test Payments API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        request.user = self.superuser  # Superuser for testing all actions

        # Pending Payment
        payment = CorporationPaymentsFactory(
            date=timezone.datetime(2025, 1, 1, 12, 0, 0),
            request_status=PaymentRequestStatus.PENDING,
        )

        payment2 = CorporationPaymentsFactory(
            journal=None,
            date=timezone.datetime(2025, 1, 2, 12, 0, 0),
            request_status=PaymentRequestStatus.PENDING,
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

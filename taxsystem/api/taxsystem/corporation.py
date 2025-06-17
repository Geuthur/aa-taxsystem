# Standard Library
import logging

# Third Party
from ninja import NinjaAPI

# Django
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.api.helpers import get_corporation, get_manage_corporation
from taxsystem.api.taxsystem.helpers.own_payments import _own_payments_actions
from taxsystem.api.taxsystem.helpers.payments import _payments_actions
from taxsystem.helpers import lazy
from taxsystem.models.tax import Payments, PaymentSystem

logger = logging.getLogger(__name__)


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/payments/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_payments(request, corporation_id: int):
            owner, perms = get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, "Corporation Not Found"

            payments = Payments.objects.filter(account__owner=owner)

            payments_dict = {}

            for payment in payments:
                try:
                    character_portrait = lazy.get_character_portrait_url(
                        payment.character_id, size=32, as_html=True
                    )
                except ValueError:
                    character_portrait = ""

                actions = _payments_actions(corporation_id, payment, perms, request)

                payments_dict[payment.pk] = {
                    "payment_id": payment.pk,
                    "date": payment.formatted_payment_date,
                    "character_portrait": character_portrait,
                    "character_name": payment.account.name,
                    "amount": payment.amount,
                    "request_status": payment.get_request_status_display(),
                    "division": payment.division,
                    "reason": payment.reason,
                    "actions": actions,
                }

            output = []
            output.append({"corporation": payments_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/own-payments/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_own_payments(request, corporation_id: int):
            corp = get_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            account = PaymentSystem.objects.get(owner=corp, user=request.user)

            payments = Payments.objects.filter(account__owner=corp, account=account)

            own_payments_dict = {}

            for payment in payments:
                actions = _own_payments_actions(corporation_id, payment, request)

                own_payments_dict[payment.pk] = {
                    "payment_id": payment.pk,
                    "date": payment.formatted_payment_date,
                    "character_name": payment.account.name,
                    "amount": payment.amount,
                    "request_status": payment.get_request_status_display(),
                    "division": payment.division,
                    "reason": payment.reason,
                    "actions": actions,
                }

            output = []
            output.append({"corporation": own_payments_dict})

            return output

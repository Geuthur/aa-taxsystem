# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.common import (
    create_own_payment_response_data,
    create_payment_response_data,
)
from taxsystem.api.schema import CharacterSchema, PaymentSchema
from taxsystem.models.corporation import CorporationPaymentAccount, CorporationPayments

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentCorporationSchema(PaymentSchema):
    character: CharacterSchema


class PaymentsResponse(Schema):
    owner: list[PaymentCorporationSchema]


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/payments/",
            response={200: PaymentsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_payments(request, corporation_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": "Corporation Not Found"}

            if perms is False:
                return 403, {"error": "Permission Denied"}

            # Get Payments
            payments = (
                CorporationPayments.objects.filter(
                    account__owner=owner,
                    owner_id=owner.eve_corporation.corporation_id,
                )
                .select_related("account")
                .order_by("-date")
            )

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                payment_data = create_payment_response_data(payment, request, perms)
                response_payment = PaymentCorporationSchema(**payment_data)
                response_payments_list.append(response_payment)
            return PaymentsResponse(owner=response_payments_list)

        @api.get(
            "corporation/{corporation_id}/view/own-payments/",
            response={200: PaymentsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_own_payments(request, corporation_id: int):
            owner = core.get_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": "Corporation Not Found"}

            account = get_object_or_404(
                CorporationPaymentAccount, owner=owner, user=request.user
            )

            # Get Payments
            payments = (
                CorporationPayments.objects.filter(
                    account__owner=owner,
                    account=account,
                    owner_id=owner.eve_corporation.corporation_id,
                )
                .select_related("account")
                .order_by("-date")
            )

            if len(payments) == 0:
                return 403, {"error": _("No Payments Found")}

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                payment_data = create_own_payment_response_data(payment)
                response_payment = PaymentCorporationSchema(**payment_data)
                response_payments_list.append(response_payment)
            return PaymentsResponse(owner=response_payments_list)

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
    build_own_payments_response_list,
    build_payments_response_list,
    get_optimized_own_payments_queryset,
    get_optimized_payments_queryset,
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
            payments = get_optimized_payments_queryset(
                CorporationPayments, owner, owner.eve_corporation.corporation_id
            )

            response_payments_list = build_payments_response_list(
                payments, request, perms, PaymentCorporationSchema
            )
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
            payments = get_optimized_own_payments_queryset(
                CorporationPayments,
                owner,
                account,
                owner.eve_corporation.corporation_id,
            )

            if len(payments) == 0:
                return 403, {"error": _("No Payments Found")}

            response_payments_list = build_own_payments_response_list(
                payments, PaymentCorporationSchema
            )
            return PaymentsResponse(owner=response_payments_list)

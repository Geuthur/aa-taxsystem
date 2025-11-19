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
from taxsystem.api.helpers.manage import manage_payments
from taxsystem.api.schema import CharacterSchema, PaymentSchema, RequestStatusSchema
from taxsystem.helpers import lazy
from taxsystem.models.corporation import CorporationPaymentAccount, CorporationPayments

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentCorporationSchema(PaymentSchema):
    character: CharacterSchema


class PaymentsResponse(Schema):
    corporation: list[PaymentCorporationSchema]


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
                    corporation_id=owner.eve_corporation.corporation_id,
                )
                .select_related("account")
                .order_by("-date")
            )

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                character_portrait = lazy.get_character_portrait_url(
                    payment.character_id, size=32, as_html=True
                )

                # Create the action buttons
                actions_html = manage_payments(
                    request=request, perms=perms, payment=payment
                )

                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=payment.RequestStatus(payment.request_status).color(),
                )

                response_payment = PaymentCorporationSchema(
                    payment_id=payment.pk,
                    character=CharacterSchema(
                        character_id=payment.character_id,
                        character_name=payment.account.name,
                        character_portrait=character_portrait,
                    ),
                    amount=payment.amount,
                    date=payment.formatted_payment_date,
                    request_status=response_request_status,
                    division_name=payment.division_name,
                    reviser=payment.reviser,
                    reason=payment.reason,
                    actions=actions_html,
                )

                response_payments_list.append(response_payment)
            return PaymentsResponse(corporation=response_payments_list)

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
                    corporation_id=owner.eve_corporation.corporation_id,
                )
                .select_related("account")
                .order_by("-date")
            )

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                # Create the character portrait
                character_portrait = lazy.get_character_portrait_url(
                    payment.character_id, size=32, as_html=True
                )

                # Create the actions
                actions = core.generate_info_button(payment)

                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=payment.RequestStatus(payment.request_status).color(),
                )

                # pylint: disable=duplicate-code
                # same code will be used in get_member_payments
                response_payment = PaymentCorporationSchema(
                    payment_id=payment.pk,
                    character=CharacterSchema(
                        character_id=payment.character_id,
                        character_name=payment.account.name,
                        character_portrait=character_portrait,
                    ),
                    amount=payment.amount,
                    date=payment.formatted_payment_date,
                    request_status=response_request_status,
                    division_name=payment.division_name,
                    reviser=payment.reviser,
                    reason=payment.reason,
                    actions=actions,
                )

                response_payments_list.append(response_payment)
            return PaymentsResponse(corporation=response_payments_list)

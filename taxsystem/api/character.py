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
from taxsystem.api.helpers.icons import get_taxsystem_manage_payments_action_icons
from taxsystem.api.schema import (
    CharacterSchema,
    LogHistorySchema,
    OwnerSchema,
    PaymentSchema,
    RequestStatusSchema,
)
from taxsystem.helpers.lazy import get_character_portrait_url
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentAccountSchema(Schema):
    account_id: int
    account_name: str
    account_status: str
    character: CharacterSchema
    payment_pool: int


class PaymentsDetailsResponse(Schema):
    owner: OwnerSchema
    account: PaymentAccountSchema
    payment: PaymentSchema
    payment_histories: list[LogHistorySchema]


class CharacterApiEndpoints:
    tags = ["Character Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/payment/{payment_pk}/view/details/",
            response={200: PaymentsDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_payment_details(request, owner_id: int, payment_pk: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            payment = get_object_or_404(owner.payment_model, pk=payment_pk)
            perms = perms or core.get_character_permissions(
                request, payment.character_id
            )

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            response_payment_histories: list[LogHistorySchema] = []
            payments_history = owner.payment_history_model.objects.filter(
                payment=payment,
            ).order_by("-date")

            # Create a list for the payment histories
            for log in payments_history:
                response_log = LogHistorySchema(
                    log_id=log.pk,
                    reviser=log.user.username if log.user else _("System"),
                    date=log.date.strftime("%Y-%m-%d %H:%M:%S"),
                    action=log.get_action_display(),
                    comment=log.comment,
                    status=log.get_new_status_display(),
                )
                response_payment_histories.append(response_log)

            # Create the payment account
            response_account = PaymentAccountSchema(
                account_id=payment.account.pk,
                account_name=payment.account.name,
                account_status=AccountStatus(payment.account.status).html(),
                character=CharacterSchema(
                    character_id=payment.character_id,
                    character_name=payment.account.name,
                    character_portrait=get_character_portrait_url(
                        payment.character_id, size=32, as_html=True
                    ),
                    corporation_id=payment.account.owner.pk,
                    corporation_name=payment.account.owner.name,
                ),
                payment_pool=payment.account.deposit,
            )

            response_request_status = RequestStatusSchema(
                status=payment.get_request_status_display(),
                html=PaymentRequestStatus(payment.request_status).alert(),
            )

            # Create the payment
            response_payment = PaymentSchema(
                payment_id=payment.pk,
                amount=payment.amount,
                date=payment.formatted_payment_date,
                request_status=response_request_status,
                division_name=payment.division_name,
                reason=payment.reason,
                reviser=payment.reviser,
            )

            response_owner = OwnerSchema(
                owner_id=owner.eve_id,
                owner_name=owner.name,
            )

            payment_details_response = PaymentsDetailsResponse(
                owner=response_owner,
                account=response_account,
                payment=response_payment,
                payment_histories=response_payment_histories,
            )

            return payment_details_response

        @api.get(
            "owner/{owner_id}/character/{character_id}/view/payments/",
            response={200: list[PaymentSchema], 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_member_payments(request, owner_id: int, character_id: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Filter the last 10000 payments by character
            payments = owner.payment_model.objects.filter(
                account__owner=owner,
                account__user__profile__main_character__character_id=character_id,
                owner_id=owner.eve_id,
            ).order_by("-date")[:10000]

            if not payments:
                return 404, {"error": _("No Payments Found")}

            response_payments_list: list[PaymentSchema] = []
            for payment in payments:
                # Create the actions
                actions_html = get_taxsystem_manage_payments_action_icons(
                    request=request, payment=payment
                )

                # pylint: disable=duplicate-code
                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=PaymentRequestStatus(payment.request_status).color(),
                )

                response_payment = PaymentSchema(
                    payment_id=payment.pk,
                    amount=payment.amount,
                    date=payment.formatted_payment_date,
                    request_status=response_request_status,
                    division_name=payment.division_name,
                    reason=payment.reason,
                    actions=actions_html,
                    reviser=payment.reviser,
                )
                response_payments_list.append(response_payment)

            return response_payments_list

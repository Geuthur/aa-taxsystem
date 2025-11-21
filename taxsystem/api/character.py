# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.manage import manage_payments
from taxsystem.api.schema import (
    CharacterSchema,
    LogHistorySchema,
    PaymentSchema,
    RequestStatusSchema,
)
from taxsystem.helpers.lazy import get_character_portrait_url
from taxsystem.models.corporation import (
    CorporationPaymentAccount,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentAccountSchema(Schema):
    account_id: int
    account_name: str
    character: CharacterSchema
    payment_pool: int
    payment_status: str


class PaymentDetailsSchema(Schema):
    account: PaymentAccountSchema | None
    payment: PaymentSchema | None
    payment_histories: list[LogHistorySchema] | None


class PaymentsDetailsResponse(Schema):
    title: str | None = None
    entity_pk: int
    entity_type: str
    payment_details: PaymentDetailsSchema | list[PaymentDetailsSchema]


class PaymentsCharacterResponse(PaymentsDetailsResponse):
    payment_details: list[PaymentSchema]
    character: CharacterSchema


class CharacterApiEndpoints:
    tags = ["Character Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/character/{character_id}/payment/{pk}/view/details/",
            response={200: PaymentsDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_payment_details(request, owner_id: int, character_id: int, pk: int):
            owner, perms = core.get_manage_owner(request, owner_id)
            perms = perms or core.get_character_permissions(request, character_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner Not Found")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied")}

            payment = get_object_or_404(owner.payments_class, pk=pk)
            account = get_object_or_404(
                owner.payments_account_class,
                user=payment.account.user,
                owner=owner,
            )

            response_payment_histories: list[LogHistorySchema] = []
            payments_history = owner.payments_history_class.objects.filter(
                payment=payment,
            ).order_by("-date")

            # Create the payment account
            response_account = PaymentAccountSchema(
                account_id=account.pk,
                account_name=account.name,
                character=CharacterSchema(
                    character_id=payment.character_id,
                    character_name=payment.account.name,
                    character_portrait=get_character_portrait_url(
                        payment.character_id, size=32, as_html=True
                    ),
                    corporation_id=account.owner.pk,
                    corporation_name=account.owner.name,
                ),
                payment_pool=account.deposit,
                payment_status=CorporationPaymentAccount.Status(account.status).html(),
            )

            # Create a list for the payment histories
            for log in payments_history:
                response_log: LogHistorySchema = LogHistorySchema(
                    log_id=log.pk,
                    reviser=log.user.username if log.user else _("System"),
                    date=log.date.strftime("%Y-%m-%d %H:%M:%S"),
                    action=log.get_action_display(),
                    comment=log.get_comment_display(),
                    status=log.get_new_status_display(),
                )
                response_payment_histories.append(response_log)

            response_request_status = RequestStatusSchema(
                status=payment.get_request_status_display(),
                color=payment.RequestStatus(payment.request_status).color(),
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

            # Create the payment details
            payment_details: PaymentDetailsSchema = PaymentDetailsSchema(
                account=response_account,
                payment=response_payment,
                payment_histories=response_payment_histories,
            )

            # Create the response
            paymentdetails_response = PaymentsDetailsResponse(
                entity_pk=owner_id,
                entity_type="character",
                payment_details=payment_details,
            )

            return render(
                request=request,
                template_name="taxsystem/modals/view_payment_details.html",
                context=paymentdetails_response.dict(),
            )

        @api.get(
            "owner/{owner_id}/character/{character_id}/view/payments/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_member_payments(request, owner_id: int, character_id: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied")}

            # Filter the last 10000 payments by character
            payments = owner.payments_class.objects.filter(
                account__owner=owner,
                account__user__profile__main_character__character_id=character_id,
                owner_id=owner.eve_id,
            ).order_by("-date")[:10000]

            if not payments:
                return 404, {"error": _("No Payments Found")}

            response_payments_list: list[PaymentSchema] = []
            for payment in payments:
                try:
                    character_id = (
                        payment.account.user.profile.main_character.character_id
                    )
                    portrait = get_character_portrait_url(
                        character_id, size=32, as_html=True
                    )
                except AttributeError:
                    portrait = ""

                # Create the actions
                actions_html = manage_payments(
                    request=request, perms=perms, payment=payment
                )

                # pylint: disable=duplicate-code
                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=payment.RequestStatus(payment.request_status).color(),
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

            character_payments_response = PaymentsCharacterResponse(
                entity_pk=character_id,
                entity_type="character",
                payment_details=response_payments_list,
                character=CharacterSchema(
                    character_id=character_id,
                    character_name=payments[0].account.name,
                    character_portrait=portrait,
                ),
            )

            return render(
                request,
                "taxsystem/modals/view_character_payments.html",
                context=character_payments_response.dict(),
            )

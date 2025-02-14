from ninja import NinjaAPI

from django.contrib.humanize.templatetags.humanize import intcomma
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from taxsystem.api.helpers import get_corporation
from taxsystem.api.taxsystem.helpers.paymentsystem import _get_has_paid_icon
from taxsystem.helpers import lazy
from taxsystem.hooks import get_extension_logger
from taxsystem.models.logs import Logs
from taxsystem.models.tax import Payments, PaymentSystem

logger = get_extension_logger(__name__)


class CharacterApiEndpoints:
    tags = ["Character Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/character/{character_id}/payment/{pk}/view/details/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_payment_details(
            request, corporation_id: int, character_id: int, pk: int
        ):
            __, corp = get_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            try:
                payment = Payments.objects.get(
                    pk=pk,
                    account__corporation=corp,
                    account__user__main_character__character_id=character_id,
                )
                account = PaymentSystem.objects.get(
                    user=payment.account.user,
                    corporation=corp,
                )
            except Payments.DoesNotExist:
                return 404, "Payment Not Found"

            # Create a dict for the character
            payments_char_dict = {
                "title": "Payments for",
                "character_id": character_id,
                "character_portrait": lazy.get_character_portrait_url(
                    character_id, size=32, as_html=True
                ),
                "character_name": payment.account.name,
                "payment_system": {},
                "payments": {},
            }

            # Create a dict for the payment system
            if account.is_active:
                status = lazy.generate_icon(
                    color="success", icon="fas fa-check", size=24
                )
            elif account.is_deactivated:
                status = lazy.generate_icon(
                    color="danger", icon="fas fa-times", size=24
                )
            else:
                status = lazy.generate_icon(
                    color="warning", icon="fas fa-user-slash", size=24
                )

            account_dict = {
                "account_id": account.pk,
                "corporation": account.corporation.name,
                "name": account.name,
                "payment_pool": f"{intcomma(account.deposit)} ISK",
                "payment_status": _get_has_paid_icon(account),
                "payment_status2": account.get_payment_status(),
                "status": status,
            }

            payment_history_dict = {}

            payments_history = Logs.objects.filter(
                payment=payment,
            ).order_by("-date")

            for log in payments_history:
                log_dict = {
                    "log_id": log.pk,
                    "reviser": log.user,
                    "date": log.date,
                    "action": log.get_action_display(),
                    "comment": log.comment,
                    "status": log.get_new_status_display(),
                }
                payment_history_dict[log.pk] = log_dict

            # Create a dict for each payment
            payments_dict = {
                "payment_id": payment.pk,
                "date": payment.date,
                "amount": f"{intcomma(payment.amount)} ISK",
                "payment_date": payment.formatted_payment_date(),
                "status": payment.get_status_display(),
                "approved": payment.get_request_status_display(),
                "system": payment.reviser,
                "reason": payment.reason,
            }

            # Add payments to the character dict
            payments_char_dict["payment"] = payments_dict
            payments_char_dict["payment_system"] = account_dict
            payments_char_dict["payment_history"] = payment_history_dict

            context = {
                "entity_pk": corporation_id,
                "entity_type": "character",
                "character": payments_char_dict,
            }

            return render(
                request,
                "taxsystem/modals/view_payment_details.html",
                context,
            )

# Standard Library
import logging

# Third Party
from ninja import NinjaAPI

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.api.helpers import get_character_permissions, get_manage_corporation
from taxsystem.helpers import lazy
from taxsystem.models.logs import PaymentHistory
from taxsystem.models.tax import Payments, PaymentSystem

logger = logging.getLogger(__name__)


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
            owner, perms = get_manage_corporation(request, corporation_id)
            perms = perms or get_character_permissions(request, character_id)

            if owner is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            try:
                payment = Payments.objects.get(
                    pk=pk,
                    account__owner=owner,
                )
                account = PaymentSystem.objects.get(
                    user=payment.account.user,
                    owner=owner,
                )
            except Payments.DoesNotExist:
                return 404, "Payment Not Found"

            # Create a dict for the character
            paymentdetails = {
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
                    color="success", icon="fas fa-check", size=24, title=_("Active")
                )
            elif account.is_deactivated:
                status = lazy.generate_icon(
                    color="danger",
                    icon="fas fa-user-clock",
                    size=24,
                    title=_("Deactivated"),
                )
            else:
                status = lazy.generate_icon(
                    color="warning",
                    icon="fas fa-user-slash",
                    size=24,
                    title=_("Inactive"),
                )

            account_dict = {
                "account_id": account.pk,
                "corporation": account.owner.name,
                "name": account.name,
                "payment_pool": f"{intcomma(account.deposit)} ISK",
                "payment_status": PaymentSystem.Status(account.status).html(),
                "status": status,
            }

            payment_history_dict = {}

            payments_history = PaymentHistory.objects.filter(
                payment=payment,
            ).order_by("-date")

            for log in payments_history:
                log_dict = {
                    "log_id": log.pk,
                    "reviser": log.user,
                    "date": log.date,
                    "action": log.get_action_display(),
                    "comment": log.get_comment_display(),
                    "status": log.get_new_status_display(),
                }
                payment_history_dict[log.pk] = log_dict

            # Create Status Display
            payment_status = "<div class='text-center alert"
            if payment.is_pending:
                payment_status += " alert-warning'>"
            elif payment.is_needs_approval:
                payment_status += " alert-info'>"
            elif payment.is_approved:
                payment_status += " alert-success'>"
            elif payment.is_rejected:
                payment_status += " alert-danger'>"
            payment_status += f"{payment.get_request_status_display()}</div>"

            # Create a dict for each payment
            payment_dict = {
                "payment_id": payment.pk,
                "amount": f"{intcomma(payment.amount)} ISK",
                "date": payment.formatted_payment_date,
                "status": format_html(payment_status),
                "reviser": payment.reviser,
                "division": payment.division,
                "reason": payment.reason,
            }

            # Add payments to the character dict
            paymentdetails["payment"] = payment_dict
            paymentdetails["payment_system"] = account_dict
            paymentdetails["payment_history"] = payment_history_dict

            context = {
                "entity_pk": corporation_id,
                "entity_type": "character",
                "character": paymentdetails,
            }

            return render(
                request,
                "taxsystem/modals/view_payment_details.html",
                context,
            )

        @api.get(
            "corporation/{corporation_id}/character/{character_id}/view/account/",
            response={200: dict, 403: str, 404: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_account_status(request, corporation_id: int, character_id: int):
            owner, perms = get_manage_corporation(request, corporation_id)
            perms = perms or get_character_permissions(request, character_id)

            if owner is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"
            try:
                payment_user = PaymentSystem.objects.get(
                    user__profile__main_character__character_id=character_id,
                    owner=owner,
                )
            except PaymentSystem.DoesNotExist:
                return 404, "Payment User Not Found"

            try:
                member = owner.ts_members.get(character_id=character_id)
            except owner.ts_members.model.DoesNotExist:
                member = None

            deposit = {
                "html": f"{intcomma(payment_user.deposit, use_l10n=True)} ISK",
                "raw": payment_user.deposit,
            }

            output = {
                "title": "Account Status for",
                "character_id": character_id,
                "character_portrait": lazy.get_character_portrait_url(
                    character_id, size=512, as_html=True
                ),
                "corporation_name": owner.corporation.corporation_name,
                "account_name": payment_user.name,
                "status": payment_user.Status(payment_user.status).html(text=True),
                "deposit": deposit,
                "has_paid": payment_user.has_paid_icon(badge=True, text=True),
                "last_paid": lazy.str_normalize_time(
                    payment_user.last_paid, hours=True
                ),
                "joined": (
                    lazy.str_normalize_time(member.joined, hours=True)
                    if member
                    else "N/A"
                ),
            }

            return output

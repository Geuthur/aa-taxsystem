from ninja import NinjaAPI

from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as trans

from taxsystem.api.helpers import get_corporation
from taxsystem.helpers.lazy import get_character_portrait_url
from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import Members, Payments, PaymentSystem

logger = get_extension_logger(__name__)


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/members/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_members(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            corporation_dict = {}

            members = Members.objects.filter(corporation=corp)

            for member in members:
                joined = timezone.localtime(member.joined).strftime("%Y-%m-%d")

                corporation_dict[member.character_id] = {
                    "character_id": member.character_id,
                    "character_portrait": get_character_portrait_url(
                        member.character_id, size=32, as_html=True
                    ),
                    "character_name": member.character_name,
                    "is_faulty": member.is_faulty,
                    "status": member.get_status_display(),
                    "joined": joined,
                    "actions": "",
                }

            output = []
            output.append({"corporation": corporation_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/administration/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_administration(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            payment_system = PaymentSystem.objects.filter(
                corporation=corp
            ).select_related("user", "user__user", "user__main_character")

            payment_dict = {}

            for payment in payment_system:
                if payment.is_active:
                    payment_dict[payment.user.user.username] = {
                        "character_id": payment.user.main_character.character_id,
                        "character_portrait": get_character_portrait_url(
                            payment.user.main_character.character_id,
                            size=32,
                            as_html=True,
                        ),
                        "character_name": payment.user.main_character.character_name,
                        "alts": payment.get_alt_ids(),
                        "status": payment.get_payment_status(),
                        "has_paid": payment.has_paid,
                        "wallet": payment.payment_pool,
                        "actions": "",
                    }

            output = []
            output.append({"corporation": payment_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/payments/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_payments(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            payment_system = Payments.objects.filter(payment_user__corporation=corp)

            payments_dict = {}

            for payment in payment_system:
                try:
                    character_id = payment.payment_user.user.main_character.character_id
                except AttributeError:
                    character_id = 0

                actions = ""
                if perms is True:
                    if payment.payment_status in [
                        Payments.States.PENDING,
                        Payments.States.NEEDS_APPROVAL,
                    ]:
                        amount = intcomma(payment.amount)
                        confirm_text = ""
                        confirm_text += trans("Are you sure to Confirm")
                        confirm_text += f"?<br><span class='fw-bold'>{amount} ISK (ID: {payment.pk}) "
                        confirm_text += trans("from")
                        confirm_text += f" {payment.payment_user.name}</span>"

                        actions = format_html(
                            "<td>{}</td>",
                            render_to_string(
                                "taxsystem/forms/approve.html",
                                {
                                    "corporation_id": corporation_id,
                                    "payment": payment,
                                    "title": trans("Approve Payment"),
                                    "confirm_text": confirm_text,
                                    "request": request,
                                },
                                request=request,
                            ),
                        )

                payments_dict[payment.pk] = {
                    "payment_id": payment.pk,
                    "date": payment.date,
                    "character_portrait": get_character_portrait_url(
                        character_id, size=32, as_html=True
                    ),
                    "character_name": payment.payment_user.name,
                    "amount": payment.amount,
                    "status": payment.get_payment_status_display(),
                    "approved": payment.get_approved_display(),
                    "system": payment.get_system_display(),
                    "payment_date": payment.formatted_payment_date(),
                    "actions": actions,
                }

            output = []
            output.append({"corporation": payments_dict})

            return output

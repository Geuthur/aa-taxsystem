# Standard Library
import logging

# Third Party
from ninja import NinjaAPI

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.api.helpers import get_manage_corporation
from taxsystem.api.taxsystem.helpers.administration import _delete_member
from taxsystem.api.taxsystem.helpers.payments import _payments_actions
from taxsystem.api.taxsystem.helpers.paymentsystem import (
    _payment_system_actions,
    _payments_info,
)
from taxsystem.api.taxsystem.helpers.statistics import (
    _get_divisions_dict,
    _get_statistics_dict,
)
from taxsystem.helpers import lazy
from taxsystem.models.logs import AdminLogs
from taxsystem.models.tax import Members, Payments, PaymentSystem
from taxsystem.models.wallet import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)

logger = logging.getLogger(__name__)


class AdminApiEndpoints:
    tags = ["Admin"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/dashboard/",
            response={200: dict, 403: str, 404: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_dashboard(request, corporation_id: int):
            owner, perms = get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            divisions = CorporationWalletDivision.objects.filter(corporation=owner)

            corporation_id = owner.corporation.corporation_id
            corporation_logo = lazy.get_corporation_logo_url(
                corporation_id, size=64, as_html=True
            )
            divisions_dict = _get_divisions_dict(divisions)
            statistics_dict = {owner.name: _get_statistics_dict(owner)}

            past30_days = CorporationWalletJournalEntry.objects.filter(
                division__corporation=owner,
                date__gte=timezone.now() - timezone.timedelta(days=30),
            ).aggregate(total=Sum("amount"))

            total_amount = past30_days.get("total", 0) or 0
            activity_color = "text-success" if total_amount >= 0 else "text-danger"
            activity_html = f"<span class='{activity_color}'>{intcomma(total_amount, use_l10n=True)}</span> ISK"

            output = {
                "corporation_name": owner.name,
                "corporation_id": corporation_id,
                "corporation_logo": corporation_logo,
                "update_status": owner.get_status.bootstrap_icon(),
                "tax_amount": owner.tax_amount,
                "tax_period": owner.tax_period,
                "divisions": divisions_dict,
                "statistics": statistics_dict,
                "activity": format_html(activity_html),
            }

            return output

        @api.get(
            "corporation/{corporation_id}/view/members/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_members(request, corporation_id: int):
            corp, perms = get_manage_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            corporation_dict = {}

            members = Members.objects.filter(owner=corp)

            for member in members:
                actions = _delete_member(
                    corporation_id=corporation_id,
                    member=member,
                    perms=perms,
                    request=request,
                )

                corporation_dict[member.character_id] = {
                    "character_id": member.character_id,
                    "character_portrait": lazy.get_character_portrait_url(
                        member.character_id, size=32, as_html=True
                    ),
                    "character_name": member.character_name,
                    "is_faulty": member.is_faulty,
                    "status": member.get_status_display(),
                    "joined": lazy.str_normalize_time(member.joined, hours=False),
                    "actions": actions,
                }

            output = []
            output.append({"corporation": corporation_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/paymentsystem/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_paymentsystem(request, corporation_id: int):
            corp, perms = get_manage_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            payment_system = (
                PaymentSystem.objects.filter(
                    owner=corp,
                    user__profile__main_character__isnull=False,
                )
                .exclude(status=PaymentSystem.Status.MISSING)
                .select_related(
                    "user", "user__profile", "user__profile__main_character"
                )
            )

            payment_dict = {}

            for user in payment_system:
                character_id = user.user.profile.main_character.character_id
                character_name = user.user.profile.main_character.character_name

                actions = _payment_system_actions(
                    corporation_id=corporation_id,
                    payment_system=user,
                    perms=perms,
                    request=request,
                )
                deposit = _payments_info(
                    corporation_id=corporation_id,
                    user=user,
                    perms=perms,
                    request=request,
                )
                payment_dict[character_id] = {
                    "character_id": character_id,
                    "character_portrait": lazy.get_character_portrait_url(
                        character_id=character_id,
                        size=32,
                        as_html=True,
                    ),
                    "character_name": character_name,
                    "alts": user.get_alt_ids(),
                    "status": user.get_payment_status(),
                    "deposit": deposit,
                    "has_paid": user.has_paid_icon(badge=True),
                    "has_paid_filter": _("Yes") if user.has_paid else _("No"),
                    "last_paid": lazy.str_normalize_time(user.last_paid, hours=True),
                    "is_active": user.is_active,
                    "actions": actions,
                }

            output = []
            output.append({"corporation": payment_dict})

            return output

        @api.get(
            "corporation/admin/{corporation_id}/view/logs/",
            response={200: list, 403: str},
            tags=self.tags,
        )
        def get_corporation_admin_logs(request, corporation_id: int):
            corp, perms = get_manage_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            logs = AdminLogs.objects.filter(owner=corp).order_by("-date")

            logs_dict = {}

            for log in logs:
                date = lazy.str_normalize_time(log.date, hours=True)
                logs_dict[log.pk] = {
                    "date": date,
                    "user_name": log.user.username,
                    "action": log.action,
                    "log": log.log,
                }

            output = []
            output.append({"logs": logs_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/character/{character_id}/view/payments/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_main_character_payments(
            request, corporation_id: int, character_id: int
        ):
            owner, perms = get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            payments = Payments.objects.filter(
                account__owner=owner,
                account__user__profile__main_character__character_id=character_id,
            )

            if not payments:
                return 404, "No Payments Found"

            # Create a dict for the character
            payments_char_dict = {
                "title": "Payments for",
                "character_id": character_id,
                "character_portrait": lazy.get_character_portrait_url(
                    character_id, size=32, as_html=True
                ),
                "character_name": payments[0].account.name,
            }

            # Create a dict for each payment
            payments_dict = {}
            for payment in payments:
                try:
                    character_id = (
                        payment.account.user.profile.main_character.character_id
                    )
                    portrait = lazy.get_character_portrait_url(
                        character_id, size=32, as_html=True
                    )
                except AttributeError:
                    portrait = ""

                actions = _payments_actions(corporation_id, payment, perms, request)
                amount = f"{intcomma(payment.amount, use_l10n=True)} ISK"

                payments_dict[payment.pk] = {
                    "payment_id": payment.pk,
                    "character_portrait": portrait,
                    "character_name": payment.account.name,
                    "payment_date": payment.formatted_payment_date,
                    "amount": amount,
                    "request_status": payment.get_request_status_display(),
                    "reviser": payment.reviser,
                    "division": payment.division,
                    "reason": payment.reason,
                    "actions": actions,
                }

            # Add payments to the character dict
            payments_char_dict["payments"] = payments_dict

            context = {
                "entity_pk": corporation_id,
                "entity_type": "character",
                "character": payments_char_dict,
            }

            return render(
                request,
                "taxsystem/modals/view_character_payments.html",
                context,
            )

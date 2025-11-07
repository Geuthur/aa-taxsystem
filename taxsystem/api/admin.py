# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timezone import datetime
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.filters import _filter_actions
from taxsystem.api.helpers.manage import generate_member_delete_button
from taxsystem.api.helpers.paymentsystem import (
    _payments_info,
    payment_system_actions,
)
from taxsystem.api.helpers.statistics import (
    _get_divisions_dict,
    _get_statistics_dict,
)
from taxsystem.api.schema import (
    AccountSchema,
    CharacterSchema,
    CorporationSchema,
    DataTableSchema,
    UpdateStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.filters import JournalFilter
from taxsystem.models.logs import AdminLogs
from taxsystem.models.tax import Members, PaymentSystem
from taxsystem.models.wallet import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class MembersSchema(Schema):
    character: CharacterSchema
    is_faulty: bool
    status: str
    joined: str
    actions: str


class MembersResponseSchema(Schema):
    corporation: list[MembersSchema]


class DashboardResponseSchema(Schema):
    corporation: CorporationSchema
    update_status: UpdateStatusSchema
    tax_amount: int
    tax_period: int
    divisions: dict
    statistics: dict
    activity: str


class PaymentSystemSchema(Schema):
    account: AccountSchema
    status: str
    deposit: str
    has_paid: DataTableSchema
    last_paid: datetime | None = None
    is_active: bool
    actions: str


class PaymentSystemResponse(Schema):
    corporation: list[PaymentSystemSchema]


class AdminApiEndpoints:
    tags = ["Admin"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/dashboard/",
            response={200: DashboardResponseSchema, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_dashboard(request, corporation_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            divisions = CorporationWalletDivision.objects.filter(corporation=owner)

            corporation_logo = lazy.get_corporation_logo_url(
                corporation_id, size=64, as_html=True
            )
            divisions_dict = _get_divisions_dict(divisions)
            statistics_dict = {owner.name: _get_statistics_dict(owner)}

            past30_days = (
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation=owner,
                    date__gte=timezone.now() - timezone.timedelta(days=30),
                )
                .exclude(first_party_id=corporation_id, second_party_id=corporation_id)
                .aggregate(total=Sum("amount"))
            )

            total_amount = past30_days.get("total", 0) or 0
            activity_color = "text-success" if total_amount >= 0 else "text-danger"
            activity_html = f"<span class='{activity_color}'>{intcomma(total_amount, use_l10n=True)}</span> ISK"

            dashboard_response = DashboardResponseSchema(
                corporation=CorporationSchema(
                    corporation_id=owner.corporation.corporation_id,
                    corporation_name=owner.corporation.corporation_name,
                    corporation_portrait=corporation_logo,
                    corporation_ticker=owner.corporation.corporation_ticker,
                ),
                update_status=UpdateStatusSchema(
                    status=owner.get_update_status,
                    icon=owner.get_status.bootstrap_icon(),
                ),
                tax_amount=owner.tax_amount,
                tax_period=owner.tax_period,
                divisions=divisions_dict,
                statistics=statistics_dict,
                activity=format_html(activity_html),
            )
            return dashboard_response

        @api.get(
            "corporation/{corporation_id}/view/members/",
            response={200: MembersResponseSchema, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_members(request, corporation_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            # Get Members
            members = Members.objects.filter(owner=owner)

            response_members_list: list[MembersSchema] = []
            for member in members:
                actions = ""
                # Create the delete button if member is missing
                if perms and member.is_missing:
                    actions = generate_member_delete_button(member=member)

                response_member = MembersSchema(
                    character=CharacterSchema(
                        character_id=member.character_id,
                        character_name=member.character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            member.character_id, size=32, as_html=True
                        ),
                    ),
                    is_faulty=member.is_faulty,
                    status=member.get_status_display(),
                    joined=lazy.str_normalize_time(member.joined, hours=False),
                    actions=actions,
                )
                response_members_list.append(response_member)

            return MembersResponseSchema(corporation=response_members_list)

        @api.get(
            "corporation/{corporation_id}/view/paymentsystem/",
            response={200: PaymentSystemResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_paymentsystem(request, corporation_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            # Get Payment Accounts for Corporation except those missing main character
            payment_system = (
                PaymentSystem.objects.filter(
                    owner=owner,
                    user__profile__main_character__isnull=False,
                )
                .exclude(status=PaymentSystem.Status.MISSING)
                .select_related(
                    "user", "user__profile", "user__profile__main_character"
                )
            )

            payment_accounts_list: list[PaymentSystemSchema] = []
            for user in payment_system:
                character_id = user.user.profile.main_character.character_id
                character_name = user.user.profile.main_character.character_name

                actions = payment_system_actions(
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
                response_payment_account = PaymentSystemSchema(
                    payment_id=user.pk,
                    account=AccountSchema(
                        character_id=character_id,
                        character_name=character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            character_id, size=32, as_html=True
                        ),
                        alt_ids=user.get_alt_ids(),
                    ),
                    status=user.get_payment_status(),
                    deposit=deposit,
                    has_paid=DataTableSchema(
                        raw=str(user.has_paid),
                        display=user.has_paid_icon(badge=True),
                        sort=str(int(user.has_paid)),
                        translation=_("Has Paid"),
                        dropdown_text=_("Yes") if user.has_paid else _("No"),
                    ),
                    last_paid=user.last_paid,
                    is_active=user.is_active,
                    actions=actions,
                )
                payment_accounts_list.append(response_payment_account)

            return PaymentSystemResponse(corporation=payment_accounts_list)

        @api.get(
            "corporation/admin/{corporation_id}/view/logs/",
            response={200: list, 403: str},
            tags=self.tags,
        )
        def get_corporation_admin_logs(request, corporation_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            logs = AdminLogs.objects.filter(owner=owner).order_by("-date")

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
            "corporation/{corporation_id}/filter_set/{filter_set_id}/view/filter/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_filter_set_filters(request, corporation_id: int, filter_set_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, "Corporation Not Found"

            if perms is False:
                return 403, "Permission Denied"

            filters = JournalFilter.objects.filter(
                filter_set__pk=filter_set_id,
            )

            output = []

            for filter_obj in filters:
                if filter_obj.filter_type == JournalFilter.FilterType.AMOUNT:
                    value = f"{intcomma(filter_obj.value, use_l10n=True)} ISK"
                else:
                    value = filter_obj.value

                filter_dict = {
                    "id": filter_obj.pk,
                    "filter_set": filter_obj.filter_set,
                    "filter_type": filter_obj.get_filter_type_display(),
                    "value": value,
                    "actions": _filter_actions(
                        corporation_id=corporation_id,
                        filter_obj=filter_obj,
                        perms=perms,
                        request=request,
                    ),
                }
                output.append(filter_dict)

            return render(
                request,
                "taxsystem/modals/view_filter.html",
                context={
                    "filters": output,
                },
            )

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
from taxsystem.api.helpers.manage import (
    generate_filter_delete_button,
    generate_member_delete_button,
    generate_ps_info_button,
    generate_ps_toggle_button,
)
from taxsystem.api.helpers.statistics import (
    StatisticsResponse,
    get_members_statistics,
    get_payment_system_statistics,
    get_payments_statistics,
)
from taxsystem.api.schema import (
    AccountSchema,
    AdminHistorySchema,
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
    joined: datetime
    actions: str


class PaymentSystemSchema(Schema):
    account: AccountSchema
    status: str
    deposit: int
    has_paid: DataTableSchema
    last_paid: datetime | None = None
    is_active: bool
    actions: str


class MembersResponse(Schema):
    corporation: list[MembersSchema]


class DivisionSchema(Schema):
    name: str
    balance: float


class DashboardDivisionsSchema(Schema):
    divisions: list[DivisionSchema]
    total_balance: float


class DashboardResponse(Schema):
    corporation: CorporationSchema
    update_status: UpdateStatusSchema
    tax_amount: int
    tax_period: int
    divisions: DashboardDivisionsSchema
    statistics: StatisticsResponse
    activity: str


class PaymentSystemResponse(Schema):
    corporation: list[PaymentSystemSchema]


class AdminLogResponse(Schema):
    corporation: list[AdminHistorySchema]


class FilterSetModelSchema(Schema):
    owner_id: int
    name: str
    description: str
    enabled: bool
    actions: str | None = None


class FilterModelSchema(Schema):
    filter_set: FilterSetModelSchema
    filter_type: str
    value: str
    actions: str | None = None


class AdminApiEndpoints:
    tags = ["Admin"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/dashboard/",
            response={200: DashboardResponse, 403: dict, 404: dict},
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

            # Create divisions
            response_divisions_list: list[DivisionSchema] = []
            total_balance = 0
            for i, division in enumerate(divisions, start=1):
                division_name = (
                    division.name if division.name else f"{i}. {_('Division')}"
                )
                response_divisions_list.append(
                    DivisionSchema(
                        name=division_name,
                        balance=division.balance,
                    )
                )
                total_balance += division.balance

            # Create statistics
            response_statistics = StatisticsResponse(
                owner_id=owner.corporation.corporation_id,
                owner_name=owner.corporation.corporation_name,
                payment_system=get_payment_system_statistics(owner),
                payments=get_payments_statistics(owner),
                members=get_members_statistics(owner),
            )

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

            dashboard_response = DashboardResponse(
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
                divisions=DashboardDivisionsSchema(
                    divisions=response_divisions_list,
                    total_balance=total_balance,
                ),
                statistics=response_statistics,
                activity=format_html(activity_html),
            )
            return dashboard_response

        @api.get(
            "corporation/{corporation_id}/view/members/",
            response={200: MembersResponse, 403: dict, 404: dict},
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
                    joined=member.joined,
                    actions=actions,
                )
                response_members_list.append(response_member)

            return MembersResponse(corporation=response_members_list)

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
            for account in payment_system:
                character_id = account.user.profile.main_character.character_id
                character_name = account.user.profile.main_character.character_name

                # Create the action buttons
                actions = []
                actions.append(generate_ps_toggle_button(account=account))
                actions.append(generate_ps_info_button(account=account))
                actions = format_html(
                    f'<div class="d-flex justify-content-end">{format_html("".join(actions))}</div>'
                )

                response_payment_account = PaymentSystemSchema(
                    payment_id=account.pk,
                    account=AccountSchema(
                        character_id=character_id,
                        character_name=character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            character_id, size=32, as_html=True
                        ),
                        alt_ids=account.get_alt_ids(),
                    ),
                    status=account.get_payment_status(),
                    deposit=account.deposit,
                    has_paid=DataTableSchema(
                        raw=str(account.has_paid),
                        display=account.has_paid_icon(badge=True),
                        sort=str(int(account.has_paid)),
                        translation=_("Has Paid"),
                        dropdown_text=_("Yes") if account.has_paid else _("No"),
                    ),
                    last_paid=account.last_paid,
                    is_active=account.is_active,
                    actions=actions,
                )
                payment_accounts_list.append(response_payment_account)

            return PaymentSystemResponse(corporation=payment_accounts_list)

        @api.get(
            "corporation/admin/{corporation_id}/view/logs/",
            response={200: AdminLogResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_admin_logs(request, corporation_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            logs = AdminLogs.objects.filter(owner=owner).order_by("-date")

            response_admin_logs_list: list[AdminHistorySchema] = []
            for log in logs:
                response_admin_log = AdminHistorySchema(
                    log_id=log.pk,
                    user_name=log.user.username,
                    date=timezone.localtime(log.date).strftime("%Y-%m-%d %H:%M"),
                    action=log.action,
                    comment=log.comment,
                )
                response_admin_logs_list.append(response_admin_log)

            return AdminLogResponse(corporation=response_admin_logs_list)

        @api.get(
            "corporation/{corporation_id}/filter-set/{filter_set_id}/view/filter/",
            response={200: list[FilterModelSchema], 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_filter_set_filters(request, corporation_id: int, filter_set_id: int):
            owner, perms = core.get_manage_corporation(request, corporation_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            filters = JournalFilter.objects.filter(
                filter_set__pk=filter_set_id,
            )

            response_filter_list: list[FilterModelSchema] = []
            for filter_obj in filters:
                if filter_obj.filter_type == JournalFilter.FilterType.AMOUNT:
                    value = f"{intcomma(filter_obj.value, use_l10n=True)} ISK"
                else:
                    value = filter_obj.value

                actions = []
                actions.append(generate_filter_delete_button(filter_obj=filter_obj))
                actions = format_html(
                    f'<div class="d-flex justify-content-end">{format_html("".join(actions))}</div>'
                )

                response_filter = FilterModelSchema(
                    filter_set=FilterSetModelSchema(
                        owner_id=filter_obj.filter_set.owner.pk,
                        name=filter_obj.filter_set.name,
                        description=filter_obj.filter_set.description,
                        enabled=filter_obj.filter_set.enabled,
                    ),
                    filter_type=filter_obj.get_filter_type_display(),
                    value=value,
                    actions=actions,
                )
                response_filter_list.append(response_filter)

            return render(
                request,
                "taxsystem/modals/view_filter.html",
                context={
                    "filters": response_filter_list,
                },
            )

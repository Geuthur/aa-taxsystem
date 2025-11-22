# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.common import (
    build_admin_logs_response_list,
    build_filters_response_list,
    build_payment_accounts_response_list,
    calculate_activity_html,
    create_dashboard_common_data,
    create_member_response_data,
)
from taxsystem.api.helpers.manage import (
    generate_member_delete_button,
)
from taxsystem.api.schema import (
    AdminHistorySchema,
    BaseDashboardResponse,
    CorporationSchema,
    FilterModelSchema,
    MembersSchema,
    PaymentSystemSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.corporation import (
    CorporationAdminHistory,
    Members,
)
from taxsystem.models.wallet import CorporationWalletDivision

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class MembersResponse(Schema):
    corporation: list[MembersSchema]


class DashboardResponse(BaseDashboardResponse):
    owner: CorporationSchema


class PaymentSystemResponse(Schema):
    owner: list[PaymentSystemSchema]


class AdminLogResponse(Schema):
    corporation: list[AdminHistorySchema]


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

            # Create common dashboard data
            common_data = create_dashboard_common_data(owner, divisions)

            # Calculate activity
            activity_html = calculate_activity_html(owner, corporation_id)

            dashboard_response = DashboardResponse(
                owner=CorporationSchema(
                    owner_id=owner.eve_corporation.corporation_id,
                    owner_name=owner.eve_corporation.corporation_name,
                    owner_type="corporation",
                    corporation_id=owner.eve_corporation.corporation_id,
                    corporation_name=owner.eve_corporation.corporation_name,
                    corporation_portrait=corporation_logo,
                    corporation_ticker=owner.eve_corporation.corporation_ticker,
                ),
                activity=format_html(activity_html),
                **common_data,
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
            members = (
                Members.objects.filter(owner=owner)
                .select_related("owner")
                .order_by("character_name")
            )

            response_members_list: list[MembersSchema] = []
            for member in members:
                actions = ""
                # Create the delete button if member is missing
                if perms and member.is_missing:
                    actions = generate_member_delete_button(member=member)

                member_data = create_member_response_data(member)
                response_member = MembersSchema(**member_data, actions=actions)
                response_members_list.append(response_member)

            return MembersResponse(corporation=response_members_list)

        @api.get(
            "owner/{owner_id}/view/paymentsystem/",
            response={200: PaymentSystemResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_paymentsystem(request, owner_id: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            # Get Payment Accounts for Owner except those missing main character
            payment_accounts = (
                owner.payments_account_class.objects.filter(
                    owner=owner,
                    user__profile__main_character__isnull=False,
                )
                .exclude(status=owner.payments_account_class.Status.MISSING)
                .select_related(
                    "user", "user__profile", "user__profile__main_character"
                )
                .prefetch_related("user__character_ownerships__character")
            )

            # Use generic helper function
            payment_accounts_list = build_payment_accounts_response_list(
                payment_accounts, PaymentSystemSchema
            )

            return PaymentSystemResponse(owner=payment_accounts_list)

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

            logs = (
                CorporationAdminHistory.objects.filter(owner=owner)
                .select_related("user")
                .order_by("-date")
            )

            # Use generic helper function
            response_admin_logs_list = build_admin_logs_response_list(
                logs, AdminHistorySchema
            )

            return AdminLogResponse(corporation=response_admin_logs_list)

        @api.get(
            "owner/{owner_id}/filter-set/{filter_set_id}/view/filter/",
            response={200: list[FilterModelSchema], 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_filter_set_filters(request, owner_id: int, filter_set_id: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            filters = owner.filter_class.objects.filter(
                filter_set__pk=filter_set_id,
            ).select_related("filter_set", "filter_set__owner")

            # Use generic helper function
            response_filter_list = build_filters_response_list(
                filters, FilterModelSchema
            )

            return render(
                request,
                "taxsystem/modals/view_filter.html",
                context={
                    "filters": response_filter_list,
                },
            )

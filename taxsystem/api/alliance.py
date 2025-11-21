# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.shortcuts import get_object_or_404
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
    calculate_activity_html,
    create_dashboard_common_data,
    create_member_response_data,
    create_own_payment_response_data,
    create_payment_response_data,
    get_optimized_own_payments_queryset,
    get_optimized_payments_queryset,
)
from taxsystem.api.schema import (
    AllianceSchema,
    BaseDashboardResponse,
    CharacterSchema,
    MembersSchema,
    PaymentSchema,
    PaymentSystemSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.alliance import AlliancePaymentAccount, AlliancePayments
from taxsystem.models.corporation import Members
from taxsystem.models.wallet import CorporationWalletDivision

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentAllianceSchema(PaymentSchema):
    character: CharacterSchema


class PaymentsResponse(Schema):
    owner: list[PaymentAllianceSchema]


class PaymentSystemResponse(Schema):
    owner: list[PaymentSystemSchema]


class DivisionSchema(Schema):
    name: str
    balance: float


class MembersResponse(Schema):
    corporation: list[MembersSchema]


class DashboardResponse(BaseDashboardResponse):
    owner: AllianceSchema


class AllianceApiEndpoints:
    tags = ["Alliance Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "alliance/{alliance_id}/view/payments/",
            response={200: PaymentsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_payments(request, alliance_id: int):
            owner, perms = core.get_manage_alliance(request, alliance_id)

            if owner is None:
                return 404, {"error": "Alliance Not Found"}

            if perms is False:
                return 403, {"error": "Permission Denied"}

            # Get Payments
            payments = get_optimized_payments_queryset(
                AlliancePayments, owner, owner.eve_alliance.alliance_id
            )

            response_payments_list: list[PaymentAllianceSchema] = []
            for payment in payments:
                payment_data = create_payment_response_data(payment, request, perms)
                response_payment = PaymentAllianceSchema(**payment_data)
                response_payments_list.append(response_payment)
            return PaymentsResponse(owner=response_payments_list)

        @api.get(
            "alliance/{alliance_id}/view/own-payments/",
            response={200: PaymentsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_own_payments(request, alliance_id: int):
            owner = core.get_alliance(request, alliance_id)

            if owner is None:
                return 404, {"error": "Alliance Not Found"}

            account = get_object_or_404(
                AlliancePaymentAccount, owner=owner, user=request.user
            )

            # Get Payments
            payments = get_optimized_own_payments_queryset(
                AlliancePayments, owner, account, owner.eve_alliance.alliance_id
            )

            if len(payments) == 0:
                return 403, {"error": _("No Payments Found")}

            response_payments_list: list[PaymentAllianceSchema] = []
            for payment in payments:
                payment_data = create_own_payment_response_data(payment)
                response_payment = PaymentAllianceSchema(**payment_data)
                response_payments_list.append(response_payment)
            return PaymentsResponse(owner=response_payments_list)

        @api.get(
            "alliance/{alliance_id}/view/dashboard/",
            response={200: DashboardResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_alliance_dashboard(request, alliance_id: int):
            owner, perms = core.get_manage_alliance(request, alliance_id)

            if owner is None:
                return 404, {"error": _("Alliance Not Found")}
            if perms is False:
                return 403, {"error": _("Permission Denied")}

            divisions = CorporationWalletDivision.objects.filter(
                corporation=owner.corporation
            )

            alliance_logo = lazy.get_alliance_logo_url(
                alliance_id, size=64, as_html=True
            )

            # Create common dashboard data
            common_data = create_dashboard_common_data(owner, divisions)

            # Calculate activity
            activity_html = calculate_activity_html(
                owner.corporation, owner.corporation.eve_corporation.corporation_id
            )

            dashboard_response = DashboardResponse(
                owner=AllianceSchema(
                    owner_id=owner.eve_alliance.alliance_id,
                    owner_name=owner.eve_alliance.alliance_name,
                    owner_type="alliance",
                    alliance_id=owner.eve_alliance.alliance_id,
                    alliance_name=owner.eve_alliance.alliance_name,
                    alliance_portrait=alliance_logo,
                    alliance_ticker=owner.eve_alliance.alliance_ticker,
                    main_corporation_id=owner.corporation.eve_corporation.corporation_id,
                    main_corporation_name=owner.corporation.eve_corporation.corporation_name,
                ),
                activity=format_html(activity_html),
                **common_data,
            )
            return dashboard_response

        @api.get(
            "alliance/{alliance_id}/view/members/",
            response={200: MembersResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_members(request, alliance_id: int):
            owner, perms = core.get_manage_alliance(request, alliance_id)

            if owner is None:
                return 404, {"error": _("Alliance Not Found")}

            if perms is False:
                return 403, {"error": _("Permission Denied")}

            # Get Members
            members = (
                Members.objects.filter(
                    owner__eve_corporation__alliance=owner.eve_alliance
                )
                .select_related(
                    "owner",
                    "owner__eve_corporation",
                    "owner__eve_corporation__alliance",
                )
                .order_by("character_name")
            )

            response_members_list: list[MembersSchema] = []
            for member in members:
                member_data = create_member_response_data(member)
                response_member = MembersSchema(**member_data)
                response_members_list.append(response_member)

            return MembersResponse(corporation=response_members_list)

# Third Party
from ninja import Schema

# Django
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.schema import (
    DashboardDivisionsSchema,
    DivisionSchema,
    UpdateStatusSchema,
)
from taxsystem.models.alliance import (
    AllianceOwner,
)
from taxsystem.models.corporation import (
    CorporationOwner,
    Members,
)
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentSystemStatisticsSchema(Schema):
    ps_count: int
    ps_count_active: int
    ps_count_inactive: int
    ps_count_deactivated: int
    ps_count_paid: int
    ps_count_unpaid: int


class PaymentsStatisticsSchema(Schema):
    payments_count: int
    payments_pending: int
    payments_automatic: int
    payments_manual: int


class MembersStatisticsSchema(Schema):
    members_count: int
    members_unregistered: int
    members_alts: int
    members_mains: int


class StatisticsResponse(Schema):
    owner_id: int | None = None
    owner_name: str | None = None
    payment_system: PaymentSystemStatisticsSchema
    payments: PaymentsStatisticsSchema
    members: MembersStatisticsSchema


def create_dashboard_common_data(owner, divisions):
    """
    Create common dashboard data structure

    Args:
        owner: Owner object (CorporationOwner or AllianceOwner)
        divisions: QuerySet of CorporationWalletDivision objects

    Returns:
        dict: Dictionary containing common dashboard data
    """
    # Create divisions
    response_divisions_list = []
    total_balance = 0

    # Get divisions and calculate total balance
    for i, division in enumerate(divisions, start=1):
        division_name = division.name if division.name else f"{i}. {_('Division')}"
        response_divisions_list.append(
            DivisionSchema(
                name=division_name,
                balance=division.balance,
            )
        )
        total_balance += division.balance

    # Create statistics
    response_statistics = StatisticsResponse(
        owner_id=owner.pk,
        owner_name=owner.name,
        payment_system=get_payment_system_statistics(owner),
        payments=get_payments_statistics(owner),
        members=get_members_statistics(owner),
    )

    return {
        "update_status": UpdateStatusSchema(
            status=owner.get_update_status,
            icon=owner.get_status.bootstrap_icon(),
        ),
        "tax_amount": owner.tax_amount,
        "tax_period": owner.tax_period,
        "divisions": DashboardDivisionsSchema(
            divisions=response_divisions_list,
            total_balance=total_balance,
        ),
        "statistics": response_statistics,
    }


def get_payments_statistics(
    owner: CorporationOwner | AllianceOwner,
) -> PaymentsStatisticsSchema:
    """Get payments statistics for an Owner."""
    payments = owner.payment_model.objects.filter(account__owner=owner)

    payments_counts = payments.aggregate(
        total=Count("id"),
        automatic=Count("id", filter=Q(reviser="System")),
        manual=Count("id", filter=~Q(reviser="System") & ~Q(reviser="")),
        pending=Count(
            "id",
            filter=Q(
                request_status__in=[
                    PaymentRequestStatus.PENDING,
                    PaymentRequestStatus.NEEDS_APPROVAL,
                ]
            ),
        ),
    )

    return PaymentsStatisticsSchema(
        payments_count=payments_counts["total"],
        payments_pending=payments_counts["pending"],
        payments_automatic=payments_counts["automatic"],
        payments_manual=payments_counts["manual"],
    )


def get_payment_system_statistics(
    owner: CorporationOwner | AllianceOwner,
) -> PaymentSystemStatisticsSchema:
    """Get payment system statistics for an Owner."""
    payment_system = owner.account_model.objects.filter(owner=owner)
    period = timezone.timedelta(days=owner.tax_period)

    payment_system_counts = payment_system.exclude(
        status=AccountStatus.MISSING
    ).aggregate(
        users=Count("id"),
        active=Count("id", filter=Q(status=AccountStatus.ACTIVE)),
        inactive=Count("id", filter=Q(status=AccountStatus.INACTIVE)),
        deactivated=Count("id", filter=Q(status=AccountStatus.DEACTIVATED)),
        paid=Count(
            "id",
            filter=(
                Q(deposit__gte=F("owner__tax_amount"))
                | (
                    Q(last_paid__isnull=False)
                    & Q(deposit__gte=0)
                    & Q(last_paid__gte=timezone.now() - period)
                )
            )
            & Q(status=AccountStatus.ACTIVE),
        ),
    )
    # Calculate unpaid count
    unpaid = payment_system_counts["active"] - payment_system_counts["paid"]

    return PaymentSystemStatisticsSchema(
        ps_count=payment_system_counts["users"],
        ps_count_active=payment_system_counts["active"],
        ps_count_inactive=payment_system_counts["inactive"],
        ps_count_deactivated=payment_system_counts["deactivated"],
        ps_count_paid=payment_system_counts["paid"],
        ps_count_unpaid=unpaid,
    )


def get_members_statistics(
    owner: CorporationOwner | AllianceOwner,
) -> MembersStatisticsSchema:
    # Determine the correct filter based on alliance system setting
    if isinstance(owner, CorporationOwner):
        # Return all members in the corporation
        members = Members.objects.filter(owner=owner).order_by("character_name")
    else:
        # Return all members in the alliance
        members = Members.objects.filter(
            owner__eve_corporation__alliance=owner.eve_alliance
        ).order_by("character_name")

    members_count = members.aggregate(
        total=Count("character_id"),
        unregistered=Count("character_id", filter=Q(status=Members.States.NOACCOUNT)),
        alts=Count("character_id", filter=Q(status=Members.States.IS_ALT)),
        mains=Count("character_id", filter=Q(status=Members.States.ACTIVE)),
    )

    return MembersStatisticsSchema(
        members_count=members_count["total"],
        members_unregistered=members_count["unregistered"],
        members_alts=members_count["alts"],
        members_mains=members_count["mains"],
    )

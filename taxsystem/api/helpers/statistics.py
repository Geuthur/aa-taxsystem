# Third Party
from ninja import Schema

# Django
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

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
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class TaxAccountStatisticsSchema(Schema):
    accounts: int
    accounts_active: int
    accounts_inactive: int
    accounts_deactivated: int
    accounts_paid: int
    accounts_unpaid: int


class PaymentsStatisticsSchema(Schema):
    payments: int
    payments_pending: int
    payments_automatic: int
    payments_manual: int


class MembersStatisticsSchema(Schema):
    members: int
    members_unregistered: int
    members_alts: int
    members_mains: int


class StatisticsResponse(Schema):
    owner_id: int | None = None
    owner_name: str | None = None
    tax_account: TaxAccountStatisticsSchema
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
        tax_account=get_tax_account_statistics(owner),
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
    payments = owner.payment_model.objects.filter(owner=owner)

    payments_statistics = payments.aggregate(
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
        payments=payments_statistics["total"],
        payments_pending=payments_statistics["pending"],
        payments_automatic=payments_statistics["automatic"],
        payments_manual=payments_statistics["manual"],
    )


def get_tax_account_statistics(
    owner: CorporationOwner | AllianceOwner,
) -> TaxAccountStatisticsSchema:
    """Get tax account statistics for an Owner."""
    tax_accounts = owner.account_model.objects.filter(owner=owner)
    period = timezone.timedelta(days=owner.tax_period)

    statistics = tax_accounts.exclude(status=AccountStatus.MISSING).aggregate(
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
    unpaid = statistics["active"] - statistics["paid"]

    return TaxAccountStatisticsSchema(
        accounts=statistics["users"],
        accounts_active=statistics["active"],
        accounts_inactive=statistics["inactive"],
        accounts_deactivated=statistics["deactivated"],
        accounts_paid=statistics["paid"],
        accounts_unpaid=unpaid,
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

    members_statistics = members.aggregate(
        total=Count("character_id"),
        unregistered=Count("character_id", filter=Q(status=Members.States.NOACCOUNT)),
        alts=Count("character_id", filter=Q(status=Members.States.IS_ALT)),
        mains=Count("character_id", filter=Q(status=Members.States.ACTIVE)),
    )

    return MembersStatisticsSchema(
        members=members_statistics["total"],
        members_unregistered=members_statistics["unregistered"],
        members_alts=members_statistics["alts"],
        members_mains=members_statistics["mains"],
    )

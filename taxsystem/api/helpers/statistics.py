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
from taxsystem.models.alliance import (
    AllianceOwner,
    AlliancePaymentAccount,
    AlliancePayments,
)
from taxsystem.models.base import PaymentAccountBase
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationPaymentAccount,
    CorporationPayments,
    Members,
)

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


def get_payments_statistics(owner) -> PaymentsStatisticsSchema:
    """Get payments statistics for an Owner."""
    # Determine the correct filter based on alliance system setting
    if isinstance(owner, CorporationOwner):
        # Determine the correct filter based on alliance system setting
        payments = CorporationPayments.objects.filter(account__owner=owner)
    elif isinstance(owner, AllianceOwner):
        payments = AlliancePayments.objects.filter(account__owner=owner)
    else:
        raise ValueError("Owner must be CorporationOwner or AllianceOwner")

    payments_counts = payments.aggregate(
        total=Count("id"),
        automatic=Count("id", filter=Q(reviser="System")),
        manual=Count("id", filter=~Q(reviser="System") & ~Q(reviser="")),
        pending=Count(
            "id",
            filter=Q(
                request_status__in=[
                    CorporationPayments.RequestStatus.PENDING,
                    CorporationPayments.RequestStatus.NEEDS_APPROVAL,
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


def get_payment_system_statistics(owner) -> PaymentSystemStatisticsSchema:
    """Get payment system statistics for an Owner."""
    if isinstance(owner, CorporationOwner):
        # Determine the correct filter based on alliance system setting
        payment_system = CorporationPaymentAccount.objects.filter(owner=owner)
    elif isinstance(owner, AllianceOwner):
        payment_system = AlliancePaymentAccount.objects.filter(owner=owner)
    else:
        raise ValueError("Owner must be CorporationOwner or AllianceOwner")

    period = timezone.timedelta(days=owner.tax_period)

    payment_system_counts = payment_system.exclude(
        status=PaymentAccountBase.Status.MISSING
    ).aggregate(
        users=Count("id"),
        active=Count("id", filter=Q(status=PaymentAccountBase.Status.ACTIVE)),
        inactive=Count("id", filter=Q(status=PaymentAccountBase.Status.INACTIVE)),
        deactivated=Count("id", filter=Q(status=PaymentAccountBase.Status.DEACTIVATED)),
        paid=Count(
            "id",
            filter=Q(deposit__gte=F("owner__tax_amount"))
            & Q(status=PaymentAccountBase.Status.ACTIVE)
            | Q(deposit=0)
            & Q(status=PaymentAccountBase.Status.ACTIVE)
            & Q(last_paid__gte=timezone.now() - period),
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


def get_members_statistics(owner) -> MembersStatisticsSchema:
    # Determine the correct filter based on alliance system setting
    if isinstance(owner, CorporationOwner):
        members = Members.objects.filter(owner=owner).order_by("character_name")
    elif isinstance(owner, AllianceOwner):
        members = Members.objects.filter(
            owner__eve_corporation__alliance=owner.eve_alliance
        ).order_by("character_name")
    else:
        raise ValueError("Owner must be CorporationOwner or AllianceOwner")

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

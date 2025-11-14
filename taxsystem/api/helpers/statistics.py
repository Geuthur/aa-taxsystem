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
from taxsystem.models.tax import Members, OwnerAudit, Payments, PaymentSystem

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


def get_payments_statistics(
    owner: OwnerAudit, alliance: bool = False
) -> PaymentsStatisticsSchema:
    """Get payments statistics for an OwnerAudit."""
    # Determine the correct filter based on alliance system setting
    payments = (
        Payments.objects.filter(account__owner__alliance=owner.alliance)
        if alliance
        else Payments.objects.filter(account__owner=owner)
    )

    payments_counts = payments.aggregate(
        total=Count("id"),
        automatic=Count("id", filter=Q(reviser="System")),
        manual=Count("id", filter=~Q(reviser="System") & ~Q(reviser="")),
        pending=Count(
            "id",
            filter=Q(
                request_status__in=[
                    Payments.RequestStatus.PENDING,
                    Payments.RequestStatus.NEEDS_APPROVAL,
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
    owner: OwnerAudit, alliance: bool = False
) -> PaymentSystemStatisticsSchema:
    """Get payment system statistics for an OwnerAudit."""
    period = timezone.timedelta(days=owner.tax_period)

    # Determine the correct filter based on alliance system setting
    payment_system = (
        PaymentSystem.objects.filter(owner__alliance=owner.alliance)
        if alliance
        else PaymentSystem.objects.filter(owner=owner)
    )

    payment_system_counts = payment_system.exclude(
        status=PaymentSystem.Status.MISSING
    ).aggregate(
        users=Count("id"),
        active=Count("id", filter=Q(status=PaymentSystem.Status.ACTIVE)),
        inactive=Count("id", filter=Q(status=PaymentSystem.Status.INACTIVE)),
        deactivated=Count("id", filter=Q(status=PaymentSystem.Status.DEACTIVATED)),
        paid=Count(
            "id",
            filter=Q(deposit__gte=F("owner__tax_amount"))
            & Q(status=PaymentSystem.Status.ACTIVE)
            | Q(deposit=0)
            & Q(status=PaymentSystem.Status.ACTIVE)
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


def get_members_statistics(
    owner: OwnerAudit, alliance: bool = False
) -> MembersStatisticsSchema:
    # Determine the correct filter based on alliance system setting
    members = (
        Members.objects.filter(owner__alliance=owner.alliance)
        if alliance
        else Members.objects.filter(owner=owner)
    )

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

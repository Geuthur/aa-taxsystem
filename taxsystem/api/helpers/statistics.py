# Third Party
from ninja import Schema

# Django
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.models.tax import Members, OwnerAudit, Payments, PaymentSystem


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


def _create_statistics(owner: OwnerAudit):
    """Helper to get statistics dictionary for an OwnerAudit."""
    # Get time period for tax payments
    period = timezone.timedelta(days=owner.tax_period)

    # Get Payments counts
    payments_counts = Payments.objects.filter(account__owner=owner).aggregate(
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

    response_payments = PaymentsStatisticsSchema(
        payments_count=payments_counts["total"],
        payments_pending=payments_counts["pending"],
        payments_automatic=payments_counts["automatic"],
        payments_manual=payments_counts["manual"],
    )

    # Get Payment System counts
    payment_system_counts = (
        PaymentSystem.objects.filter(
            owner=owner,
            user__profile__main_character__isnull=False,
        )
        .exclude(status=PaymentSystem.Status.MISSING)
        .aggregate(
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
    )
    unpaid = payment_system_counts["active"] - payment_system_counts["paid"]

    response_payment_account = PaymentSystemStatisticsSchema(
        ps_count=payment_system_counts["users"],
        ps_count_active=payment_system_counts["active"],
        ps_count_inactive=payment_system_counts["inactive"],
        ps_count_deactivated=payment_system_counts["deactivated"],
        ps_count_paid=payment_system_counts["paid"],
        ps_count_unpaid=unpaid,
    )

    # Get Members counts
    members_count = Members.objects.filter(owner=owner).aggregate(
        total=Count("character_id"),
        unregistered=Count("character_id", filter=Q(status=Members.States.NOACCOUNT)),
        alts=Count("character_id", filter=Q(status=Members.States.IS_ALT)),
        mains=Count("character_id", filter=Q(status=Members.States.ACTIVE)),
    )

    response_members = MembersStatisticsSchema(
        members_count=members_count["total"],
        members_unregistered=members_count["unregistered"],
        members_alts=members_count["alts"],
        members_mains=members_count["mains"],
    )

    return StatisticsResponse(
        owner_id=owner.corporation.corporation_id,
        owner_name=owner.corporation.corporation_name,
        payment_system=response_payment_account,
        payments=response_payments,
        members=response_members,
    )

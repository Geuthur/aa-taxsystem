from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Count, Q
from django.utils.translation import gettext as _

from taxsystem.models.tax import Members, OwnerAudit, Payments, PaymentSystem
from taxsystem.models.wallet import CorporationWalletDivision


def _get_divisions_dict(divisions: CorporationWalletDivision):
    divisions_dict = {}
    total_balance = 0
    for i, division in enumerate(divisions, start=1):
        division_name = division.name if division.name else f"{i}. {_('Division')}"
        division_balance = intcomma(division.balance)
        divisions_dict[division_name] = {
            "name": division_name,
            "balance": division_balance,
        }
        total_balance += division.balance

    divisions_dict["total"] = {
        "name": _("Total"),
        "balance": intcomma(total_balance),
    }

    return divisions_dict


def _get_statistics_dict(corp: OwnerAudit):
    payments_counts = Payments.objects.filter(account__corporation=corp).aggregate(
        total=Count("id"),
        automatic=Count("id", filter=Q(reviser="System")),
        manual=Count("id", filter=~Q(reviser="System") & ~Q(reviser="")),
        pending=Count(
            "id",
            filter=Q(
                status__in=[
                    Payments.Status.PENDING,
                    Payments.Status.NEEDS_APPROVAL,
                ]
            ),
        ),
    )

    payment_system_counts = PaymentSystem.objects.filter(corporation=corp).aggregate(
        users=Count("id"),
        active=Count("id", filter=Q(status=PaymentSystem.Status.ACTIVE)),
        inactive=Count("id", filter=Q(status=PaymentSystem.Status.INACTIVE)),
        deactivated=Count("id", filter=Q(status=PaymentSystem.Status.DEACTIVATED)),
    )

    members_count = Members.objects.filter(corporation=corp).aggregate(
        total=Count("character_id"),
        unregistered=Count("character_id", filter=Q(status=Members.States.NOACCOUNT)),
        alts=Count("character_id", filter=Q(status=Members.States.IS_ALT)),
        mains=Count("character_id", filter=Q(status=Members.States.ACTIVE)),
    )

    return {
        # Payment System
        "payment_users": payment_system_counts["users"],
        "payment_users_active": payment_system_counts["active"],
        "payment_users_inactive": payment_system_counts["inactive"],
        "payment_users_deactivated": payment_system_counts["deactivated"],
        "payment_users_paid": 0,
        "payment_users_unpaid": 0,
        # Payments
        "payments": payments_counts["total"],
        "payments_pending": payments_counts["pending"],
        "payments_auto": payments_counts["automatic"],
        "payments_manually": payments_counts["manual"],
        # Members
        "members": members_count["total"],
        "members_unregistered": members_count["unregistered"],
        "members_alts": members_count["alts"],
        "members_mains": members_count["mains"],
    }

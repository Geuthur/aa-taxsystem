"""Tax Helpers"""

from django.utils import timezone

from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import (
    OwnerAudit,
    Payments,
    PaymentSystem,
)
from taxsystem.models.wallet import CorporationWalletJournalEntry

logger = get_extension_logger(__name__)


# pylint: disable=too-many-locals
def update_corporation_payments_filter(corp_id):
    """Update corporation members"""
    audit_corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)

    logger.debug(
        "Updating payments for: %s",
        audit_corp.corporation.corporation_name,
    )

    payment_users = PaymentSystem.objects.filter(corporation=audit_corp)

    if not payment_users:
        return ("No Payment Users for %s", audit_corp.corporation.corporation_name)

    users = {}

    for user in payment_users:
        alts = user.get_alt_ids()
        users[user.user] = alts

    journal = CorporationWalletJournalEntry.objects.filter(
        division__corporation=audit_corp, ref_type__in=["player_donation"]
    ).order_by("-date")

    _current_entry_ids = set(
        Payments.objects.filter(payment_user__corporation=audit_corp).values_list(
            "entry_id", flat=True
        )
    )

    items = []
    for entry in journal:
        # Skip if already processed
        if entry.entry_id in _current_entry_ids:
            continue
        for user, alts in users.items():
            if entry.first_party_id in alts:
                payment_item = Payments(
                    entry_id=entry.entry_id,
                    name=user.name,
                    payment_user=user,
                    date=timezone.now(),
                    amount=entry.amount,
                    payment_status=Payments.States.PENDING,
                    payment_date=entry.date,
                    reason=entry.reason,
                    approved=Payments.Approval.PENDDING,
                )
                items.append(payment_item)

    Payments.objects.bulk_create(items, ignore_conflicts=True)

    logger.debug(
        "Finished %s Payments for %s",
        len(items),
        audit_corp.corporation.corporation_name,
    )

    return ("Finished Members for %s", audit_corp.corporation.corporation_name)

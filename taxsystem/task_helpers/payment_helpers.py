"""Tax Helpers"""

from django.db import transaction
from django.utils import timezone

from taxsystem.hooks import get_extension_logger
from taxsystem.models.filters import SmartGroup
from taxsystem.models.tax import (
    OwnerAudit,
    Payments,
    PaymentSystem,
)
from taxsystem.models.wallet import CorporationWalletJournalEntry

logger = get_extension_logger(__name__)


# pylint: disable=too-many-locals
def update_corporation_payments(corp_id):
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
        users[user] = alts

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
            if entry.first_party.id in alts:
                payment_item = Payments(
                    entry_id=entry.entry_id,
                    name=user.name,
                    payment_user=user,
                    date=timezone.now(),
                    amount=entry.amount,
                    payment_status=Payments.States.PENDING,
                    payment_date=entry.date,
                    reason=entry.reason,
                    approved=Payments.Approval.PENDING,
                )
                items.append(payment_item)

    Payments.objects.bulk_create(items, ignore_conflicts=True)

    audit_corp.last_update_payments = timezone.now()
    audit_corp.save()

    logger.debug(
        "Finished %s Payments for %s",
        len(items),
        audit_corp.corporation.corporation_name,
    )

    return ("Finished Payments for %s", audit_corp.corporation.corporation_name)


def update_corporation_payments_filter(corp_id, runs=0):
    """Update Filtered Payments for Corporation"""
    audit_corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)

    logger.debug(
        "Updating payment system for: %s",
        audit_corp.corporation.corporation_name,
    )

    payments = Payments.objects.filter(
        payment_user__corporation=audit_corp, payment_status=Payments.States.PENDING
    )

    _current_payment_ids = set(payments.values_list("id", flat=True))
    _automatic_payment_ids = []

    # Check for any automatic payments
    try:
        filters = SmartGroup.objects.get(corporation=audit_corp)
        if filters:
            payments = filters.filter(payments)
            for payment in payments:
                if payment.payment_status == Payments.States.PENDING:
                    # Ensure all transers are processed in a single transaction
                    with transaction.atomic():
                        payment.payment_status = Payments.States.PAID
                        payment.approved = Payments.Approval.APPROVED
                        payment.system = Payments.Systems.AUTOMATIC

                        # Update payment pool for user
                        PaymentSystem.objects.filter(
                            corporation=audit_corp, user=payment.payment_user.user
                        ).update(
                            payment_pool=payment.payment_user.payment_pool
                            + payment.amount
                        )

                        payment.save()
                        runs = runs + 1
                        _automatic_payment_ids.append(payment.pk)
    except SmartGroup.DoesNotExist:
        pass

    # Check for any payments that need approval
    needs_approval = _current_payment_ids - set(_automatic_payment_ids)
    approvals = Payments.objects.filter(
        id__in=needs_approval, payment_status=Payments.States.PENDING
    )

    for payment in approvals:
        payment.payment_status = Payments.States.NEEDS_APPROVAL
        payment.approved = Payments.Approval.PENDING
        payment.save()
        runs = runs + 1

    # Check approved payments
    approved = Payments.objects.filter(
        payment_user__corporation=audit_corp,
        payment_status=Payments.States.NEEDS_APPROVAL,
        approved=Payments.Approval.APPROVED,
    )

    for payment in approved:
        with transaction.atomic():
            payment.payment_status = Payments.States.PAID
            PaymentSystem.objects.filter(
                corporation=audit_corp, user=payment.payment_user.user
            ).update(payment_pool=payment.payment_user.payment_pool + payment.amount)
            payment.save()
            runs = runs + 1

    # Check Payment Period
    payday = PaymentSystem.objects.filter(
        corporation=audit_corp, status=PaymentSystem.States.ACTIVE
    )

    for user in payday:
        if user.last_paid is None:
            # First Period is free
            user.last_paid = timezone.now()
        if timezone.now() - user.last_paid >= timezone.timedelta(
            days=audit_corp.tax_period
        ):
            user.payment_pool -= audit_corp.tax_amount
            user.last_paid = timezone.now()
            runs = runs + 1
        user.save()

    audit_corp.last_update_payment_system = timezone.now()
    audit_corp.save()

    logger.debug(
        "Finished %s: Payment System entrys for %s",
        runs,
        audit_corp.corporation.corporation_name,
    )

    return ("Finished Payment System for %s", audit_corp.corporation.corporation_name)

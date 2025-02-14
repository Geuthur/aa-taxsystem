"""Tax Helpers"""

from django.db import transaction
from django.utils import timezone

from taxsystem.hooks import get_extension_logger
from taxsystem.models.filters import SmartGroup
from taxsystem.models.logs import Logs
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

    accounts = PaymentSystem.objects.filter(corporation=audit_corp)

    if not accounts:
        return ("No Payment Users for %s", audit_corp.corporation.corporation_name)

    users = {}

    for user in accounts:
        alts = user.get_alt_ids()
        users[user] = alts

    journal = CorporationWalletJournalEntry.objects.filter(
        division__corporation=audit_corp, ref_type__in=["player_donation"]
    ).order_by("-date")

    _current_entry_ids = set(
        Payments.objects.filter(account__corporation=audit_corp).values_list(
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
                    account=user,
                    amount=entry.amount,
                    status=Payments.Status.PENDING,
                    request_status=Payments.RequestStatus.PENDING,
                    date=entry.date,
                    reason=entry.reason,
                )
                items.append(payment_item)

    payments = Payments.objects.bulk_create(items, ignore_conflicts=True)

    for payment in payments:
        Logs(
            user=payment.account.user.user,
            payment=payment,
            action=Logs.Actions.PAYMENT_ADDED,
            new_status=Payments.RequestStatus.PENDING,
        ).save()

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
        account__corporation=audit_corp, status=Payments.Status.PENDING
    )

    _current_payment_ids = set(payments.values_list("id", flat=True))
    _automatic_payment_ids = []

    # Check for any automatic payments
    try:
        filters = SmartGroup.objects.get(corporation=audit_corp)
        if filters:
            payments = filters.filter(payments)
            for payment in payments:
                if payment.status == Payments.Status.PENDING:
                    # Ensure all transers are processed in a single transaction
                    with transaction.atomic():
                        payment.status = Payments.Status.PAID
                        payment.request_status = Payments.RequestStatus.APPROVED
                        payment.reviser = "System"

                        # Update payment pool for user
                        PaymentSystem.objects.filter(
                            corporation=audit_corp, user=payment.account.user
                        ).update(deposit=payment.account.deposit + payment.amount)

                        payment.save()

                        Logs(
                            user=payment.account.user.user,
                            payment=payment,
                            action=Logs.Actions.STATUS_CHANGE,
                            new_status=Payments.RequestStatus.APPROVED,
                        ).save()

                        runs = runs + 1
                        _automatic_payment_ids.append(payment.pk)
    except SmartGroup.DoesNotExist:
        pass

    # Check for any payments that need approval
    needs_approval = _current_payment_ids - set(_automatic_payment_ids)
    approvals = Payments.objects.filter(
        id__in=needs_approval, status=Payments.Status.PENDING
    )

    for payment in approvals:
        payment.status = Payments.Status.NEEDS_APPROVAL
        payment.request_status = Payments.RequestStatus.PENDING
        payment.save()

        Logs(
            user=payment.account.user.user,
            payment=payment,
            action=Logs.Actions.STATUS_CHANGE,
            new_status=Payments.RequestStatus.PENDING,
        ).save()

        runs = runs + 1

    # Check approved payments
    approved = Payments.objects.filter(
        account__corporation=audit_corp,
        status=Payments.Status.NEEDS_APPROVAL,
        request_status=Payments.RequestStatus.APPROVED,
    )

    for payment in approved:
        with transaction.atomic():
            payment.status = Payments.Status.PAID
            PaymentSystem.objects.filter(
                corporation=audit_corp, user=payment.account.user
            ).update(deposit=payment.account.deposit + payment.amount)
            payment.save()

            Logs(
                user=payment.account.user.user,
                payment=payment,
                action=Logs.Actions.STATUS_CHANGE,
                new_status=Payments.RequestStatus.APPROVED,
            ).save()

            runs = runs + 1

    # Check Payment Period
    payday = PaymentSystem.objects.filter(
        corporation=audit_corp, status=PaymentSystem.Status.ACTIVE
    )

    for user in payday:
        if user.last_paid is None:
            # First Period is free
            user.last_paid = timezone.now()
        if timezone.now() - user.last_paid >= timezone.timedelta(
            days=audit_corp.tax_period
        ):
            user.deposit -= audit_corp.tax_amount
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

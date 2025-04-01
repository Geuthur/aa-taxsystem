"""App Tasks"""

import datetime

from celery import chain, shared_task

from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

from taxsystem import app_settings
from taxsystem.decorators import when_esi_is_available
from taxsystem.models.tax import OwnerAudit
from taxsystem.task_helpers.payment_helpers import (
    update_corporation_payments,
    update_corporation_payments_filter,
    update_payday,
)
from taxsystem.task_helpers.tax_helpers import update_corporation_members
from taxsystem.task_helpers.wallet_helpers import update_corporation_wallet_division

logger = get_extension_logger(__name__)

MAX_RETRIES_DEFAULT = 3

# Default params for all tasks.
TASK_DEFAULTS = {
    "time_limit": app_settings.TAXSYSTEM_TASKS_TIME_LIMIT,
    "max_retries": MAX_RETRIES_DEFAULT,
}

# Default params for tasks that need run once only.
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **{"base": QueueOnce}}

_update_taxsystem_params = {
    **TASK_DEFAULTS_ONCE,
    **{"once": {"keys": ["corp_id"], "graceful": True}},
}


@shared_task
@when_esi_is_available
def update_all_taxsytem(runs: int = 0):
    corps = OwnerAudit.objects.select_related("corporation").all()
    for corp in corps:
        update_corp.apply_async(args=[corp.corporation.corporation_id])
        runs = runs + 1


@shared_task(bind=True, base=QueueOnce)
def update_corp(self, corp_id, force_refresh=False):  # pylint: disable=unused-argument
    class SkipDates:
        """Skip Dates for Updates"""

        wallet = timezone.now() - datetime.timedelta(
            hours=app_settings.TAXSYSTEM_CORP_WALLET_SKIP_DATE
        )
        members = timezone.now() - datetime.timedelta(
            hours=app_settings.TAXSYSTEM_CORP_MEMBERS_SKIP_DATE
        )
        payments = timezone.now() - datetime.timedelta(
            hours=app_settings.TAXSYSTEM_CORP_PAYMENTS_SKIP_DATE
        )
        payment_system = timezone.now() - datetime.timedelta(
            hours=app_settings.TAXSYSTEM_CORP_PAYMENT_SYSTEM_SKIP_DATE
        )
        payment_payday = timezone.now() - datetime.timedelta(
            hours=app_settings.TAXSYSTEM_CORP_PAYMENT_PAYDAY_SKIP_DATE
        )

    corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)
    logger.debug("Processing Audit Updates for %s", corp.corporation.corporation_name)

    que = []
    mindt = timezone.now() - datetime.timedelta(days=app_settings.TAXSYSTEM_STALE_TIME)
    priority = 7

    if (corp.last_update_wallet or mindt) <= SkipDates.wallet or force_refresh:
        que.append(
            update_corp_wallet.si(corp_id, force_refresh=force_refresh).set(
                priority=priority
            )
        )
    if (corp.last_update_members or mindt) <= SkipDates.members or force_refresh:
        que.append(
            update_corp_members.si(corp_id, force_refresh=force_refresh).set(
                priority=priority
            )
        )
    if (corp.last_update_payments or mindt) <= SkipDates.payments or force_refresh:
        que.append(update_corp_payments.si(corp_id).set(priority=priority))
    if (
        corp.last_update_payment_system or mindt
    ) <= SkipDates.payment_system or force_refresh:
        que.append(update_corp_payments_filter.si(corp_id).set(priority=priority))
    if (corp.last_update_payday or mindt) <= SkipDates.payment_payday or force_refresh:
        que.append(update_corp_payday.si(corp_id).set(priority=priority))

    chain(que).apply_async()
    logger.debug("Queued Updates for %s", corp.corporation.corporation_name)


@shared_task(**_update_taxsystem_params)
def update_corp_wallet(
    corp_id,
    force_refresh=False,
):
    return update_corporation_wallet_division(corp_id, force_refresh=force_refresh)


@shared_task(**_update_taxsystem_params)
def update_corp_members(
    corp_id,
    force_refresh=False,
):
    return update_corporation_members(corp_id, force_refresh=force_refresh)


@shared_task(**_update_taxsystem_params)
def update_corp_payments(
    corp_id,
):
    return update_corporation_payments(corp_id)


@shared_task(**_update_taxsystem_params)
def update_corp_payments_filter(
    corp_id,
):
    return update_corporation_payments_filter(corp_id)


@shared_task(**_update_taxsystem_params)
def update_corp_payday(
    corp_id,
):
    return update_payday(corp_id)

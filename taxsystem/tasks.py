"""App Tasks"""

import datetime

from celery import shared_task

from django.utils import timezone

from allianceauth.services.tasks import QueueOnce

from taxsystem import app_settings
from taxsystem.decorators import when_esi_is_available
from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import OwnerAudit
from taxsystem.task_helpers.general_helpers import enqueue_next_task, no_fail_chain
from taxsystem.task_helpers.payment_helpers import update_corporation_payments_filter
from taxsystem.task_helpers.tax_helpers import update_corporation_members
from taxsystem.task_helpers.wallet_helpers import update_corporation_wallet_division

logger = get_extension_logger(__name__)


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
            days=app_settings.TAXSYSTEM_CORP_MEMBERS_SKIP_DATE
        )

    corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)
    logger.debug("Processing Audit Updates for %s", corp.corporation.corporation_name)

    que = []
    mindt = timezone.now() - datetime.timedelta(days=90)

    if (corp.last_update_wallet or mindt) <= SkipDates.wallet or force_refresh:
        que.append(update_corp_wallet.si(corp_id, force_refresh=force_refresh))
    if (corp.last_update_members or mindt) <= SkipDates.members or force_refresh:
        que.append(update_corp_members.si(corp_id, force_refresh=force_refresh))
    if (corp.last_update_payments or mindt) <= SkipDates.wallet or force_refresh:
        que.append(update_payments_filter.si(corp_id))

    enqueue_next_task(que)

    logger.debug("Queued Updates for %s", corp.corporation.corporation_name)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["corp_id"]},
    name="taxsystem.tasks.update_corp_wallet",
)
@no_fail_chain
def update_corp_wallet(
    self, corp_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_corporation_wallet_division(corp_id, force_refresh=force_refresh)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["corp_id"]},
    name="taxsystem.tasks.update_corp_members",
)
@no_fail_chain
def update_corp_members(
    self, corp_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_corporation_members(corp_id, force_refresh=force_refresh)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["corp_id"]},
    name="taxsystem.tasks.update_payments_filter",
)
@no_fail_chain
def update_payments_filter(
    self, corp_id, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_corporation_payments_filter(corp_id)

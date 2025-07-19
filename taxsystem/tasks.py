"""App Tasks"""

# Standard Library
import inspect
from collections.abc import Callable

# Third Party
from celery import chain, shared_task

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, app_settings
from taxsystem.decorators import when_esi_is_available
from taxsystem.models.tax import OwnerAudit

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

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
    **{"once": {"keys": ["owner_pk", "force_refresh"], "graceful": True}},
}


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_taxsytem(runs: int = 0, force_refresh: bool = False):
    """Update all taxsystem data"""
    corporations = OwnerAudit.objects.select_related("corporation").filter(active=1)
    for corporation in corporations:
        update_corporation.apply_async(
            args=[corporation.pk], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    logger.info("Queued %s OwnerAudit Tasks", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_corporation(owner_pk, force_refresh=False):
    """Update a corporation"""
    owner = OwnerAudit.objects.prefetch_related("ts_update_status").get(pk=owner_pk)

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(owner.corporation.corporation_name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        owner.reset_has_token_error()

    needs_update = owner.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", owner.corporation.corporation_name)
        return

    sections = owner.UpdateSection.get_sections()

    for section in sections:
        # Skip sections that are not in the needs_update list
        if not force_refresh and not needs_update.for_section(section):
            logger.debug(
                "No updates needed for %s (%s)",
                owner.corporation.corporation_name,
                section,
            )
            continue

        task_name = f"update_owner_{section}"
        task = globals().get(task_name)
        que.append(
            task.si(owner.pk, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        owner.corporation.corporation_name,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_division_names(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.DIVISION_NAMES,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_division(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.DIVISION,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_wallet(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.WALLET,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_members(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.MEMBERS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_payments(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.PAYMENTS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_payment_system(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.PAYMENT_SYSTEM,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
@when_esi_is_available
def update_owner_payday(owner_pk: int, force_refresh: bool):
    return _update_owner_section(
        owner_pk,
        section=OwnerAudit.UpdateSection.PAYDAY,
        force_refresh=force_refresh,
    )


def _update_owner_section(owner_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the character audit."""
    section = OwnerAudit.UpdateSection(section)
    corporation = OwnerAudit.objects.get(pk=owner_pk)
    logger.debug(
        "Updating %s for %s", section.label, corporation.corporation.corporation_name
    )

    corporation.reset_update_status(section)

    method: Callable = getattr(corporation, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    result = corporation.perform_update_status(section, method, **kwargs)
    corporation.update_section_log(
        section, is_success=True, is_updated=result.is_updated
    )


@shared_task(**TASK_DEFAULTS_ONCE)
def clear_all_etags():
    logger.debug("Clearing all etags")
    try:
        # Third Party
        # pylint: disable=import-outside-toplevel
        from django_redis import get_redis_connection

        _client = get_redis_connection("default")
    except (NotImplementedError, ModuleNotFoundError):
        # Django
        # pylint: disable=import-outside-toplevel
        from django.core.cache import caches

        default_cache = caches["default"]
        _client = default_cache.get_master_client()
    keys = _client.keys(":?:taxsystem-*")
    if keys:
        deleted = _client.delete(*keys)
        logger.info("Deleted %s etag keys", deleted)
    else:
        logger.info("No etag keys to delete")

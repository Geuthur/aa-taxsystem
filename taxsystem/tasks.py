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
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.models.general import AllianceUpdateSection, CorporationUpdateSection

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
    corporations: list[CorporationOwner] = CorporationOwner.objects.select_related(
        "eve_corporation"
    ).filter(active=1)
    alliances: list[AllianceOwner] = AllianceOwner.objects.select_related(
        "eve_alliance"
    ).filter(active=1)
    # Queue tasks for all corporations
    for corporation in corporations:
        update_corporation.apply_async(
            args=[corporation.pk], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    # Queue tasks for all alliances
    for alliance in alliances:
        update_alliance.apply_async(
            args=[alliance.pk], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    logger.info("Queued %s Owner Tasks", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_corporation(owner_pk, force_refresh=False):
    """Update a corporation"""
    owner: CorporationOwner = CorporationOwner.objects.prefetch_related(
        "ts_corporation_update_status"
    ).get(pk=owner_pk)

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(owner.name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        owner.reset_has_token_error()

    needs_update = owner.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", owner.name)
        return

    sections = CorporationUpdateSection.get_sections()

    for section in sections:
        # Skip sections that are not in the needs_update list
        if not force_refresh and not needs_update.for_section(section):
            logger.debug(
                "No updates needed for %s (%s)",
                owner.name,
                section,
            )
            continue

        task_name = f"update_corp_{section}"
        task = globals().get(task_name)
        que.append(
            task.si(owner.pk, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        owner.name,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_division_names(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.DIVISION_NAMES,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_division(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.DIVISION,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_wallet(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.WALLET,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_members(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.MEMBERS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_payments(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.PAYMENTS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_payment_system(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.PAYMENT_SYSTEM,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_corp_payday(owner_pk: int, force_refresh: bool):
    return _update_corp_section(
        owner_pk,
        section=CorporationUpdateSection.PAYDAY,
        force_refresh=force_refresh,
    )


def _update_corp_section(owner_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the corporation."""
    section = CorporationUpdateSection(section)
    corporation: CorporationOwner = CorporationOwner.objects.get(pk=owner_pk)
    logger.debug("Updating %s for %s", section.label, corporation.name)

    corporation.reset_update_status(section)

    method: Callable = getattr(corporation, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    result = corporation.perform_update_status(section, method, **kwargs)
    corporation.update_section_log(section, result)


# Alliance Tasks


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_alliance(owner_pk, force_refresh=False):
    """Update an alliance"""
    owner: AllianceOwner = AllianceOwner.objects.prefetch_related(
        "ts_alliance_update_status"
    ).get(pk=owner_pk)

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(owner.name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        owner.reset_has_token_error()

    needs_update = owner.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", owner.name)
        return

    sections = AllianceUpdateSection.get_sections()

    for section in sections:
        # Skip sections that are not in the needs_update list
        if not force_refresh and not needs_update.for_section(section):
            logger.debug(
                "No updates needed for %s (%s)",
                owner.name,
                section,
            )
            continue

        task_name = f"update_ally_{section}"
        task = globals().get(task_name)
        que.append(
            task.si(owner.pk, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        owner.name,
    )


@shared_task(**_update_taxsystem_params)
def update_ally_payments(owner_pk: int, force_refresh: bool):
    return _update_ally_section(
        owner_pk,
        section=AllianceUpdateSection.PAYMENTS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_ally_payment_system(owner_pk: int, force_refresh: bool):
    return _update_ally_section(
        owner_pk,
        section=AllianceUpdateSection.PAYMENT_SYSTEM,
        force_refresh=force_refresh,
    )


@shared_task(**_update_taxsystem_params)
def update_ally_payday(owner_pk: int, force_refresh: bool):
    return _update_ally_section(
        owner_pk,
        section=AllianceUpdateSection.PAYDAY,
        force_refresh=force_refresh,
    )


def _update_ally_section(owner_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the alliance."""
    section = AllianceUpdateSection(section)
    alliance: AllianceOwner = AllianceOwner.objects.get(pk=owner_pk)
    logger.debug("Updating %s for %s", section.label, alliance.name)
    alliance.reset_update_status(section)

    method: Callable = getattr(alliance, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    result = alliance.perform_update_status(section, method, **kwargs)
    alliance.update_section_log(section, result)

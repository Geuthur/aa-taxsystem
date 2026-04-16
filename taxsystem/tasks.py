"""App Tasks"""

# Standard Library
import inspect
from collections.abc import Callable
from urllib.parse import urljoin

# Third Party
from celery import Task, chain, shared_task

# Django
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# AA TaxSystem
from taxsystem import __title__, app_settings
from taxsystem.helpers.discord import send_user_notification
from taxsystem.models.alliance import AllianceOwner, AlliancePaymentAccount
from taxsystem.models.corporation import CorporationOwner, CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    AllianceUpdateSection,
    CorporationUpdateSection,
)
from taxsystem.providers import AppLogger, retry_task_on_esi_error

logger = AppLogger(get_extension_logger(__name__), __title__)

MAX_RETRIES_DEFAULT = 3

# Default params for all tasks.
TASK_DEFAULTS = {
    "time_limit": app_settings.TAXSYSTEM_TASKS_TIME_LIMIT,
    "max_retries": MAX_RETRIES_DEFAULT,
}

# Default params for tasks that need bind=True and run once only.
TASK_DEFAULTS_BIND_ONCE = {**TASK_DEFAULTS, **{"bind": True, "base": QueueOnce}}

# Default params for tasks that need run once only.
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **{"base": QueueOnce}}

TASK_DEFAULTS_BIND_ONCE_OWNER = {
    **TASK_DEFAULTS_BIND_ONCE,
    **{"once": {"keys": ["owner_eve_id"], "graceful": True}},
}


@shared_task(**TASK_DEFAULTS_ONCE)
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
            args=[corporation.eve_id], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    # Queue tasks for all alliances
    for alliance in alliances:
        update_alliance.apply_async(
            args=[alliance.eve_id], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    logger.info("Queued %s Owner Tasks", runs)


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corporation(
    self: Task,  # pylint: disable=unused-argument
    owner_eve_id: int,
    force_refresh: bool = False,
) -> bool:
    """Update a corporation"""
    owner: CorporationOwner = CorporationOwner.objects.prefetch_related(
        "ts_corporation_update_status"
    ).get(eve_corporation__corporation_id=owner_eve_id)

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(owner.name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        owner.update_manager.reset_has_token_error()

    needs_update = owner.update_manager.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", owner.name)
        return False

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
            task.si(owner.eve_id, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        owner.name,
    )
    return True


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_division_names(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.DIVISION_NAMES,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_divisions(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.DIVISIONS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_wallet(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.WALLET,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_members(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.MEMBERS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_payments(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.PAYMENTS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_tax_accounts(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.TAX_ACCOUNTS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_corp_deadlines(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_corp_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=CorporationUpdateSection.DEADLINES,
        force_refresh=force_refresh,
    )


def _update_corp_section(
    task: Task, owner_eve_id: int, section: str, force_refresh: bool
):
    """Update a specific section of the corporation."""
    section = CorporationUpdateSection(section)
    owner = CorporationOwner.objects.get(eve_corporation__corporation_id=owner_eve_id)
    logger.debug("Updating %s for %s", section.label, owner.name)

    owner.update_manager.reset_update_status(section)

    method: Callable = getattr(owner, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    # Perform the update with the retry context manager
    with retry_task_on_esi_error(task):
        result = owner.update_manager.perform_update_status(section, method, **kwargs)
    owner.update_manager.update_section_log(section, result)


# Alliance Tasks


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_alliance(
    self: Task,  # pylint: disable=unused-argument
    owner_eve_id: int,
    force_refresh: bool = False,
) -> bool:
    """Update an alliance"""
    owner: AllianceOwner = AllianceOwner.objects.prefetch_related(
        "ts_alliance_update_status"
    ).get(eve_alliance__alliance_id=owner_eve_id)

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(owner.name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        owner.update_manager.reset_has_token_error()

    needs_update = owner.update_manager.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", owner.name)
        return False

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
            task.si(owner.eve_id, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        owner.name,
    )
    return True


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_ally_payments(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_ally_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=AllianceUpdateSection.PAYMENTS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_ally_tax_accounts(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_ally_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=AllianceUpdateSection.TAX_ACCOUNTS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def update_ally_deadlines(self: Task, owner_eve_id: int, force_refresh: bool):
    return _update_ally_section(
        task=self,
        owner_eve_id=owner_eve_id,
        section=AllianceUpdateSection.DEADLINES,
        force_refresh=force_refresh,
    )


def _update_ally_section(
    task: Task, owner_eve_id: int, section: str, force_refresh: bool
):
    """Update a specific section of the alliance."""
    section = AllianceUpdateSection(section)
    alliance = AllianceOwner.objects.get(eve_alliance__alliance_id=owner_eve_id)
    logger.debug("Updating %s for %s", section.label, alliance.name)
    alliance.update_manager.reset_update_status(section)

    method: Callable = getattr(alliance, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    # Perform the update with the retry context manager
    with retry_task_on_esi_error(task):
        result = alliance.update_manager.perform_update_status(
            section, method, **kwargs
        )
    alliance.update_manager.update_section_log(section, result)


@shared_task(**TASK_DEFAULTS_ONCE)
def check_account_deposit(runs: int = 0):
    """Check if any accounts have not paid and send notifications if needed."""
    alliances = AllianceOwner.objects.filter(active=1)
    corporations = CorporationOwner.objects.filter(active=1)

    # Check alliance users
    for alliance in alliances:
        _send_alliance_notification.apply_async(
            kwargs={"owner_eve_id": alliance.eve_alliance.alliance_id}
        )
        runs = runs + 1

    # Check corporation users
    for corporation in corporations:
        _send_corporation_notification.apply_async(
            kwargs={"owner_eve_id": corporation.eve_corporation.corporation_id}
        )
        runs = runs + 1
    logger.info("Queued %s notification tasks for overdue payments", runs)


@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def _send_alliance_notification(
    self: Task, owner_eve_id: int, runs: int = 0
):  # pylint: disable=unused-argument
    """Send a notification to an alliance."""
    accounts = AlliancePaymentAccount.objects.filter(
        owner__eve_alliance__alliance_id=owner_eve_id, status=AccountStatus.ACTIVE
    ).select_related("owner")

    owner_name = None
    for account in accounts:
        # Get the owner name from the first account, if not already set
        if owner_name is None:
            owner_name = account.owner.name
        # Only send a notification if the user has not been notified and has not paid
        if account.has_notified is False:
            if account.has_paid is False:
                url = urljoin(
                    settings.SITE_URL,
                    reverse(
                        "taxsystem:account",
                        args=[account.owner.eve_alliance.alliance_id],
                    ),
                )
                msg = account.owner.tax_message
                msg += f"\n__**`{account.owner.name}`**__: __**`{account.deposit}`**__ ISK.\n\n"
                msg += f"Account Overview: {url}"
                send_user_notification(
                    user_id=account.user_id,
                    title="Outstanding Payment Notification",
                    message=format_html(msg),
                    embed_message=True,
                    level="warning",
                )
            account.last_notification = timezone.now()
            account.save()
            runs = runs + 1
            logger.debug(
                "Sent notification to user %s for alliance %s",
                account.name,
                account.owner.name,
            )
    logger.info("Sent %s notifications for alliance %s", runs, owner_name)


# TODO Make this more efficient by only checking accounts that are overdue instead of all active accounts.
# This would require adding a next_notification field to the account model and indexing it for efficient querying.
@shared_task(**TASK_DEFAULTS_BIND_ONCE_OWNER)
def _send_corporation_notification(
    self: Task, owner_eve_id: int, runs: int = 0
):  # pylint: disable=unused-argument
    """Send a notification to a corporation."""
    accounts = CorporationPaymentAccount.objects.filter(
        owner__eve_corporation__corporation_id=owner_eve_id, status=AccountStatus.ACTIVE
    ).select_related("owner")

    owner_name = None
    for account in accounts:
        # Get the owner name from the first account, if not already set
        if owner_name is None:
            owner_name = account.owner.name
        # Only send a notification if the user has not been notified and has not paid
        if account.has_notified is False:
            if account.has_paid is False:
                url = urljoin(
                    settings.SITE_URL,
                    reverse(
                        "taxsystem:account",
                        args=[account.owner.eve_corporation.corporation_id],
                    ),
                )
                msg = account.owner.tax_message
                msg += f"\n__**`{account.owner.name}`**__: __**`{account.deposit}`**__ ISK.\n\n"
                msg += f"Account Overview: {url}"
                send_user_notification(
                    user_id=account.user_id,
                    title="Outstanding Payment Notification",
                    message=format_html(msg),
                    embed_message=True,
                    level="warning",
                )
                account.last_notification = timezone.now()
                account.save()
                runs = runs + 1
                logger.debug(
                    "Sent notification to user %s for corporation %s",
                    account.name,
                    account.owner.name,
                )
    logger.info("Sent %s notifications for corporation %s", runs, owner_name)

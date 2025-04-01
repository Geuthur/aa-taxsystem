"""Tax Helpers"""

from django.utils import timezone
from eveuniverse.models import EveEntity

from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

from taxsystem.models.tax import (
    Members,
    OwnerAudit,
    PaymentSystem,
)
from taxsystem.providers import esi
from taxsystem.task_helpers.etag_helpers import (
    HTTPGatewayTimeoutError,
    NotModifiedError,
    etag_results,
)
from taxsystem.task_helpers.general_helpers import get_corp_token

logger = get_extension_logger(__name__)


# pylint: disable=too-many-locals
def update_corporation_members(corp_id, force_refresh=False):
    """Update corporation members"""
    audit_corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)

    logger.debug(
        "Updating members for: %s",
        audit_corp.corporation.corporation_name,
    )

    req_scopes = [
        "esi-corporations.read_corporation_membership.v1",
        "esi-corporations.track_members.v1",
    ]

    req_roles = ["CEO", "Director"]

    token = get_corp_token(corp_id, req_scopes, req_roles)

    # pylint: disable=duplicate-code
    if not token:
        logger.debug("No valid token for: %s", audit_corp.corporation.corporation_name)
        return "No Tokens"

    # Check Payment Accounts

    check_payment_accounts(corp_id)

    try:
        _current_members_ids = set(
            Members.objects.filter(corporation=audit_corp).values_list(
                "character_id", flat=True
            )
        )
        members_ob = (
            esi.client.Corporation.get_corporations_corporation_id_membertracking(
                corporation_id=audit_corp.corporation.corporation_id,
            )
        )

        members = etag_results(members_ob, token, force_refresh=force_refresh)

        _esi_members_ids = [member.get("character_id") for member in members]
        _old_members = []
        _new_members = []

        characters = EveEntity.objects.bulk_resolve_names(_esi_members_ids)

        for member in members:
            character_id = member.get("character_id")
            joined = member.get("start_date")
            logon_date = member.get("logon_date")
            logged_off = member.get("logoff_date")
            character_name = characters.to_name(character_id)
            member_item = Members(
                corporation=audit_corp,
                character_id=character_id,
                character_name=character_name,
                joined=joined,
                logon=logon_date,
                logged_off=logged_off,
                status=Members.States.ACTIVE,
            )
            if character_id in _current_members_ids:
                _old_members.append(member_item)
            else:
                _new_members.append(member_item)

        # Set missing members
        old_member_ids = {member.character_id for member in _old_members}
        missing_members_ids = _current_members_ids - old_member_ids

        if missing_members_ids:
            Members.objects.filter(
                corporation=audit_corp, character_id__in=missing_members_ids
            ).update(status=Members.States.MISSING)
            logger.debug(
                "Marked %s missing members for: %s",
                len(missing_members_ids),
                audit_corp.corporation.corporation_name,
            )
        if _old_members:
            Members.objects.bulk_update(
                _old_members,
                ["character_name", "status", "logon", "logged_off"],
            )
            logger.debug(
                "Updated %s members for: %s",
                len(_old_members),
                audit_corp.corporation.corporation_name,
            )
        if _new_members:
            Members.objects.bulk_create(_new_members, ignore_conflicts=True)
            logger.debug(
                "Added %s new members for: %s",
                len(_new_members),
                audit_corp.corporation.corporation_name,
            )

        # Update payment accounts
        update_payment_accounts(corp_id, _esi_members_ids)

        logger.debug(
            "Corp %s - Old Members: %s, New Members: %s, Missing: %s",
            audit_corp.name,
            len(_old_members),
            len(_new_members),
            len(missing_members_ids),
        )
    except NotModifiedError:
        logger.debug(
            "No changes detected for: %s", audit_corp.corporation.corporation_name
        )
    except HTTPGatewayTimeoutError:
        logger.debug(
            "ESI Timeout skipping Members for: %s",
            audit_corp.corporation.corporation_name,
        )
        return (
            "ESI Timeout skipping Members for %s",
            audit_corp.corporation.corporation_name,
        )
    audit_corp.last_update_members = timezone.now()
    audit_corp.save()

    return ("Finished Members for %s", audit_corp.corporation.corporation_name)


def update_payment_accounts(corp_id: int, members_ids: list[int]):
    """Update payment accounts for a corporation."""
    audit_corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)

    logger.debug(
        "Updating Payment Accounts for: %s",
        audit_corp.corporation.corporation_name,
    )

    accounts = UserProfile.objects.filter(
        main_character__isnull=False,
        main_character__corporation_id=audit_corp.corporation.corporation_id,
    ).select_related(
        "user__profile__main_character",
        "main_character__character_ownership",
        "main_character__character_ownership__user__profile",
        "main_character__character_ownership__user__profile__main_character",
    )

    members = Members.objects.filter(corporation=audit_corp)

    if not accounts:
        logger.debug(
            "No valid accounts for: %s", audit_corp.corporation.corporation_name
        )
        return "No Accounts"

    items = []

    for account in accounts:
        alts = set(
            account.user.character_ownerships.all().values_list(
                "character__character_id", flat=True
            )
        )
        main = account.main_character

        relevant_alts = alts.intersection(members_ids)
        for alt in relevant_alts:
            members_ids.remove(alt)
            if alt != main.character_id:
                # Update the status of the member to alt
                members.filter(character_id=alt).update(status=Members.States.IS_ALT)
        try:
            existing_payment_system = PaymentSystem.objects.get(
                user=account.user, corporation=audit_corp
            )

            if existing_payment_system.status != PaymentSystem.Status.DEACTIVATED:
                existing_payment_system.status = PaymentSystem.Status.ACTIVE
                existing_payment_system.save()
        except PaymentSystem.DoesNotExist:
            items.append(
                PaymentSystem(
                    name=main.character_name,
                    corporation=audit_corp,
                    user=account.user,
                    status=PaymentSystem.Status.ACTIVE,
                )
            )

    if members_ids:
        # Mark members without accounts
        for member_id in members_ids:
            members.filter(character_id=member_id).update(
                status=Members.States.NOACCOUNT
            )

        logger.debug(
            "Marked %s members without accounts for: %s",
            len(members_ids),
            audit_corp.corporation.corporation_name,
        )

    if items:
        PaymentSystem.objects.bulk_create(items, ignore_conflicts=True)
        logger.debug(
            "Added %s new payment users for: %s",
            len(items),
            audit_corp.corporation.corporation_name,
        )
    else:
        logger.debug(
            "No new payment user for: %s",
            audit_corp.corporation.corporation_name,
        )

    return ("Finished payment system for %s", audit_corp.corporation.corporation_name)


def check_payment_accounts(corp_id: int):
    """Check payment accounts for a corporation."""
    audit_corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)

    logger.debug(
        "Checking Payment Accounts for: %s",
        audit_corp.corporation.corporation_name,
    )

    accounts = UserProfile.objects.filter(
        main_character__isnull=False,
    ).select_related(
        "user__profile__main_character",
        "main_character__character_ownership",
        "main_character__character_ownership__user__profile",
        "main_character__character_ownership__user__profile__main_character",
    )

    if not accounts:
        logger.debug(
            "No valid accounts for skipping Check: %s",
            audit_corp.corporation.corporation_name,
        )
        return "No Accounts"

    for account in accounts:
        main = account.main_character
        main_corporation = main.corporation

        try:
            payment_system = PaymentSystem.objects.get(
                user=account.user, corporation=audit_corp
            )
            payment_system_corp = payment_system.corporation.corporation
            # Check if the user is no longer in the same corporation
            if (
                not payment_system.is_missing
                and not payment_system_corp == main_corporation
            ):
                payment_system.status = PaymentSystem.Status.MISSING
                payment_system.save()
                logger.debug(
                    "User %s is no longer in Corp marked as Missing",
                    payment_system.name,
                )
            # Check if the user changed to a existing corporation Payment System
            elif payment_system.is_missing and payment_system_corp != main_corporation:
                try:
                    new_audit_corp = OwnerAudit.objects.get(
                        corporation=main_corporation
                    )
                    payment_system.corporation = new_audit_corp
                    payment_system.deposit = 0
                    payment_system.status = PaymentSystem.Status.ACTIVE
                    payment_system.last_paid = None
                    payment_system.save()
                    logger.debug(
                        "User %s is now in Corp %s",
                        payment_system.name,
                        new_audit_corp.corporation.corporation_name,
                    )
                except OwnerAudit.DoesNotExist:
                    continue
            elif payment_system.is_missing and payment_system_corp == main_corporation:
                payment_system.status = PaymentSystem.Status.ACTIVE
                payment_system.notice = None
                payment_system.deposit = 0
                payment_system.last_paid = None
                payment_system.save()
                logger.debug(
                    "User %s is back in Corp %s",
                    payment_system.name,
                    main_corporation.corporation_name,
                )
        except PaymentSystem.DoesNotExist:
            logger.debug(
                "No Payment System for %s - %s",
                account.user.username,
                audit_corp.corporation.corporation_name,
            )
            continue
    return (
        "Finished checking Payment Accounts for %s",
        audit_corp.corporation.corporation_name,
    )

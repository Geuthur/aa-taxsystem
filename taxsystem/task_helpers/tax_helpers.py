"""Tax Helpers"""

from django.utils import timezone
from eveuniverse.models import EveEntity

from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import (
    Members,
    OwnerAudit,
)
from taxsystem.providers import esi
from taxsystem.task_helpers.etag_helpers import NotModifiedError, etag_results
from taxsystem.task_helpers.general_helpers import get_corp_token

logger = get_extension_logger(__name__)


# pylint: disable=too-many-locals
def update_corporation_members(corp_id, force_refresh=False):
    audit_corp = OwnerAudit.objects.get(corporation__corporation_id=corp_id)

    logger.debug(
        "Updating members for: %s",
        audit_corp.corporation.corporation_name,
    )

    req_scopes = [
        "esi-corporations.read_corporation_membership.v1",
        "esi-corporations.read_titles.v1",
    ]
    req_roles = ["CEO", "Director"]

    token = get_corp_token(corp_id, req_scopes, req_roles)

    # pylint: disable=duplicate-code
    if not token:
        logger.debug("No valid token for: %s", audit_corp.corporation.corporation_name)
        return "No Tokens"

    try:
        _current_members_ids = set(
            Members.objects.filter(audit=audit_corp).values_list(
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
            character_name = characters.to_name(character_id)
            member_item = Members(
                audit=audit_corp,
                character_id=character_id,
                character_name=character_name,
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
                audit=audit_corp, character_id__in=missing_members_ids
            ).update(status=Members.States.MISSING)
            logger.debug(
                "Marked %s missing members for: %s",
                len(missing_members_ids),
                audit_corp.corporation.corporation_name,
            )
        if _old_members:
            Members.objects.bulk_update(_old_members, ["character_name", "status"])
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

        audit_corp.last_update_members = timezone.now()
        audit_corp.save()

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
    return ("Corp Task finished for %s", audit_corp.corporation.corporation_name)

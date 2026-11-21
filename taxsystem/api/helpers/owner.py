"""Helpers of the owner API."""

# AA TaxSystem
from taxsystem.api.helpers.core import get_object_with_access
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner


def get_owner(
    request, owner_id: int, manage: bool = False
) -> tuple[bool, CorporationOwner | AllianceOwner | None]:
    """
    Get a CorporationOwner or AllianceOwner by EVE ID and check permissions.

    The ID is looked up as corporation first, then as alliance.

    Args:
        request: Django Request Object
        owner_id: EVE corporation or alliance ID of the owner
        manage: Check against `manage_to` instead of `visible_to` (for write actions)
    Returns:
        Tuple of (has_permissions: bool, CorporationOwner | AllianceOwner | None)
    """
    perms, owner = get_object_with_access(
        request,
        CorporationOwner.objects,
        manage=manage,
        eve_corporation__corporation_id=owner_id,
    )
    if owner is not None:
        return perms, owner
    return get_object_with_access(
        request,
        AllianceOwner.objects,
        manage=manage,
        eve_alliance__alliance_id=owner_id,
    )

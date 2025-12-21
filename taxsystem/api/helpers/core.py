# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner


def get_manage_owner(
    request: WSGIRequest, owner_id: int
) -> tuple[CorporationOwner | AllianceOwner | None, bool]:
    """
    Check if the user has manage permissions for the owner.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        owner_id (int): The ID of the owner to retrieve
    Returns:
        tuple: A tuple containing the owner object (or None if not found) and a boolean indicating permission
    """
    perms = True
    try:
        owner = CorporationOwner.objects.get(eve_corporation__corporation_id=owner_id)
        visible = CorporationOwner.objects.manage_to(request.user)
        if owner not in visible:
            perms = False
    except CorporationOwner.DoesNotExist:
        try:
            owner = AllianceOwner.objects.get(eve_alliance__alliance_id=owner_id)
            visible = AllianceOwner.objects.manage_to(request.user)
            if owner not in visible:
                perms = False
        except AllianceOwner.DoesNotExist:
            return None, None
    return owner, perms


def get_owner(
    request: WSGIRequest, owner_id: int
) -> tuple[CorporationOwner | AllianceOwner | None, bool]:
    """
    Check if the user has visibility permissions for the owner.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        owner_id (int): The ID of the owner to retrieve
    Returns:
        tuple: A tuple containing the owner object (or None if not found) and a boolean indicating permission
    """
    perms = True
    try:
        owner = CorporationOwner.objects.get(eve_corporation__corporation_id=owner_id)
        visible = CorporationOwner.objects.visible_to(request.user)
        if owner not in visible:
            perms = False
    except CorporationOwner.DoesNotExist:
        try:
            owner = AllianceOwner.objects.get(eve_alliance__alliance_id=owner_id)
            visible = AllianceOwner.objects.visible_to(request.user)
            if owner not in visible:
                perms = False
        except AllianceOwner.DoesNotExist:
            return None, False
    return owner, perms


def get_character_permissions(request, character_id) -> bool:
    """
    Check if the user has permissions for the character.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        character_id (int): The ID of the character to check permissions for
    Returns:
        bool: True if the user has permissions for the character, False otherwise
    """
    perms = True

    # Get all character IDs the user owns
    char_ids = request.user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    if character_id not in char_ids:
        perms = False
    return perms

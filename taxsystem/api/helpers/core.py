# Standard Library
from typing import Protocol, TypeVar

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

# Alliance Auth
from allianceauth.authentication.models import User

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner

T = TypeVar("T", bound=models.Model)


class AccessManager(Protocol[T]):
    """A manager with `visible_to` and `manage_to` (e.g. the owner managers)."""

    def get(self, **lookup) -> T:
        """Get one object."""

    def visible_to(self, user) -> models.QuerySet[T]:
        """Objects the user may see."""

    def manage_to(self, user) -> models.QuerySet[T]:
        """Objects the user may manage."""


def get_object_with_access(
    request, manager: AccessManager[T], manage: bool = False, **lookup
) -> tuple[bool, T | None]:
    """
    Get one object through an `AccessManager` and check the user's access to it.

    Args:
        request: Django Request Object
        manager: The manager of the model, e.g. `CorporationOwner.objects`
        manage: Check against `manage_to` instead of `visible_to` (for write actions)
        **lookup: Lookup of the object, e.g. `eve_corporation__corporation_id=1`
    Returns:
        Tuple of (has_permissions: bool, object | None)
    """
    try:
        obj = manager.get(**lookup)
    except ObjectDoesNotExist:
        return False, None

    if manage:
        allowed = manager.manage_to(request.user)
    else:
        allowed = manager.visible_to(request.user)
    return allowed.filter(pk=obj.pk).exists(), obj


def get_tax_free_user_ids(owner: CorporationOwner | AllianceOwner) -> set[int]:
    """
    Return the IDs of all users that are in a tax-free group of the owner.

    Same definition as the group part of ``is_tax_free`` on the payment account,
    but loaded once per owner instead of once per account.
    """
    group_ids = owner.group_model.objects.filter(
        owner=owner, groups__isnull=False
    ).values_list("groups__pk", flat=True)
    return set(
        User.objects.filter(groups__pk__in=list(group_ids)).values_list("pk", flat=True)
    )


def get_character_permissions(request, character_id) -> bool:
    """
    Check if the user has permissions for the character.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        character_id (int): The ID of the character to check permissions for
    Returns:
        bool: True if the user has permissions for the character, False otherwise
    """
    return request.user.character_ownerships.filter(
        character__character_id=character_id
    ).exists()

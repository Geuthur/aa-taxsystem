"""Generic View Helpers for Owner (Corporation/Alliance) Views"""

# Django
from django.core.handlers.wsgi import WSGIRequest

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner


def get_default_owner_id(request: WSGIRequest, owner_type: str) -> int | None:
    """
    Get default owner ID from user's main character.

    Args:
        request: Django request object
        owner_type: "corporation" or "alliance"

    Returns:
        Owner ID (corporation_id or alliance_id) or None
    """
    if not hasattr(request.user, "profile") or not request.user.profile.main_character:
        return None

    main_char = request.user.profile.main_character

    if owner_type == "corporation":
        return main_char.corporation_id
    if owner_type == "alliance":
        return main_char.alliance_id

    return None


def get_owner_context_key(owner_type: str) -> str:
    """
    Get context key for owner_id based on type.

    Args:
        owner_type: "corporation" or "alliance"

    Returns:
        Context key: "corporation_id" or "alliance_id"
    """
    return f"{owner_type}_id"


def get_owner_template(view_name: str, owner_type: str) -> str:
    """
    Get template name based on owner type and view.

    Args:
        view_name: Name of the view ("manage", "payments", "own_payments")
        owner_type: "corporation" or "alliance"

    Returns:
        Template path
    """
    templates = {
        "manage": {
            "corporation": "taxsystem/manage.html",
            "alliance": "taxsystem/manage.html",  # Same template
        },
        "payments": {
            "corporation": "taxsystem/payments.html",
            "alliance": "taxsystem/payments.html",  # Same template
        },
        "own_payments": {
            "corporation": "taxsystem/own-payments.html",
            "alliance": "taxsystem/own-payments.html",  # Same template
        },
    }

    return templates.get(view_name, {}).get(owner_type, "taxsystem/index.html")


def get_owner_display_name(owner_type: str) -> str:
    """
    Get display name for owner type.

    Args:
        owner_type: "corporation" or "alliance"

    Returns:
        Display name: "Corporation" or "Alliance"
    """
    return owner_type.title()


def is_corporation_owner(owner) -> bool:
    """Check if owner is a CorporationOwner instance."""
    return isinstance(owner, CorporationOwner)


def is_alliance_owner(owner) -> bool:
    """Check if owner is an AllianceOwner instance."""
    return isinstance(owner, AllianceOwner)


def get_owner_type_from_instance(owner) -> str:
    """
    Get owner type string from owner instance.

    Args:
        owner: CorporationOwner or AllianceOwner instance

    Returns:
        "corporation" or "alliance"
    """
    if is_corporation_owner(owner):
        return "corporation"
    if is_alliance_owner(owner):
        return "alliance"
    return "unknown"

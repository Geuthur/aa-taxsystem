"""This module provides lazy loading of some common functions and objects that are not needed for every request."""

# Django
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import (
    alliance_logo_url,
    character_portrait_url,
    corporation_logo_url,
    type_render_url,
)


def get_character_portrait_url(
    character_id: int, size: int = 32, character_name: str = None, as_html: bool = False
) -> str:
    """Get the character portrait for a character ID."""
    try:
        render_url = character_portrait_url(character_id=character_id, size=size)
    except ValueError:
        return ""

    if as_html:
        render_html = format_html(
            '<img class="character-portrait rounded-circle" src="{}" alt="{}">',
            render_url,
            character_name,
        )
        return render_html
    return render_url


def get_corporation_logo_url(
    corporation_id: int,
    size: int = 32,
    corporation_name: str = None,
    as_html: bool = False,
) -> str:
    """Get the corporation logo for a corporation ID."""

    render_url = corporation_logo_url(corporation_id=corporation_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="corporation-logo rounded-circle" src="{}" alt="{}">',
            render_url,
            corporation_name,
        )
        return render_html
    return render_url


def get_alliance_logo_url(
    alliance_id: int,
    size: int = 32,
    alliance_name: str = None,
    as_html: bool = False,
) -> str:
    """Get the alliance logo for a alliance ID."""

    render_url = alliance_logo_url(alliance_id=alliance_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="alliance-logo rounded-circle" src="{}" alt="{}">',
            render_url,
            alliance_name,
        )
        return render_html
    return render_url


def get_type_render_url(
    type_id: int, size: int = 32, type_name: str = None, as_html: bool = False
) -> str:
    """Get the type render for a type ID."""

    render_url = type_render_url(type_id=type_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="type-render rounded-circle" src="{}" alt="{}">',
            render_url,
            type_name,
        )
        return render_html
    return render_url

"""This module provides lazy loading of some common functions and objects that are not needed for every request."""

from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.evelinks.eveimageserver import (
    character_portrait_url,
    type_render_url,
)


def get_character_portrait_url(
    character_id: int, size: int = 32, character_name: str = None, as_html: bool = False
) -> str:
    """Get the character portrait for a character ID."""

    render_url = character_portrait_url(character_id=character_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="character-portrait rounded-circle" src="{}" alt="{}">',
            render_url,
            character_name,
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
            '<img class="type-render rounded-circle" src="{}}" alt="{}">',
            render_url,
            type_name,
        )
        return render_html
    return render_url


def get_badge_html(label: str, color: str = "primary", size: str = "sm") -> str:
    """Get a badge HTML element."""

    return format_html(
        '<span class="badge badge-{} badge-{}">{}</span>',
        color,
        size,
        label,
    )


def get_bool_icon_html(
    value: bool, true_icon: str = "check", false_icon: str = "times"
) -> str:
    """Get a boolean icon HTML element."""

    icon = true_icon if value else false_icon
    state = "success" if value else "danger"

    return format_html(
        '<button class="btn btn-{} btn-sm"><i class="fas fa-{}"></i></button>',
        state,
        icon,
    )

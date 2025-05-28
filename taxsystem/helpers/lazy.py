"""This module provides lazy loading of some common functions and objects that are not needed for every request."""

# Django
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import (
    character_portrait_url,
    corporation_logo_url,
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


def get_badge_html(label: str, color: str = "primary", size: str = "sm") -> str:
    """Get a badge HTML element."""

    return format_html(
        '<span class="badge badge-{} badge-{}">{}</span>',
        color,
        size,
        label,
    )


def str_normalize_time(evetime, hours: bool = False) -> str:
    """Normalize time to a string."""
    if hours:
        return timezone.localtime(evetime).strftime("%Y-%m-%d %H:%M")
    return timezone.localtime(evetime).strftime("%Y-%m-%d")


def generate_icon(
    color: str, icon: str, size: str = 32, title: str = None, position: str = "end"
) -> str:
    """Generate a bootstrap icon button."""
    html = f"<div class='d-flex justify-content-{position}'>"
    html += f"<button class='btn btn-{color} btn-sm d-flex align-items-center justify-content-center'"
    html += f" style='height: {size}px; width: {size}px;' data-tooltip-toggle='taxsystem-tooltip'"
    if title:
        html += f" title='{title}'"
    html += ">"
    html += f"<i class='{icon}'></i>"
    html += "</button>"
    html += "</div>"
    return format_html(html)

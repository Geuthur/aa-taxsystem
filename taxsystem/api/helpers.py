from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from taxsystem.models.tax import OwnerAudit


def get_corporation(request, corporation_id) -> tuple[bool | None, OwnerAudit | None]:
    """Get Corporation and check permissions"""
    perms = True

    try:
        corp = OwnerAudit.objects.get(corporation__corporation_id=corporation_id)
    except OwnerAudit.DoesNotExist:
        return None, None

    # Check access
    visible = OwnerAudit.objects.visible_to(request.user)
    if corp not in visible:
        perms = False
    return perms, corp


def generate_button(
    corporation_id: int, template, queryset, settings, request
) -> mark_safe:
    """Generate a html button for the tax system"""
    return format_html(
        render_to_string(
            template,
            {
                "corporation_id": corporation_id,
                "queryset": queryset,
                "settings": settings,
            },
            request=request,
        )
    )


# pylint: disable=too-many-positional-arguments
def generate_settings(
    title: str, icon: str, color: str, text: str, modal: str, action: str, ajax: str
) -> dict:
    """Generate a settings dict for the tax system"""
    return {
        "title": title,
        "icon": icon,
        "color": color,
        "text": text,
        "modal": modal,
        "action": action,
        "ajax": ajax,
    }

# Django
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.models.tax import OwnerAudit, Payments


def get_manage_corporation(request, corporation_id) -> tuple[OwnerAudit | None, bool]:
    """Get Corporation and Permission"""
    corp = get_corporation(request, corporation_id)
    perms = get_manage_permission(request, corporation_id)
    return corp, perms


def get_corporation(request, corporation_id) -> OwnerAudit | None:
    """Get Corporation"""
    try:
        corp = OwnerAudit.objects.get(corporation__corporation_id=corporation_id)
    except OwnerAudit.DoesNotExist:
        return None

    # Check access
    visible = OwnerAudit.objects.visible_to(request.user)
    if corp not in visible:
        corp = None
    return corp


def get_manage_permission(request, corporation_id) -> bool:
    """Get Permission for Corporation"""
    perms = True

    try:
        corp = OwnerAudit.objects.get(corporation__corporation_id=corporation_id)
    except OwnerAudit.DoesNotExist:
        return False

    # Check access
    visible = OwnerAudit.objects.manage_to(request.user)
    if corp not in visible:
        perms = False
    return perms


def get_character_permissions(request, character_id) -> bool:
    """Get Permission for Character"""
    perms = True

    char_ids = request.user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    if character_id not in char_ids:
        perms = False
    return perms


def get_info_button(corporation_id, payment: Payments, request) -> mark_safe:
    details = generate_settings(
        title=_("Payment Details"),
        icon="fas fa-info",
        color="primary",
        text=_("View Payment Details"),
        modal="modalViewDetailsContainer",
        action=f"/taxsystem/api/corporation/{corporation_id}/character/{payment.character_id}/payment/{payment.pk}/view/details/",
        ajax="ajax_details",
    )
    button = generate_button(
        corporation_id=corporation_id,
        template="taxsystem/partials/form/button.html",
        queryset=payment,
        settings=details,
        request=request,
    )
    return button


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

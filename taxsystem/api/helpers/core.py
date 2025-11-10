# Django
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.models.tax import OwnerAudit, Payments


def get_manage_corporation(request, corporation_id) -> tuple[OwnerAudit | None, bool]:
    """Get Corporation and Permission"""
    perms = True
    try:
        corp = OwnerAudit.objects.get(corporation__corporation_id=corporation_id)
    except OwnerAudit.DoesNotExist:
        return None, None

    visible = OwnerAudit.objects.visible_to(request.user)
    if corp not in visible:
        perms = False
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


def generate_status_icon(payment: Payments) -> mark_safe:
    """Generate a status icon for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/icons/payment-status.html",
            {
                "payment": payment,
                "color": Payments.RequestStatus(payment.request_status).color(),
            },
        )
    )


def generate_info_button(payment: Payments) -> mark_safe:
    """Generate a info button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/payment-info.html",
            {
                "payment": payment,
            },
        )
    )

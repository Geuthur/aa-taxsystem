# Django
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner, CorporationPayments


def get_manage_owner(
    request, owner_id
) -> tuple[CorporationOwner | AllianceOwner | None, bool]:
    """Get Owner (Corporation or Alliance) and Permission"""
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
    request, owner_id
) -> tuple[CorporationOwner | AllianceOwner | None, bool]:
    """Get Owner (Corporation or Alliance) and Permission"""
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


def get_corporation(request, corporation_id) -> CorporationOwner | None:
    """Get Corporation"""
    try:
        corp = CorporationOwner.objects.get(
            eve_corporation__corporation_id=corporation_id
        )
    except CorporationOwner.DoesNotExist:
        return None

    # Check access
    visible = CorporationOwner.objects.visible_to(request.user)
    if corp not in visible:
        corp = None
    return corp


def get_manage_corporation(
    request, corporation_id
) -> tuple[CorporationOwner | None, bool]:
    """Get Corporation and Permission"""
    perms = True
    try:
        corp = CorporationOwner.objects.get(
            eve_corporation__corporation_id=corporation_id
        )
    except CorporationOwner.DoesNotExist:
        return None, None

    visible = CorporationOwner.objects.manage_to(request.user)
    if corp not in visible:
        perms = False
    return corp, perms


def get_alliance(request, alliance_id) -> AllianceOwner | None:
    """Get Alliance"""
    try:
        owner = AllianceOwner.objects.get(eve_alliance__alliance_id=alliance_id)
    except AllianceOwner.DoesNotExist:
        return None

    # Check access
    visible = AllianceOwner.objects.visible_to(request.user)
    if owner not in visible:
        owner = None
    return owner


def get_manage_alliance(request, alliance_id) -> tuple[AllianceOwner | None, bool]:
    """Get Permission for Alliance"""
    perms = True
    try:
        owner = AllianceOwner.objects.get(eve_alliance__alliance_id=alliance_id)
    except AllianceOwner.DoesNotExist:
        return None, None

    # Check access
    visible = AllianceOwner.objects.manage_to(request.user)
    if owner not in visible:
        perms = False
    return owner, perms


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


def generate_status_icon(payment: CorporationPayments) -> mark_safe:
    """Generate a status icon for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/icons/payment-status.html",
            {
                "payment": payment,
                "color": CorporationPayments.RequestStatus(
                    payment.request_status
                ).color(),
            },
        )
    )


def generate_info_button(payment: CorporationPayments) -> mark_safe:
    """Generate a info button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/payment-info.html",
            {
                "payment": payment,
            },
        )
    )

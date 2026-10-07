"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required

# AA TaxSystem
from taxsystem import __app_name__, __title__, __version__, tasks
from taxsystem.models.alliance import (
    AllianceOwner,
)
from taxsystem.models.corporation import CorporationOwner
from taxsystem.models.helpers.textchoices import AdminActions
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


@login_required
@permission_required("taxsystem.basic_access")
def react_base(request: WSGIRequest):
    """Serve the React app; routing and permissions of the pages are handled by the API."""
    context = {"version": __version__, "app_name": __app_name__}
    return render(request, "taxsystem/react_base.html", context=context)


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=CorporationOwner.get_esi_scopes())
def add_corp(request: WSGIRequest, token):
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    corp = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )[0]

    owner, created = CorporationOwner.objects.update_or_create(
        eve_corporation=corp,
        defaults={
            "name": char.corporation_name,
            "active": True,
        },
    )

    if created:
        owner.admin_log_model(
            user=request.user,
            owner=owner,
            action=AdminActions.ADD,
            comment=_("Added to Tax System"),
        ).save()

    tasks.update_corporation.apply_async(
        args=[owner.eve_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = _("{corporation_name} successfully added/updated to Tax System").format(
        corporation_name=char.corporation_name,
    )
    messages.info(request, msg)
    return redirect("taxsystem:index")


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=CorporationOwner.get_esi_scopes())
def add_alliance(request: WSGIRequest, token):
    # TODO Implement Alliance System
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    tax_corp = get_object_or_404(
        CorporationOwner, eve_corporation__corporation_id=char.corporation_id
    )

    ally = EveAllianceInfo.objects.get_or_create(
        alliance_id=char.alliance_id,
        defaults={
            "member_count": 0,
            "alliance_ticker": char.alliance_ticker,
            "alliance_name": char.alliance_name,
        },
    )[0]

    owner_alliance, created = AllianceOwner.objects.update_or_create(
        eve_alliance=ally,
        defaults={
            "corporation": tax_corp,
            "name": char.alliance_name,
            "active": True,
        },
    )

    if created:
        owner_alliance.admin_log_model(
            user=request.user,
            owner=owner_alliance,
            action=AdminActions.ADD,
            comment=_("Added Alliance to Tax System with Corporation {corp}").format(
                corp=tax_corp.name
            ),
        ).save()

    tasks.update_alliance.apply_async(
        args=[owner_alliance.eve_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = _("{alliance_name} successfully added/updated to Tax System").format(
        alliance_name=char.alliance_name,
    )
    messages.info(request, msg)
    return redirect("taxsystem:index")

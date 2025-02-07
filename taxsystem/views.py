"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as trans
from esi.decorators import token_required

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from taxsystem.helpers.views import add_info_to_context
from taxsystem.models import OwnerAudit
from taxsystem.tasks import update_corp

from .hooks import get_extension_logger

logger = get_extension_logger(__name__)


@login_required
@permission_required("taxsystem.basic_access")
def index(request):
    context = {
        "title": "Tax System",
    }
    return render(request, "taxsystem/index.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def members(request, corporation_pk):
    """Corporation View"""

    context = {
        "entity_pk": corporation_pk,
        "entity_type": "corporation",
        "title": "Members",
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/view/members.html", context=context)


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=OwnerAudit.get_esi_scopes())
def add_corp(request, token):
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    corp, _ = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )

    OwnerAudit.objects.update_or_create(
        corporation=corp,
        defaults={
            "name": corp.corporation_name,
            "active": True,
        },
    )

    update_corp.apply_async(
        args=[char.corporation_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = trans("{corporation_name} successfully added/updated to Tax System").format(
        corporation_name=corp.corporation_name,
    )
    messages.info(request, msg)
    return redirect("taxsystem:index")


@login_required
@permission_required("taxsystem.manage_access")
def overview(request):
    """Overview of the tax system"""

    context = {}
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/admin/overview.html", context=context)

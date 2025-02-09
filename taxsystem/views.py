"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as trans
from django.views.decorators.http import require_POST
from esi.decorators import token_required

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from taxsystem.api.helpers import get_corporation
from taxsystem.helpers.views import add_info_to_context
from taxsystem.models import OwnerAudit
from taxsystem.models.tax import Payments, PaymentSystem
from taxsystem.tasks import update_corp

from .hooks import get_extension_logger

logger = get_extension_logger(__name__)


@login_required
@permission_required("taxsystem.basic_access")
def index(request):
    context = {
        "title": "Tax System",
    }
    context = add_info_to_context(request, context)
    return render(request, "taxsystem/index.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def administration(request, corporation_pk):
    """Manage View"""

    context = {
        "entity_pk": corporation_pk,
        "entity_type": "corporation",
        "title": "Administration",
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/view/manage.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def payments(request, corporation_pk):
    """Payments View"""

    if corporation_pk == 0:
        try:
            corporation_pk = request.user.profile.main_character.corporation_id
        except AttributeError:
            messages.error(request.user, "No Main Character found")

    context = {
        "entity_pk": corporation_pk,
        "entity_type": "corporation",
        "title": "Payments",
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/view/payments.html", context=context)


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


@login_required
@permission_required("taxsystem.manage_access")
@require_POST
def approve_payment(request, corporation_id: int, payment_pk: int):
    # Check Permission
    perms, corp = get_corporation(request, corporation_id)
    previous_url = request.headers.get("referer", "taxsystem:payments")

    if not perms:
        msg = trans("Permission Denied")
        messages.error(request, msg)
        return redirect(previous_url)

    try:
        with transaction.atomic():
            payment = Payments.objects.get(
                payment_user__corporation=corp, pk=payment_pk
            )
            if payment.payment_status in [
                Payments.States.PENDING,
                Payments.States.NEEDS_APPROVAL,
            ]:
                payment.approved = Payments.Approval.APPROVED
                payment.payment_status = Payments.States.PAID
                payment.system = Payments.Systems.MANUAL
                payment.save()

                payment_user = PaymentSystem.objects.get(
                    corporation=corp, user=payment.payment_user.user
                )
                payment_user.payment_pool += payment.amount
                payment_user.save()

                msg = trans("Payment ID: %s successfully approved") % payment.pk
            else:
                msg = trans("Payment ID: %s is already edited") % payment.pk
    except IntegrityError:
        msg = trans("Transaction failed. Please try again.")

    messages.info(request, msg)
    return redirect(previous_url)

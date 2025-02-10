"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
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
        "title": _("Tax System"),
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
        "title": _("Administration"),
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/view/manage.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def payments(request, corporation_pk):
    """Payments View"""
    corporation_name = None
    if corporation_pk == 0:
        try:
            corporation_pk = request.user.profile.main_character.corporation_id
            corporation_name = request.user.profile.main_character.corporation_name
        except AttributeError:
            messages.error(request.user, "No Main Character found")

    context = {
        "entity_name": corporation_name,
        "entity_pk": corporation_pk,
        "entity_type": "corporation",
        "title": _("Payments"),
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
    msg = _("{corporation_name} successfully added/updated to Tax System").format(
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
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect(previous_url)

    try:
        with transaction.atomic():
            payment = Payments.objects.get(
                payment_user__corporation=corp, pk=payment_pk
            )
            if payment.is_pending or payment.is_needs_approval:
                payment.approved = Payments.Approval.APPROVED
                payment.payment_status = Payments.States.PAID
                payment.system = Payments.Systems.MANUAL
                payment.save()

                payment_user = PaymentSystem.objects.get(
                    corporation=corp, user=payment.payment_user.user
                )
                payment_user.payment_pool += payment.amount
                payment_user.save()

                msg = _("Payment ID: %s successfully approved") % payment.pk
            else:
                msg = _("Payment ID: %s is already edited") % payment.pk
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")

    messages.info(request, msg)
    return redirect(previous_url)


@login_required
@permission_required("taxsystem.manage_access")
@require_POST
def undo_payment(request, corporation_id: int, payment_pk: int):
    # Check Permission
    perms, corp = get_corporation(request, corporation_id)
    previous_url = request.headers.get("referer", "taxsystem:payments")

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect(previous_url)

    try:
        with transaction.atomic():
            payment = Payments.objects.get(
                payment_user__corporation=corp, pk=payment_pk
            )
            if payment.is_paid:
                payment.approved = Payments.Approval.PENDING
                payment.payment_status = Payments.States.PENDING
                payment.system = Payments.Systems.MANUAL
                payment.save()

                payment_user = PaymentSystem.objects.get(
                    corporation=corp, user=payment.payment_user.user
                )
                payment_user.payment_pool -= payment.amount
                payment_user.save()

                msg = _("Payment ID: %s successfully undone") % payment.pk
            else:
                msg = _("Payment ID: %s is already undone") % payment.pk
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")

    messages.info(request, msg)
    return redirect(previous_url)


@login_required
@permission_required("taxsystem.manage_access")
@require_POST
def decline_payment(request, corporation_id: int, payment_pk: int):
    # Check Permission
    perms, corp = get_corporation(request, corporation_id)
    previous_url = request.headers.get("referer", "taxsystem:payments")

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect(previous_url)

    try:
        with transaction.atomic():
            payment = Payments.objects.get(
                payment_user__corporation=corp, pk=payment_pk
            )
            if payment.is_pending or payment.is_needs_approval:
                payment.approved = Payments.Approval.REJECTED
                payment.payment_status = Payments.States.FAILED
                payment.system = Payments.Systems.MANUAL
                payment.save()

                payment_user = PaymentSystem.objects.get(
                    corporation=corp, user=payment.payment_user.user
                )
                payment_user.save()

                msg = _("Payment ID: %s successfully declined") % payment.pk
            else:
                msg = _("Payment ID: %s is already declined") % payment.pk
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")

    messages.info(request, msg)
    return redirect(previous_url)


@login_required
@permission_required("taxsystem.manage_access")
@require_POST
def switch_user(request, corporation_id: int, user_pk: int):
    # Check Permission
    perms, corp = get_corporation(request, corporation_id)
    previous_url = request.headers.get("referer", "taxsystem:payments")

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect(previous_url)

    try:
        with transaction.atomic():
            payment_system = PaymentSystem.objects.get(corporation=corp, pk=user_pk)
            if payment_system.is_active:
                payment_system.status = PaymentSystem.States.DEACTIVATED
                msg = (
                    _("Payment System User: %s successfully deactivated")
                    % payment_system.name
                )
            else:
                payment_system.status = PaymentSystem.States.ACTIVE
                msg = (
                    _("Payment System User: %s successfully activated")
                    % payment_system.name
                )
            payment_system.save()
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")

    messages.info(request, msg)
    return redirect(previous_url)


@csrf_exempt
def update_tax_amount(request: WSGIRequest, corporation_id: int):
    if request.method == "POST":
        value = float(request.POST.get("value"))

        try:
            if value < 0:
                return JsonResponse(
                    {"message": _("Please enter a valid number")}, status=400
                )
        except ValueError:
            return JsonResponse(
                {"message": _("Please enter a valid number")}, status=400
            )

        # Check Permission
        perms, corp = get_corporation(request, corporation_id)

        if not perms:
            return JsonResponse({"message": _("Permission Denied")}, status=403)

        try:
            corp.tax_amount = value
            corp.save()
        except ValidationError:
            return JsonResponse(
                {"message": _("Please enter a valid number")}, status=400
            )
        return JsonResponse({"message": ""}, status=200)
    return JsonResponse({"message": _("Invalid request method")}, status=405)


@csrf_exempt
def update_tax_period(request: WSGIRequest, corporation_id: int):
    if request.method == "POST":
        value = float(request.POST.get("value"))

        try:
            if value < 0:
                return JsonResponse(
                    {"message": _("Please enter a valid number")}, status=400
                )
        except ValueError:
            return JsonResponse(
                {"message": _("Please enter a valid number")}, status=400
            )

        # Check Permission
        perms, corp = get_corporation(request, corporation_id)

        if not perms:
            return JsonResponse({"message": _("Permission Denied")}, status=403)

        try:
            corp.tax_period = value
            corp.save()
        except ValidationError:
            return JsonResponse(
                {"message": _("Please enter a valid number")}, status=400
            )
        return JsonResponse({"message": ""}, status=200)
    return JsonResponse({"message": _("Invalid request method")}, status=405)

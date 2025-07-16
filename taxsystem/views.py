"""PvE Views"""

# Standard Library
import logging

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.decorators import permissions_required
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.decorators import token_required

# AA TaxSystem
from taxsystem import forms, tasks
from taxsystem.api.helpers import get_corporation, get_manage_permission
from taxsystem.helpers.views import add_info_to_context
from taxsystem.models.logs import AdminLogs, PaymentHistory
from taxsystem.models.tax import Members, OwnerAudit, Payments, PaymentSystem

logger = logging.getLogger(__name__)


@login_required
@permission_required("taxsystem.basic_access")
def index(request):
    """Index View"""
    return redirect(
        "taxsystem:payments", request.user.profile.main_character.corporation_id
    )


@login_required
@permission_required("taxsystem.basic_access")
def admin(request):
    corporation_id = request.user.profile.main_character.corporation_id
    if not request.user.is_superuser:
        messages.error(request, _("You do not have permission to access this page."))
        return redirect("taxsystem:index")

    if request.method == "POST":
        force_refresh = False
        if request.POST.get("force_refresh", False):
            force_refresh = True
        if request.POST.get("run_clear_etag"):
            messages.info(request, _("Queued Clear All ETags"))
            tasks.clear_all_etags.apply_async(priority=1)
        if request.POST.get("run_taxsystem_updates"):
            messages.info(request, _("Queued Update All Taxsystem"))
            tasks.update_all_taxsytem.apply_async(
                kwargs={"force_refresh": force_refresh}, priority=7
            )
    context = {
        "corporation_id": corporation_id,
        "title": _("Tax System Superuser Administration"),
    }
    return render(request, "taxsystem/admin.html", context=context)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
def administration(request, corporation_id):
    """Manage View"""
    if corporation_id is None:
        corporation_id = request.user.profile.main_character.corporation_id

    context = {
        "corporation_id": corporation_id,
        "title": _("Administration"),
        "forms": {
            "accept_request": forms.TaxAcceptForm(),
            "reject_request": forms.TaxRejectForm(),
            "undo_request": forms.TaxUndoForm(),
            "switchuser_request": forms.TaxSwitchUserForm(),
            "delete_request": forms.TaxDeleteForm(),
        },
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/manage.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def payments(request, corporation_id):
    """Payments View"""
    if corporation_id is None:
        corporation_id = request.user.profile.main_character.corporation_id

    perms = get_corporation(request, corporation_id)

    if perms is None:
        messages.error(request, _("No corporation found."))

    corporations = OwnerAudit.objects.visible_to(request.user)

    context = {
        "corporation_id": corporation_id,
        "title": _("Payments"),
        "forms": {
            "accept_request": forms.TaxAcceptForm(),
            "reject_request": forms.TaxRejectForm(),
            "undo_request": forms.TaxUndoForm(),
        },
        "corporations": corporations,
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/payments.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def own_payments(request, corporation_id=None):
    """Own Payments View"""
    if corporation_id is None:
        corporation_id = request.user.profile.main_character.corporation_id

    perms = get_corporation(request, corporation_id)

    if perms is None:
        messages.error(request, _("No corporation found."))

    corporations = OwnerAudit.objects.visible_to(request.user)

    context = {
        "corporation_id": corporation_id,
        "title": _("Own Payments"),
        "corporations": corporations,
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/own-payments.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def faq(request, corporation_id):
    """Payments View"""
    if corporation_id is None:
        corporation_id = request.user.profile.main_character.corporation_id

    corporations = OwnerAudit.objects.visible_to(request.user)

    context = {
        "corporation_id": corporation_id,
        "title": _("FAQ"),
        "corporations": corporations,
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/faq.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def account(request, corporation_id):
    """Payments View"""
    if corporation_id is None:
        corporation_id = request.user.profile.main_character.corporation_id
    character_id = request.user.profile.main_character.character_id

    corporations = OwnerAudit.objects.visible_to(request.user)

    perms = get_corporation(request, corporation_id)

    if perms is None:
        messages.error(request, _("No corporation found."))

    context = {
        "corporation_id": corporation_id,
        "title": _("Account"),
        "corporations": corporations,
        "character_id": character_id,
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/account.html", context=context)


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=OwnerAudit.get_esi_scopes())
def add_corp(request, token):
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    corp, __ = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )

    owner, created = OwnerAudit.objects.update_or_create(
        corporation=corp,
        defaults={
            "name": corp.corporation_name,
            "active": True,
        },
    )

    if created:
        AdminLogs(
            user=request.user,
            owner=owner,
            action=AdminLogs.Actions.ADD,
            comment=_("Added to Tax System"),
        ).save()

    tasks.update_corporation.apply_async(
        args=[owner.pk], kwargs={"force_refresh": True}, priority=6
    )
    msg = _("{corporation_name} successfully added/updated to Tax System").format(
        corporation_name=corp.corporation_name,
    )
    messages.info(request, msg)
    return redirect("taxsystem:index")


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@require_POST
def approve_payment(request: WSGIRequest, corporation_id: int, payment_pk: int):
    msg = _("Invalid Method")
    corp = get_corporation(request, corporation_id)

    perms = get_manage_permission(request, corporation_id)
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.TaxAcceptForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["accept_info"]
                payment = Payments.objects.get(account__owner=corp, pk=payment_pk)
                if payment.is_pending or payment.is_needs_approval:
                    msg = _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} approved"
                    ).format(
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )
                    payment.request_status = Payments.RequestStatus.APPROVED
                    payment.reviser = request.user.profile.main_character.character_name
                    payment.save()

                    payment_account = PaymentSystem.objects.get(
                        owner=corp, user=payment.account.user
                    )
                    payment_account.deposit += payment.amount
                    payment_account.save()
                    PaymentHistory(
                        user=request.user,
                        payment=payment,
                        action=PaymentHistory.Actions.STATUS_CHANGE,
                        comment=reason,
                        new_status=Payments.RequestStatus.APPROVED,
                    ).save()
                    return JsonResponse(
                        data={"success": True, "message": msg}, status=200, safe=False
                    )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@require_POST
def undo_payment(request: WSGIRequest, corporation_id: int, payment_pk: int):
    msg = _("Invalid Method")
    corp = get_corporation(request, corporation_id)

    perms = get_manage_permission(request, corporation_id)
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.TaxUndoForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["undo_reason"]
                payment = Payments.objects.get(account__owner=corp, pk=payment_pk)
                if payment.is_approved or payment.is_rejected:
                    msg = _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} undone"
                    ).format(
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )
                    # Ensure that the payment is not rejected
                    if not payment.is_rejected:
                        payment_account = PaymentSystem.objects.get(
                            owner=corp, user=payment.account.user
                        )
                        payment_account.deposit -= payment.amount
                        payment_account.save()
                    payment.request_status = Payments.RequestStatus.PENDING
                    payment.reviser = ""
                    payment.save()
                    PaymentHistory(
                        user=request.user,
                        payment=payment,
                        action=PaymentHistory.Actions.STATUS_CHANGE,
                        comment=reason,
                        new_status=Payments.RequestStatus.PENDING,
                    ).save()
                    return JsonResponse(
                        data={"success": True, "message": msg}, status=200, safe=False
                    )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@require_POST
def reject_payment(request: WSGIRequest, corporation_id: int, payment_pk: int):
    msg = _("Invalid Method")
    corp = get_corporation(request, corporation_id)

    perms = get_manage_permission(request, corporation_id)
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.TaxRejectForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["reject_reason"]
                payment = Payments.objects.get(account__owner=corp, pk=payment_pk)
                if payment.is_pending or payment.is_needs_approval:
                    payment.request_status = Payments.RequestStatus.REJECTED
                    payment.reviser = request.user.profile.main_character.character_name
                    payment.save()

                    payment_account = PaymentSystem.objects.get(
                        owner=corp, user=payment.account.user
                    )
                    payment_account.save()
                    msg = _("Payment ID: %s - Amount: %s - Name: %s rejected") % (
                        payment.pk,
                        intcomma(payment.amount),
                        payment.name,
                    )

                    PaymentHistory(
                        user=request.user,
                        payment=payment,
                        action=PaymentHistory.Actions.STATUS_CHANGE,
                        comment=reason,
                        new_status=Payments.RequestStatus.REJECTED,
                    ).save()
                    return JsonResponse(
                        data={"success": True, "message": msg}, status=200, safe=False
                    )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@require_POST
def switch_user(request: WSGIRequest, corporation_id: int, payment_system_pk: int):
    msg = _("Invalid Method")
    corp = get_corporation(request, corporation_id)

    perms = get_manage_permission(request, corporation_id)
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.TaxSwitchUserForm(data=request.POST)
            if form.is_valid():
                payment_system = PaymentSystem.objects.get(
                    owner=corp, pk=payment_system_pk
                )
                if payment_system.is_active:
                    payment_system.status = PaymentSystem.Status.DEACTIVATED
                    msg = _("Payment System User: %s deactivated") % payment_system.name
                else:
                    payment_system.status = PaymentSystem.Status.ACTIVE
                    msg = _("Payment System User: %s activated") % payment_system.name

                AdminLogs(
                    user=request.user,
                    owner=corp,
                    action=AdminLogs.Actions.CHANGE,
                    comment=msg,
                ).save()
                payment_system.save()
            return JsonResponse(
                data={"success": True, "message": msg}, status=200, safe=False
            )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@csrf_exempt
def update_tax_amount(request: WSGIRequest, corporation_id: int):
    if request.method == "POST":
        value = float(request.POST.get("value"))
        msg = _("Please enter a valid number")
        try:
            if value < 0:
                return JsonResponse({"message": msg}, status=400)
        except ValueError:
            return JsonResponse({"message": msg}, status=400)

        corp = get_corporation(request, corporation_id)

        perms = get_manage_permission(request, corporation_id)

        if not perms:
            return JsonResponse({"message": _("Permission Denied")}, status=403)

        try:
            corp.tax_amount = value
            corp.save()
            msg = _(f"Tax Amount from {corp.name} updated to {value}")
            AdminLogs(
                user=request.user,
                owner=corp,
                action=AdminLogs.Actions.CHANGE,
                comment=msg,
            ).save()
        except ValidationError:
            return JsonResponse({"message": msg}, status=400)
        return JsonResponse({"message": msg}, status=200)
    return JsonResponse({"message": _("Invalid request method")}, status=405)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@csrf_exempt
def update_tax_period(request: WSGIRequest, corporation_id: int):
    if request.method == "POST":
        value = int(request.POST.get("value"))
        msg = _("Please enter a valid number")
        try:
            if value < 0:
                return JsonResponse({"message": msg}, status=400)
        except ValueError:
            return JsonResponse({"message": msg}, status=400)

        corp = get_corporation(request, corporation_id)

        perms = get_manage_permission(request, corporation_id)

        if not perms:
            return JsonResponse({"message": _("Permission Denied")}, status=403)

        try:
            corp.tax_period = value
            corp.save()
            msg = _(f"Tax Period from {corp.name} updated to {value}")
            AdminLogs(
                user=request.user,
                owner=corp,
                action=AdminLogs.Actions.CHANGE,
                comment=msg,
            ).save()
        except ValidationError:
            return JsonResponse({"message": msg}, status=400)
        return JsonResponse({"message": msg}, status=200)
    return JsonResponse({"message": _("Invalid request method")}, status=405)


@login_required
@permissions_required(["taxsystem.manage_own_corp", "taxsystem.manage_corps"])
@require_POST
def delete_member(request: WSGIRequest, corporation_id: int, member_pk: int):
    msg = _("Invalid Method")
    corp = get_corporation(request, corporation_id)

    perms = get_manage_permission(request, corporation_id)
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    form = forms.TaxDeleteForm(data=request.POST)
    if form.is_valid():
        reason = form.cleaned_data["delete_reason"]
        member = Members.objects.get(owner=corp, pk=member_pk)
        if member.is_missing:
            msg = _(f"Member {member.character_name} deleted")
            msg += f" - {reason}"
            member.delete()
            AdminLogs(
                user=request.user,
                owner=corp,
                action=AdminLogs.Actions.DELETE,
                comment=msg,
            ).save()
            return JsonResponse(
                data={"success": True, "message": msg}, status=200, safe=False
            )
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)

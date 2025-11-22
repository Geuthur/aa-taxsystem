"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.decorators import permissions_required
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, forms, tasks
from taxsystem.api.helpers.core import (
    get_alliance,
    get_character_permissions,
    get_corporation,
    get_manage_corporation,
    get_manage_owner,
    get_owner,
)
from taxsystem.helpers import lazy
from taxsystem.helpers.views import add_info_to_context
from taxsystem.helpers.views_generic import (
    get_default_owner_id,
    get_owner_context_key,
    get_owner_display_name,
    get_owner_template,
    get_owner_type_from_instance,
)
from taxsystem.models.alliance import (
    AllianceAdminHistory,
    AllianceOwner,
)
from taxsystem.models.corporation import (
    CorporationAdminHistory,
    CorporationOwner,
    Members,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("taxsystem.basic_access")
def admin(request: WSGIRequest):
    corporation_id = request.user.profile.main_character.corporation_id
    if not request.user.is_superuser:
        messages.error(request, _("You do not have permission to access this page."))
        return redirect("taxsystem:index")

    def _handle_taxsystem_updates(force_refresh):
        messages.info(request, _("Queued Update All Taxsystem"))
        tasks.update_all_taxsytem.apply_async(
            kwargs={"force_refresh": force_refresh}, priority=7
        )

    def _handle_corporation_updates(force_refresh):
        corporation_id_input = request.POST.get("corporation_id")
        if corporation_id_input:
            try:
                corp_id = int(corporation_id_input)
                corporation = CorporationOwner.objects.get(
                    eve_corporation__corporation_id=corp_id
                )
                messages.info(
                    request,
                    _("Queued Update for Corporation: %s") % corporation.name,
                )
                tasks.update_corporation.apply_async(
                    args=[corporation.pk],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
            except (ValueError, CorporationOwner.DoesNotExist):
                messages.error(
                    request,
                    _("Corporation with ID %s not found") % corporation_id_input,
                )
        else:
            messages.info(request, _("Queued Update All Taxsystem Corporations"))
            corporations = CorporationOwner.objects.filter(active=True)
            for corporation in corporations:
                tasks.update_corporation.apply_async(
                    args=[corporation.pk],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )

    def _handle_alliance_updates(force_refresh):
        alliance_id_input = request.POST.get("alliance_id")
        if alliance_id_input:
            try:
                ally_id = int(alliance_id_input)
                alliance = AllianceOwner.objects.get(eve_alliance__alliance_id=ally_id)
                messages.info(
                    request, _("Queued Update for Alliance: %s") % alliance.name
                )
                tasks.update_alliance.apply_async(
                    args=[alliance.pk],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
            except (ValueError, AllianceOwner.DoesNotExist):
                messages.error(
                    request, _("Alliance with ID %s not found") % alliance_id_input
                )
        else:
            messages.info(request, _("Queued Update All Taxsystem Alliances"))
            alliances = AllianceOwner.objects.filter(active=True)
            for alliance in alliances:
                tasks.update_alliance.apply_async(
                    args=[alliance.pk],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )

    if request.method == "POST":
        force_refresh = bool(request.POST.get("force_refresh", False))
        if request.POST.get("run_taxsystem_updates"):
            _handle_taxsystem_updates(force_refresh)
        if request.POST.get("run_taxsystem_corporation_updates"):
            _handle_corporation_updates(force_refresh)
        if request.POST.get("run_taxsystem_alliance_updates"):
            _handle_alliance_updates(force_refresh)

    context = {
        "corporation_id": corporation_id,
        "title": _("Tax System Superuser Administration"),
    }
    return render(request, "taxsystem/admin.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def index(request: WSGIRequest):  # pylint: disable=unused-argument
    """Index View - Redirects to Owner Overview"""
    return redirect("taxsystem:owner_overview")


@login_required
@permission_required("taxsystem.basic_access")
def owner_overview(request: WSGIRequest):
    """
    Owner Overview - Unified view for all Corporations and Alliances.

    Shows all owners (corporations and alliances) that the user has access to
    in a single DataTable with portraits, names, types, and action buttons.

    Args:
        request: The HTTP request object containing user information

    Returns:
        HttpResponse: Rendered owner overview template with combined owner list
    """
    owners = []

    # Get visible corporations using manager method
    corps = CorporationOwner.objects.visible_to(request.user).select_related(
        "eve_corporation"
    )

    for corp in corps:
        owners.append(
            {
                "type": "corporation",
                "type_display": _("Corporation"),
                "id": corp.eve_corporation.corporation_id,
                "name": corp.eve_corporation.corporation_name,
                "portrait": lazy.get_corporation_logo_url(
                    corp.eve_corporation.corporation_id,
                    size=64,
                    corporation_name=corp.eve_corporation.corporation_name,
                    as_html=True,
                ),
                "active": corp.active,
            }
        )

    # Get visible alliances using manager method
    alliances = AllianceOwner.objects.visible_to(request.user).select_related(
        "eve_alliance"
    )
    for alliance in alliances:
        owners.append(
            {
                "type": "alliance",
                "type_display": _("Alliance"),
                "id": alliance.eve_alliance.alliance_id,
                "name": alliance.eve_alliance.alliance_name,
                "portrait": lazy.get_alliance_logo_url(
                    alliance.eve_alliance.alliance_id,
                    size=64,
                    alliance_name=alliance.eve_alliance.alliance_name,
                    as_html=True,
                ),
                "active": alliance.active,
            }
        )

    # Sort by name
    owners.sort(key=lambda x: x["name"].lower())

    context = {
        "owners": owners,
        "title": _("Owner Overview"),
        "total_count": len(owners),
        "corporation_count": len([o for o in owners if o["type"] == "corporation"]),
        "alliance_count": len([o for o in owners if o["type"] == "alliance"]),
    }

    return render(
        request, "taxsystem/owner-overview.html", add_info_to_context(request, context)
    )


@login_required
@permission_required("taxsystem.basic_access")
def payments(request: WSGIRequest, owner_id: int = None):
    """Payments View"""
    if not owner_id:
        owner_id = request.user.profile.main_character.corporation_id

    owner, perms = get_owner(request, owner_id)

    if owner is None:
        messages.error(request, _("Owner not Found"))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied"))
        return redirect("taxsystem:index")

    # Determine owner type for context
    owner_type = get_owner_type_from_instance(owner)

    return generic_owner_payments(request, owner_id=owner_id, owner_type=owner_type)


@login_required
@permission_required("taxsystem.basic_access")
def own_payments(request: WSGIRequest, owner_id=None):
    """Own Payments View (Backwards-compatible wrapper)"""
    if not owner_id:
        owner_id = request.user.profile.main_character.corporation_id

    owner, perms = get_owner(request, owner_id)

    if owner is None:
        messages.error(request, _("Owner not Found"))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied"))
        return redirect("taxsystem:index")

    # Determine owner type for context
    owner_type = get_owner_type_from_instance(owner)
    return generic_owner_own_payments(request, owner_id=owner_id, owner_type=owner_type)


@login_required
@permission_required("taxsystem.basic_access")
def faq(request: WSGIRequest, owner_id=None):
    """FAQ View (Generic for Corporation and Alliance)"""
    if not owner_id:
        owner_id = request.user.profile.main_character.corporation_id

    # Get owner generically
    owner, perms = get_manage_owner(request, owner_id)
    perms = perms or get_character_permissions(
        request, request.user.profile.main_character.character_id
    )

    if owner is None:
        messages.error(request, _("Owner not Found"))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied"))
        return redirect("taxsystem:index")

    # Determine owner type for context
    owner_type = get_owner_type_from_instance(owner)
    context_key = get_owner_context_key(owner_type)

    corporations = CorporationOwner.objects.visible_to(request.user)

    context = {
        "owner_id": owner_id,
        context_key: owner_id,  # "corporation_id" or "alliance_id"
        "owner_type": owner_type,
        "title": _("FAQ"),
        "corporations": corporations,
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/faq.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def account(request: WSGIRequest, owner_id=None):
    """Account View (Generic for Corporation and Alliance)"""
    if not owner_id:
        owner_id = request.user.profile.main_character.corporation_id

    character_id = request.user.profile.main_character.character_id

    user_profile = UserProfile.objects.filter(
        main_character__character_id=character_id
    ).first()

    if not user_profile:
        messages.error(request, _("No User found."))
        return redirect("taxsystem:index")

    try:
        owner, perms = get_manage_owner(request, owner_id)
        perms = perms or get_character_permissions(request, character_id)
    except AttributeError:
        messages.error(request, _("User has no main character set."))
        return redirect("taxsystem:index")

    if owner is None:
        messages.error(request, _("Owner not Found"))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied"))
        return redirect("taxsystem:index")

    payment_user = owner.payments_account_class.objects.filter(
        user__profile=user_profile,
        owner=owner,
    ).first()

    if not payment_user:
        messages.error(request, _("No Payment System User found."))
        return redirect("taxsystem:index")

    # Get member info
    try:
        member = Members.objects.get(character_id=character_id)
    except Members.DoesNotExist:
        member = None

    # Determine owner type for context
    owner_type = get_owner_type_from_instance(owner)
    context_key = get_owner_context_key(owner_type)

    context = {
        "title": _("Account"),
        "character_id": character_id,
        "owner_id": owner_id,
        context_key: owner_id,
        "owner_type": owner_type,
        "account": {
            "name": payment_user.name,
            "owner": owner,
            "corporation": owner,  # Backwards compatibility
            "status": payment_user.Status(payment_user.status).html(text=True),
            "deposit": (
                payment_user.deposit_html
                if payment_user.status != payment_user.Status.MISSING
                else "N/A"
            ),
            "has_paid": (
                payment_user.has_paid_icon(badge=True, text=True)
                if payment_user.status != payment_user.Status.MISSING
                else "N/A"
            ),
            "last_paid": (
                payment_user.last_paid
                if payment_user.status != payment_user.Status.MISSING
                else "N/A"
            ),
            "next_due": (
                payment_user.next_due
                if payment_user.status != payment_user.Status.MISSING
                else "N/A"
            ),
            "joined": member.joined if member else "N/A",
            "last_login": member.logon if member else "N/A",
        },
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/account.html", context=context)


@login_required
@permissions_required(
    [
        "taxsystem.manage_own_corp",
        "taxsystem.manage_corps",
        "taxsystem.manage_own_alliance",
        "taxsystem.manage_alliances",
    ]
)
def manage_owner(request: WSGIRequest, owner_id: int = None):
    """Manage View (Backwards-compatible wrapper)"""
    owner, perms = get_manage_owner(request, owner_id)

    if owner is None:
        messages.error(request, _("Owner not Found"))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied"))
        return redirect("taxsystem:index")

    # Determine owner type for context
    owner_type = get_owner_type_from_instance(owner)

    return generic_manage_owner(request, owner_id=owner_id, owner_type=owner_type)


@login_required
def manage_filter(request: WSGIRequest, owner_id: int):
    """Manage View"""
    owner, perms = get_manage_owner(request, owner_id)

    filter_sets = owner.filterset_class.objects.filter(owner=owner)
    context = {
        "corporation_id": owner_id if isinstance(owner, CorporationOwner) else None,
        "alliance_id": owner_id if isinstance(owner, AllianceOwner) else None,
        "owner_id": owner_id,
        "filter_sets": filter_sets,
        "title": _("Manage Filters"),
        "forms": {
            "filter": forms.AddJournalFilterForm(
                queryset=owner.filterset_class.objects.filter(owner=owner)
            ),
            "filter_set": forms.CreateFilterSetForm(),
            "delete_request": forms.MemberDeleteForm(),
        },
    }
    if perms is False:
        messages.error(request, _("You do not have permission to manage this owner."))
        return redirect("taxsystem:index")

    with transaction.atomic():
        form_add = forms.AddJournalFilterForm(
            data=request.POST,
            queryset=owner.filterset_class.objects.filter(owner=owner),
        )
        form_set = forms.CreateFilterSetForm(data=request.POST)

        if form_add.is_valid():
            queryset = form_add.cleaned_data["filter_set"]
            filter_type = form_add.cleaned_data["filter_type"]
            value = form_add.cleaned_data["value"]
            try:
                owner.filter_class.objects.create(
                    filter_set=queryset,
                    filter_type=filter_type,
                    value=value,
                )
            except IntegrityError:
                messages.error(request, _("A filter with this name already exists."))
                return redirect("taxsystem:manage_filter", owner_id=owner_id)
            except Exception as e:  # pylint: disable=broad-except
                messages.error(
                    request, _("Something went wrong, please try again later.")
                )
                logger.error("Error creating journal filter: %s", e)
                return redirect("taxsystem:manage_filter", owner_id=owner_id)

        if form_set.is_valid():
            name = form_set.cleaned_data["name"]
            description = form_set.cleaned_data["description"]
            try:
                owner.filterset_class.objects.create(
                    owner=owner,
                    name=name,
                    description=description,
                )
            except IntegrityError:
                messages.error(
                    request, _("A filter set with this name already exists.")
                )
                return redirect("taxsystem:manage_filter", owner_id=owner_id)
            except Exception as e:  # pylint: disable=broad-except
                messages.error(
                    request, _("Something went wrong, please try again later.")
                )
                logger.error("Error creating journal filter set: %s", e)
                return render(request, "taxsystem/manage-filter.html", context=context)

    return render(request, "taxsystem/manage-filter.html", context=context)


@login_required
def switch_filterset(request: WSGIRequest, owner_id: int, filter_set_id: int):
    """Deactivate Filter Set View"""
    owner, perms = get_manage_owner(request, owner_id)

    if perms is False:
        messages.error(request, _("You do not have permission to manage this owner."))
        return redirect("taxsystem:index")

    filter_set = get_object_or_404(
        owner.filterset_class.objects.filter(owner=owner), id=filter_set_id
    )
    filter_sets = owner.filterset_class.objects.filter(owner=owner)

    filter_set.enabled = not filter_set.enabled
    filter_set.save()

    context = {
        "owner_id": owner_id,
        "filter_sets": filter_sets,
        "forms": {
            "filter": forms.AddJournalFilterForm(
                queryset=owner.filterset_class.objects.filter(owner=owner)
            ),
            "filter_set": forms.CreateFilterSetForm(),
        },
        "title": _("Deactivate Filter Set"),
    }
    context = add_info_to_context(request, context)

    messages.success(
        request, _(f"Filter set switched to {filter_set.enabled} successfully.")
    )
    return redirect("taxsystem:manage_filter", owner_id=owner_id)


@login_required
def delete_filterset(request: WSGIRequest, owner_id: int, filter_set_id: int):
    """Delete Filter Set View"""
    owner, perms = get_manage_owner(request, owner_id)

    if perms is False:
        messages.error(request, _("You do not have permission to manage this owner."))
        return redirect("taxsystem:index")

    filter_set = get_object_or_404(
        owner.filterset_class.objects.filter(owner=owner), id=filter_set_id
    )
    filter_sets = owner.filterset_class.objects.filter(owner=owner)

    filter_set.delete()
    msg = _(f"{filter_set.name} from {owner.name} deleted")
    owner.admin_history_class(
        user=request.user,
        owner=owner,
        action=owner.admin_history_class.Actions.DELETE,
        comment=msg,
    ).save()
    messages.success(request, _("Filter set deleted successfully."))

    context = {
        "owner_id": owner_id,
        "filter_sets": filter_sets,
        "forms": {
            "filter": forms.AddJournalFilterForm(
                queryset=owner.filterset_class.objects.filter(owner=owner)
            ),
            "filter_set": forms.CreateFilterSetForm(),
        },
        "title": _("Delete Filter Set"),
    }
    context = add_info_to_context(request, context)

    return redirect("taxsystem:manage_filter", owner_id=owner_id)


@login_required
@require_POST
def delete_filter(request: WSGIRequest, owner_id: int, filter_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    form = forms.FilterDeleteForm(data=request.POST)
    if form.is_valid():
        filter_obj = owner.filter_class.objects.get(
            filter_set__owner=owner, pk=filter_pk
        )
        if filter_obj:
            msg = _(
                f"{filter_obj.filter_type}({filter_obj.value}) from {filter_obj.filter_set} deleted - {form.cleaned_data['delete_reason']}"
            )
            filter_obj.delete()
            owner.admin_history_class(
                user=request.user,
                owner=owner,
                action=owner.admin_history_class.Actions.DELETE,
                comment=msg,
            ).save()
            return JsonResponse(
                data={"success": True, "message": msg}, status=200, safe=False
            )
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
def edit_filterset(request: WSGIRequest, owner_id: int, filter_set_id: int):
    """Edit Filter Set View"""
    owner, perms = get_manage_owner(request, owner_id)

    if perms is False:
        messages.error(request, _("You do not have permission to manage this owner."))
        return redirect("taxsystem:index")

    edit_set = get_object_or_404(
        owner.filterset_class.filter(owner=owner), id=filter_set_id
    )
    filter_sets = owner.filterset_class.filter(owner=owner)

    if request.method == "POST":
        form = forms.EditFilterSetForm(request.POST, instance=edit_set)
        if form.is_valid():
            form.save()
            messages.success(request, _("Filter set updated successfully."))
            return redirect("taxsystem:manage_filter", owner_id=owner_id)
    else:
        form = forms.EditFilterSetForm(instance=edit_set)

    context = {
        "owner_id": owner_id,
        "filter_sets": filter_sets,
        "forms": {
            "edit_filter_set": form,
        },
        "title": _("Edit Filter Set"),
    }
    context = add_info_to_context(request, context)

    return render(request, "taxsystem/manage-filter.html", context=context)


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=CorporationOwner.get_esi_scopes())
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

    owner, created = CorporationOwner.objects.update_or_create(
        eve_corporation=corp,
        defaults={
            "name": char.corporation_name,
            "active": True,
        },
    )

    if created:
        CorporationAdminHistory(
            user=request.user,
            owner=owner,
            action=CorporationAdminHistory.Actions.ADD,
            comment=_("Added to Tax System"),
        ).save()

    tasks.update_corporation.apply_async(
        args=[owner.pk], kwargs={"force_refresh": True}, priority=6
    )
    msg = _("{corporation_name} successfully added/updated to Tax System").format(
        corporation_name=char.corporation_name,
    )
    messages.info(request, msg)
    return redirect("taxsystem:index")


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=CorporationOwner.get_esi_scopes())
def add_alliance(request, token):
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    tax_corp = get_object_or_404(
        CorporationOwner, eve_corporation__corporation_id=char.corporation_id
    )

    ally, __ = EveAllianceInfo.objects.get_or_create(
        alliance_id=char.alliance_id,
        defaults={
            "member_count": 0,
            "alliance_ticker": char.alliance_ticker,
            "alliance_name": char.alliance_name,
        },
    )

    owner_alliance, created = AllianceOwner.objects.update_or_create(
        eve_alliance=ally,
        defaults={
            "corporation": tax_corp,
            "name": char.alliance_name,
            "active": True,
        },
    )

    if created:
        AllianceAdminHistory(
            user=request.user,
            owner=owner_alliance,
            action=AllianceAdminHistory.Actions.ADD,
            comment=_("Added Alliance to Tax System with Corporation {corp}").format(
                corp=tax_corp.name
            ),
        ).save()

    tasks.update_alliance.apply_async(
        args=[owner_alliance.pk], kwargs={"force_refresh": True}, priority=6
    )
    msg = _("{alliance_name} successfully added/updated to Tax System").format(
        alliance_name=char.alliance_name,
    )
    messages.info(request, msg)
    return redirect("taxsystem:index")


@login_required
@require_POST
def approve_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.PaymentAcceptForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["accept_info"]
                payment = owner.payments_class.objects.get(
                    account__owner=owner, pk=payment_pk
                )
                if payment.is_pending or payment.is_needs_approval:
                    msg = _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} approved"
                    ).format(
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )
                    payment.request_status = owner.payments_class.RequestStatus.APPROVED
                    payment.reviser = request.user.profile.main_character.character_name
                    payment.save()

                    payment_account = owner.payments_account_class.objects.get(
                        owner=owner, user=payment.account.user
                    )
                    payment_account.deposit += payment.amount
                    payment_account.save()
                    owner.payments_history_class(
                        user=request.user,
                        payment=payment,
                        action=owner.payments_history_class.Actions.STATUS_CHANGE,
                        comment=reason,
                        new_status=owner.payments_class.RequestStatus.APPROVED,
                    ).save()
                    return JsonResponse(
                        data={"success": True, "message": msg}, status=200, safe=False
                    )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@require_POST
def undo_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.PaymentUndoForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["undo_reason"]
                payment = owner.payments_class.objects.get(
                    account__owner=owner, pk=payment_pk
                )
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
                        payment_account = owner.payments_account_class.objects.get(
                            owner=owner, user=payment.account.user
                        )
                        payment_account.deposit -= payment.amount
                        payment_account.save()
                    payment.request_status = owner.payments_class.RequestStatus.PENDING
                    payment.reviser = ""
                    payment.save()
                    owner.payments_history_class(
                        user=request.user,
                        payment=payment,
                        action=owner.payments_history_class.Actions.STATUS_CHANGE,
                        comment=reason,
                        new_status=owner.payments_class.RequestStatus.PENDING,
                    ).save()
                    return JsonResponse(
                        data={"success": True, "message": msg}, status=200, safe=False
                    )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@require_POST
def reject_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.PaymentRejectForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["reject_reason"]
                payment = owner.payments_class.objects.get(
                    account__owner=owner, pk=payment_pk
                )
                if payment.is_pending or payment.is_needs_approval:
                    payment.request_status = owner.payments_class.RequestStatus.REJECTED
                    payment.reviser = request.user.profile.main_character.character_name
                    payment.save()

                    payment_account = owner.payments_account_class.objects.get(
                        owner=owner, user=payment.account.user
                    )
                    payment_account.save()
                    msg = _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} rejected"
                    ).format(
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )

                    owner.payments_history_class(
                        user=request.user,
                        payment=payment,
                        action=owner.payments_history_class.Actions.STATUS_CHANGE,
                        comment=reason,
                        new_status=owner.payments_class.RequestStatus.REJECTED,
                    ).save()
                    return JsonResponse(
                        data={"success": True, "message": msg}, status=200, safe=False
                    )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@require_POST
def delete_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.PaymentDeleteForm(data=request.POST)
            if form.is_valid():
                reason = form.cleaned_data["delete_reason"]
                payment = owner.payments_class.objects.get(
                    account__owner=owner, pk=payment_pk
                )

                if payment.entry_id != 0:  # Prevent deletion of ESI imported payments
                    msg = _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} deletion failed - ESI imported payments cannot be deleted"
                    ).format(
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )
                    return JsonResponse(
                        data={"success": False, "message": msg}, status=400, safe=False
                    )

                msg = _(
                    "Payment ID: {pid} - Amount: {amount} - Name: {name} deleted - {reason}"
                ).format(
                    pid=payment.pk,
                    amount=intcomma(payment.amount),
                    name=payment.name,
                    reason=reason,
                )

                # Refund if approved
                if payment.is_approved:
                    payment_user = owner.payments_account_class.objects.get(
                        owner=owner, user=payment.account.user
                    )
                    payment_user.deposit -= payment.amount
                    payment_user.save()

                # Delete Payment
                payment.delete()

                # Log Admin Action
                owner.admin_history_class(
                    user=request.user,
                    owner=owner,
                    action=owner.admin_history_class.Actions.DELETE,
                    comment=msg,
                ).save()

                return JsonResponse(
                    data={"success": True, "message": msg}, status=200, safe=False
                )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@require_POST
def add_payment(request: WSGIRequest, owner_id: int, payment_system_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.PaymentAddForm(data=request.POST)
            if form.is_valid():
                amount = form.cleaned_data["amount"]
                reason = form.cleaned_data["add_reason"]
                payment_account = owner.payments_account_class.objects.get(
                    owner=owner, pk=payment_system_pk
                )

                payment = owner.payments_class(
                    name=payment_account.user.username,
                    entry_id=0,  # Manual Entry
                    amount=amount,
                    account=payment_account,
                    date=timezone.now(),
                    reason=reason,
                    request_status=owner.payments_class.RequestStatus.APPROVED,
                    reviser=request.user.username,
                    owner_id=owner_id,
                )
                payment.save()
                payment_account.deposit += amount
                payment_account.save()

                msg = _(
                    "Payment ID: {pid} - Amount: {amount} - Name: {name} added"
                ).format(
                    pid=payment.pk,
                    amount=intcomma(payment.amount),
                    name=payment.name,
                )

                # Log Payment Action
                owner.payments_history_class(
                    user=request.user,
                    payment=payment,
                    action=owner.payments_history_class.Actions.PAYMENT_ADDED,
                    comment=reason,
                    new_status=owner.payments_class.RequestStatus.APPROVED,
                ).save()

                # Log Admin Action
                owner.admin_history_class(
                    user=request.user,
                    owner=owner,
                    action=owner.admin_history_class.Actions.ADD,
                    comment=msg,
                ).save()
                return JsonResponse(
                    data={"success": True, "message": msg}, status=200, safe=False
                )
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


@login_required
@require_POST
def switch_user(request: WSGIRequest, owner_id: int, payment_system_pk: int):
    msg = _("Invalid Method")
    owner, perms = get_manage_owner(request, owner_id)

    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    try:
        with transaction.atomic():
            form = forms.TaxSwitchUserForm(data=request.POST)
            if form.is_valid():
                # Get Payment System User
                payment_system = owner.payments_account_class.objects.get(
                    owner=owner, pk=payment_system_pk
                )
                # Toggle Active Status
                if payment_system.is_active:
                    payment_system.status = payment_system.Status.DEACTIVATED
                    msg = _("Payment System User: %s deactivated") % payment_system.name
                else:
                    payment_system.status = payment_system.Status.ACTIVE
                    msg = _("Payment System User: %s activated") % payment_system.name

                # Log Admin Action
                owner.admin_history_class(
                    user=request.user,
                    owner=owner,
                    action=owner.admin_history_class.Actions.CHANGE,
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
@csrf_exempt
def update_tax_amount(request: WSGIRequest, owner_id: int):
    if request.method == "POST":
        value = float(request.POST.get("value"))
        msg = _("Please enter a valid number")
        try:
            if value < 0:
                return JsonResponse({"message": msg}, status=400)
        except ValueError:
            return JsonResponse({"message": msg}, status=400)

        owner, perms = get_manage_owner(request, owner_id)

        logger.debug(
            f"Updating tax amount for owner ID {owner_id} to {value}. Permissions: {perms}"
        )

        if not perms:
            return JsonResponse({"message": _("Permission Denied")}, status=403)

        try:
            owner.tax_amount = value
            owner.save()
            msg = _(f"Tax Amount from {owner.name} updated to {value}")
            owner.admin_history_class(
                user=request.user,
                owner=owner,
                action=owner.admin_history_class.Actions.CHANGE,
                comment=msg,
            ).save()
            logger.debug(f"Tax amount updated successfully for owner ID {owner_id}")
        except ValidationError:
            return JsonResponse({"message": msg}, status=400)
        return JsonResponse({"message": msg}, status=200)
    return JsonResponse({"message": _("Invalid request method")}, status=405)


@login_required
@csrf_exempt
def update_tax_period(request: WSGIRequest, owner_id: int):
    if request.method == "POST":
        value = int(request.POST.get("value"))
        msg = _("Please enter a valid number")
        try:
            if value < 0:
                return JsonResponse({"message": msg}, status=400)
        except ValueError:
            return JsonResponse({"message": msg}, status=400)

        owner, perms = get_manage_owner(request, owner_id)

        if not perms:
            return JsonResponse({"message": _("Permission Denied")}, status=403)

        try:
            owner.tax_period = value
            owner.save()
            msg = _(f"Tax Period from {owner.name} updated to {value}")
            owner.admin_history_class(
                user=request.user,
                owner=owner,
                action=owner.admin_history_class.Actions.CHANGE,
                comment=msg,
            ).save()
        except ValidationError:
            return JsonResponse({"message": msg}, status=400)
        return JsonResponse({"message": msg}, status=200)
    return JsonResponse({"message": _("Invalid request method")}, status=405)


@login_required
@require_POST
def delete_member(request: WSGIRequest, corporation_id: int, member_pk: int):
    msg = _("Invalid Method")
    corp, perms = get_manage_corporation(request, corporation_id)
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            data={"success": False, "message": msg}, status=403, safe=False
        )

    form = forms.MemberDeleteForm(data=request.POST)
    if form.is_valid():
        reason = form.cleaned_data["delete_reason"]
        member = Members.objects.get(owner=corp, pk=member_pk)
        if member.is_missing:
            msg = _(f"Member {member.character_name} deleted - {reason}")
            member.delete()
            CorporationAdminHistory(
                user=request.user,
                owner=corp,
                action=CorporationAdminHistory.Actions.DELETE,
                comment=msg,
            ).save()
            return JsonResponse(
                data={"success": True, "message": msg}, status=200, safe=False
            )
    return JsonResponse(data={"success": False, "message": msg}, status=400, safe=False)


# =============================================================================
# Generic Owner Views (Corporation and Alliance Unified)
# =============================================================================


@login_required
def generic_manage_owner(
    request: WSGIRequest, owner_id: int = None, owner_type: str = "corporation"
):
    """
    Unified Owner Management View for Corporation and Alliance.

    Args:
        request: Django request object
        owner_id: Owner ID (corporation_id or alliance_id)
        owner_type: "corporation" or "alliance"

    Returns:
        Rendered manage template
    """
    # 1. Default ID resolution
    if owner_id is None:
        owner_id = get_default_owner_id(request, owner_type)
        if owner_id is None:
            messages.error(
                request,
                _("No default {owner_type} found.").format(
                    owner_type=get_owner_display_name(owner_type)
                ),
            )
            return redirect("taxsystem:index")

    # 2. Get owner and permissions
    owner, perms = get_manage_owner(request, owner_id)

    # 3. Permission checks
    if perms is False:
        messages.error(
            request,
            _("You do not have permission to manage this {owner_type}.").format(
                owner_type=get_owner_display_name(owner_type).lower()
            ),
        )
        return redirect("taxsystem:index")

    if owner is None:
        messages.error(
            request,
            _("{owner_type} not Found").format(
                owner_type=get_owner_display_name(owner_type)
            ),
        )
        return redirect("taxsystem:index")

    # 4. Build context
    context_key = get_owner_context_key(owner_type)
    template = get_owner_template("manage", owner_type)

    context = {
        context_key: owner_id,  # "corporation_id" or "alliance_id"
        "owner_id": owner_id,  # Generic key for templates
        "owner_type": owner_type,  # For conditional template logic
        "corporations": CorporationOwner.objects.visible_to(request.user),
        "title": (
            _("Corporation Tax System")
            if owner_type == "corporation"
            else _("Alliance Tax System")
        ),
        "manage_filter_url": reverse(
            "taxsystem:manage_filter", kwargs={"owner_id": owner_id}
        ),
        "forms": {
            "accept_request": forms.PaymentAcceptForm(),
            "reject_request": forms.PaymentRejectForm(),
            "add_request": forms.PaymentAddForm(),
            "payment_delete_request": forms.PaymentDeleteForm(),
            "undo_request": forms.PaymentUndoForm(),
            "switchuser_request": forms.TaxSwitchUserForm(),
            "delete_request": forms.MemberDeleteForm(),
        },
    }
    context = add_info_to_context(request, context)

    return render(request, template, context=context)


@login_required
@permission_required("taxsystem.basic_access")
def generic_owner_payments(
    request: WSGIRequest, owner_id: int = None, owner_type: str = "corporation"
):
    """
    Unified Payments View for Corporation and Alliance.

    Args:
        request: Django request object
        owner_id: Owner ID (corporation_id or alliance_id)
        owner_type: "corporation" or "alliance"

    Returns:
        Rendered payments template
    """
    # 1. Default ID resolution
    if owner_id is None:
        owner_id = get_default_owner_id(request, owner_type)
        if owner_id is None:
            messages.error(
                request,
                _("No default {owner_type} found.").format(
                    owner_type=get_owner_display_name(owner_type)
                ),
            )
            return redirect("taxsystem:index")

    # 2. Get owner
    if owner_type == "corporation":
        owner = get_corporation(request, owner_id)
    else:
        owner = get_alliance(request, owner_id)

    if owner is None:
        messages.error(
            request,
            _("No {owner_type} found.").format(
                owner_type=get_owner_display_name(owner_type)
            ),
        )

    # 3. Build context
    context_key = get_owner_context_key(owner_type)
    template = get_owner_template("payments", owner_type)

    corporations = CorporationOwner.objects.visible_to(request.user)

    context = {
        context_key: owner_id,  # "corporation_id" or "alliance_id"
        "owner_id": owner_id,  # Generic key
        "owner_type": owner_type,
        "title": _("Payments"),
        "forms": {
            "add_request": forms.PaymentAddForm(),
            "payment_delete_request": forms.PaymentDeleteForm(),
            "accept_request": forms.PaymentAcceptForm(),
            "reject_request": forms.PaymentRejectForm(),
            "undo_request": forms.PaymentUndoForm(),
        },
        "corporations": corporations,
    }
    context = add_info_to_context(request, context)

    return render(request, template, context=context)


@login_required
@permission_required("taxsystem.basic_access")
def generic_owner_own_payments(
    request: WSGIRequest, owner_id: int = None, owner_type: str = "corporation"
):
    """
    Unified Own Payments View for Corporation and Alliance.

    Args:
        request: Django request object
        owner_id: Owner ID (corporation_id or alliance_id)
        owner_type: "corporation" or "alliance"

    Returns:
        Rendered own payments template
    """
    # 1. Default ID resolution
    if owner_id is None:
        owner_id = get_default_owner_id(request, owner_type)
        if owner_id is None:
            messages.error(
                request,
                _("No default {owner_type} found.").format(
                    owner_type=get_owner_display_name(owner_type)
                ),
            )
            return redirect("taxsystem:index")

    # 2. Get owner and permissions
    if owner_type == "corporation":
        owner = get_corporation(request, owner_id)
    else:
        owner = get_alliance(request, owner_id)

    if owner is None:
        messages.error(
            request,
            _("No {owner_type} found.").format(
                owner_type=get_owner_display_name(owner_type)
            ),
        )
        return redirect("taxsystem:index")

    # 3. Build context
    context_key = get_owner_context_key(owner_type)
    template = get_owner_template("own_payments", owner_type)

    corporations = CorporationOwner.objects.visible_to(request.user)

    context = {
        context_key: owner_id,  # "corporation_id" or "alliance_id"
        "owner_id": owner_id,  # Generic key
        "owner_type": owner_type,
        "title": _("Own Payments") if owner_type == "alliance" else _("My Payments"),
        "corporations": corporations,
    }
    context = add_info_to_context(request, context)

    return render(request, template, context=context)

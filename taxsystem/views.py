"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
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
    get_character_permissions,
    get_manage_owner,
    get_owner,
)
from taxsystem.helpers import lazy
from taxsystem.models.alliance import (
    AllianceOwner,
)
from taxsystem.models.corporation import (
    CorporationOwner,
    Members,
)
from taxsystem.models.helpers.textchoices import AccountStatus
from taxsystem.models.logs import (
    AdminActions,
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

    if request.method == "POST":
        force_refresh = bool(request.POST.get("force_refresh", False))
        if request.POST.get("run_taxsystem_updates"):
            _handle_taxsystem_updates(force_refresh)
        if request.POST.get("run_taxsystem_corporation_updates"):
            _handle_corporation_updates(force_refresh)

    context = {
        "corporation_id": corporation_id,
        "title": _("Tax System Superuser Administration"),
    }
    return render(request, "taxsystem/admin.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def index(request: WSGIRequest):  # pylint: disable=unused-argument
    """
    Main TaxSystem View
    This view displays an overview of all available tax system owners depending on user's permissions.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
    Returns:
        HttpResponse: Rendered owner overview template with combined owner list
    """
    owner_list = []

    # Get all Corporations the user can see with their permissions
    corporations = (
        CorporationOwner.objects.visible_to(request.user)
        .select_related("eve_corporation")
        .order_by("eve_corporation__corporation_name")
    )
    for corporation in corporations:
        owner_list.append(
            {
                "type": "corporation",
                "type_display": _("Corporation"),
                "id": corporation.eve_corporation.corporation_id,
                "name": corporation.eve_corporation.corporation_name,
                "portrait": lazy.get_corporation_logo_url(
                    corporation.eve_corporation.corporation_id,
                    size=64,
                    corporation_name=corporation.eve_corporation.corporation_name,
                    as_html=True,
                ),
                "active": corporation.active,
                "actions": "",
            }
        )

    alliances = (
        AllianceOwner.objects.visible_to(request.user)
        .select_related("eve_alliance")
        .order_by("eve_alliance__alliance_name")
    )
    for alliance in alliances:
        owner_list.append(
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
                "actions": "",
            }
        )

    context = {
        "owners": owner_list,
        "title": _("TaxSystem Overview"),
        "total_count": len(owner_list),
    }

    return render(request, "taxsystem/taxsystem.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def payments(request: WSGIRequest, owner_id: int):
    """
    Render Payments View
    This view displays the payments made to a specific owner depending on user's permissions.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        owner_id (int): The ID of the owner for which to display payments
    Returns:
        HttpResponse: Rendered payments template with payment details
    """
    owner, perms = get_owner(request, owner_id)
    if owner is None:
        messages.error(request, _("Owner not Found."))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied."))
        return redirect("taxsystem:index")

    context = {
        "owner": owner,
        "title": _("Payments"),
    }

    return render(request, "taxsystem/view-payments.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def my_payments(request: WSGIRequest, owner_id: int):
    """
    Render My Payments View
    This view displays the payments made by the logged-in user for a specific owner depending on user's permissions.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        owner_id (int): The ID of the owner for which to display payments
    Returns:
        HttpResponse: Rendered my payments template with payment details
    """
    owner, perms = get_owner(request, owner_id)

    if owner is None:
        messages.error(request, _("Owner not Found."))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied."))
        return redirect("taxsystem:index")

    context = {
        "owner": owner,
        "title": _("My Payments"),
    }
    return render(request, "taxsystem/view-my-payments.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def faq(request: WSGIRequest, owner_id: int):
    """
    Render FAQ View
    This view displays the FAQ for a specific owner depending on user's permissions.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        owner_id (int): The ID of the owner to retrieve
    Returns:
        HttpResponse: Rendered FAQ template with owner details
    """
    owner, perms = get_owner(request, owner_id)
    if owner is None:
        messages.error(request, _("Owner not Found."))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied."))
        return redirect("taxsystem:index")

    context = {
        "owner": owner,
        "title": _("FAQ"),
    }

    return render(request, "taxsystem/view-faq.html", context=context)


@login_required
@permission_required("taxsystem.basic_access")
def account(request: WSGIRequest, owner_id: int, character_id: int = None):
    """
    Render Account View
    This view displays the account details for a specific character and owner depending on user's permissions.
    Args:
        request (WSGIRequest): The HTTP request object containing user information from Alliance Auth
        owner_id (int): The ID of the owner to retrieve
        character_id (int): The ID of the character whose account details are to be displayed
    Returns:
        HttpResponse: Rendered account template with account details
    """
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    user_profile = UserProfile.objects.filter(
        main_character__character_id=character_id
    ).first()

    if not user_profile:
        messages.error(request, _("No User found."))
        return redirect("taxsystem:index")

    owner, perms = get_manage_owner(request, owner_id)
    # Give access if character permission exists
    perms = perms or get_character_permissions(request, character_id)

    if owner is None:
        messages.error(request, _("Owner not Found."))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied."))
        return redirect("taxsystem:index")

    tax_account = owner.account_model.objects.filter(
        user__profile=user_profile,
        owner=owner,
    ).first()

    if not tax_account:
        messages.error(request, _("No Tax Account found."))
        return redirect("taxsystem:index")

    # Get member info
    try:
        member = Members.objects.get(character_id=character_id)
    except Members.DoesNotExist:
        member = None

    context = {
        "title": _("Account"),
        "owner": owner,
        "account": {
            "name": tax_account.name,
            "owner": owner,
            "corporation": owner,
            "character_id": character_id,
            "status": AccountStatus(tax_account.status).html(text=True),
            "deposit": (
                tax_account.deposit
                if tax_account.status != AccountStatus.MISSING
                else "N/A"
            ),
            "has_paid": (
                tax_account.has_paid_icon(badge=True, text=True)
                if tax_account.status != AccountStatus.MISSING
                else "N/A"
            ),
            "last_paid": (
                tax_account.last_paid
                if tax_account.status != AccountStatus.MISSING
                else "N/A"
            ),
            "next_due": (
                tax_account.next_due
                if tax_account.status != AccountStatus.MISSING
                else "N/A"
            ),
            "joined": member.joined if member else "N/A",
            "last_login": member.logon if member else "N/A",
        },
    }

    return render(request, "taxsystem/view-account.html", context=context)


@login_required
def manage_owner(request: WSGIRequest, owner_id: int = None):
    """Manage View (Backwards-compatible wrapper)"""
    owner, perms = get_manage_owner(request, owner_id)

    if owner is None:
        messages.error(request, _("Owner not Found."))
        return redirect("taxsystem:index")

    if perms is False:
        messages.error(request, _("Permission Denied."))
        return redirect("taxsystem:index")

    context = {
        "owner": owner,
        "title": _("Manage Tax System"),
        "manage_filter_url": reverse(
            "taxsystem:manage_filter", kwargs={"owner_id": owner_id}
        ),
        "forms": {
            "accept_payment_request": (
                forms.AcceptCorporationPaymentForm()
                if isinstance(owner, CorporationOwner)
                else forms.AcceptAlliancePaymentForm()
            ),
            "accept_reject_payment_request": (
                forms.RejectCorporationPaymentForm()
                if isinstance(owner, CorporationOwner)
                else forms.RejectAlliancePaymentForm()
            ),
            "add_payment_request": forms.PaymentAddForm(),
            "accept_delete_payment_request": (
                forms.DeleteCorporationPaymentForm()
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAlliancePaymentForm()
            ),
            "accept_undo_payment_request": (
                forms.UndoCorporationPaymentForm()
                if isinstance(owner, CorporationOwner)
                else forms.UndoAlliancePaymentForm()
            ),
            "accept_delete_member_request": forms.DeleteMemberForm(),
        },
    }
    return render(request, "taxsystem/view-manage.html", context=context)


@login_required
def manage_filter(request: WSGIRequest, owner_id: int):
    """Manage View"""
    owner, perms = get_manage_owner(request, owner_id)

    if perms is False:
        messages.error(request, _("You do not have permission to manage this owner."))
        return redirect("taxsystem:index")

    # Get existing filters
    queryset = owner.filterset_model.objects.filter(owner=owner)

    context = {
        "owner": owner,
        "title": _("Manage Filters"),
        "forms": {
            "filter": forms.AddJournalFilterForm(queryset=queryset),
            "filter_set": forms.CreateFilterSetForm(),
            "delete_filter_set": (
                forms.DeleteCorporationFilterSetForm()
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAllianceFilterSetForm()
            ),
            "delete_filter": (
                forms.DeleteCorporationFilterForm()
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAllianceFilterForm()
            ),
        },
    }

    with transaction.atomic():
        form_add = forms.AddJournalFilterForm(
            data=request.POST,
            queryset=queryset,
        )
        form_set = forms.CreateFilterSetForm(data=request.POST)

        if form_add.is_valid():
            queryset = form_add.cleaned_data["filter_set"]
            filter_type = form_add.cleaned_data["filter_type"]
            value = form_add.cleaned_data["value"]
            try:
                owner.filter_model.objects.create(
                    filter_set=queryset,
                    filter_type=filter_type,
                    value=value,
                )
            except IntegrityError:
                messages.error(
                    request,
                    format_lazy(
                        _("A Filter with {filter} already exists."),
                        filter=f'{filter_type} "{value}"',
                    ),
                )
            except Exception as e:  # pylint: disable=broad-except
                messages.error(
                    request, _("Something went wrong, please try again later.")
                )
                logger.exception("Error creating journal filter: %s", e)
                return redirect("taxsystem:manage_filter", owner_id=owner_id)

        if form_set.is_valid():
            name = form_set.cleaned_data["name"]
            description = form_set.cleaned_data["description"]
            try:
                owner.filterset_model.objects.create(
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
                logger.exception("Error creating journal filter set: %s", e)
                return redirect("taxsystem:manage_filter", owner_id=owner_id)

    return render(request, "taxsystem/view-filter.html", context=context)


@login_required
@permission_required("taxsystem.create_access")
@token_required(scopes=CorporationOwner.get_esi_scopes())
def add_corp(request: WSGIRequest, token):
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
        owner.admin_log_model(
            user=request.user,
            owner=owner,
            action=AdminActions.ADD,
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
def add_alliance(request: WSGIRequest, token):
    # TODO Implement Alliance System
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
        owner_alliance.admin_log_model(
            user=request.user,
            owner=owner_alliance,
            action=AdminActions.ADD,
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

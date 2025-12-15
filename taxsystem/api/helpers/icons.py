# Django
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.decorators import permissions_required

# AA TaxSystem
from taxsystem.models.alliance import (
    AllianceFilter,
    AllianceFilterSet,
    AlliancePaymentAccount,
    AlliancePayments,
)
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationFilterSet,
    CorporationPaymentAccount,
    CorporationPayments,
    Members,
)
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus


@permissions_required(
    [
        "taxsystem.manage_own_corp",
        "taxsystem.manage_corps",
        "taxsystem.manage_own_alliance",
        "taxsystem.manage_alliances",
    ]
)
def get_taxsystem_manage_action_icons(
    request: WSGIRequest,  # pylint: disable=unused-argument
    account: CorporationPaymentAccount | AlliancePaymentAccount,
):
    """
    Generate HTML Action Icons for the Tax System Management view.

    This function creates a set of action icons for managing tax system accounts.
    The Buttons include Edit, Delete, and View Transactions, each represented by an icon depending on User's permissions.

    Args:
        request (WSGIRequest): The HTTP request object containing user information.
        account (CorporationPaymentAccount | AlliancePaymentAccount): The tax account object.
    Returns:
        SafeString: HTML string containing the action icons.
    """
    taxsystem_request_icons = "<div class='d-flex justify-content-end'>"
    taxsystem_request_icons += get_tax_account_add_button(account=account)
    taxsystem_request_icons += get_tax_account_switch_button(account=account)
    taxsystem_request_icons += get_tax_account_info_button(account=account)
    taxsystem_request_icons += "</div>"
    return taxsystem_request_icons


@permissions_required(
    [
        "taxsystem.manage_own_corp",
        "taxsystem.manage_corps",
        "taxsystem.manage_own_alliance",
        "taxsystem.manage_alliances",
    ]
)
def get_taxsystem_manage_payments_action_icons(
    request: WSGIRequest,  # pylint: disable=unused-argument
    payment: CorporationPayments | AlliancePayments,
):
    """
    Generate HTML Action Icons for the Tax System Management view Payments Modal.

    This function creates a set of action icons for managing tax system accounts.
    The Buttons include Approve, Reject, Undo, Delete and View Transactions, each represented by an icon depending on User's permissions.

    Args:
        request (WSGIRequest): The HTTP request object containing user information.
        account (CorporationPaymentAccount | AlliancePaymentAccount): The tax account object.
    Returns:
        SafeString: HTML string containing the action icons.
    """
    taxsystem_request_icons = "<div class='d-flex justify-content-end'>"

    # Only show approve/reject buttons for pending or needs approval payments
    if payment.request_status in [
        PaymentRequestStatus.PENDING,
        PaymentRequestStatus.NEEDS_APPROVAL,
    ]:
        taxsystem_request_icons += get_payments_approve_button(payment=payment)
        taxsystem_request_icons += get_payments_reject_button(payment=payment)
    # Only show undo button for approved/rejected payments
    if payment.request_status in [
        PaymentRequestStatus.APPROVED,
        PaymentRequestStatus.REJECTED,
    ]:
        taxsystem_request_icons += get_payments_undo_button(payment=payment)
    # Only show delete button for custom payments (not linked to an Wallet Entry)
    if payment.entry_id is None:
        taxsystem_request_icons += get_payments_delete_button(payment=payment)
    # Always show info button
    taxsystem_request_icons += get_payments_info_button(payment=payment)
    taxsystem_request_icons += "</div>"
    return taxsystem_request_icons


@permissions_required(
    [
        "taxsystem.manage_own_corp",
        "taxsystem.manage_corps",
        "taxsystem.manage_own_alliance",
        "taxsystem.manage_alliances",
    ]
)
def get_filter_set_action_icons(
    request: WSGIRequest,  # pylint: disable=unused-argument
    filter_set: CorporationFilterSet | AllianceFilterSet,
):
    """
    Generate HTML Action Icons for Manage Filter Set View.

    This function creates a set of action icons for managing Tax System Filter Sets.
    The Buttons include Edit, Delete, and View Filter Sets, each represented by an icon depending on User's permissions.

    Args:
        request (WSGIRequest): The HTTP request object containing user information.
        filter_set (CorporationFilterSet | AllianceFilterSet): The filter set object.
    Returns:
        String: HTML string containing the action icons.
    """
    taxsystem_request_icons = "<div class='d-flex justify-content-end'>"
    taxsystem_request_icons += get_filter_set_info_button(filter_set=filter_set)
    taxsystem_request_icons += get_filter_set_switch_button(filter_set=filter_set)
    taxsystem_request_icons += get_filter_set_delete_button(filter_set=filter_set)
    taxsystem_request_icons += "</div>"
    return taxsystem_request_icons


def get_filter_set_info_button(
    filter_set: CorporationFilterSet | AllianceFilterSet,
) -> str:
    """
    Generate a Filter Set Info button for the Manage Filter View.

    This function creates a HTML info button for viewing a given Filter Set object.
    When clicked, it triggers a modal to display detailed information about the Filter Set.

    Args:
        filter_set (CorporationFilterSet | AllianceFilterSet): The filter set object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the delete Request
    button_request_info_url = reverse(
        "taxsystem:api:get_filter",
        kwargs={
            "filterset_pk": filter_set.pk,
            "owner_id": filter_set.owner.eve_id,
        },
    )

    # Define the icon and tooltip for the delete button
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("View Filter Set")
    color = "primary"

    # Create the HTML for the delete icon button
    filter_set_info_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-view-filter-set" '
        f'title="{title}">{icon}</button>'
    )
    return filter_set_info_button


def get_filter_set_switch_button(
    filter_set: CorporationFilterSet | AllianceFilterSet,
) -> str:
    """
    Generate a Filter Set Switch for the Manage Filter View.

    This function creates a HTML Switch button for switching Filter Sets Status depending on it's current state.
    When clicked, it toggles the active state of the Filter Set.

    Args:
        filter_set (CorporationFilterSet | AllianceFilterSet): The filter set object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the delete Request
    button_request_switch_url = reverse(
        "taxsystem:api:switch_filter_set",
        kwargs={
            "filterset_pk": filter_set.pk,
            "owner_id": filter_set.owner.eve_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "warning"
    if filter_set.enabled:
        icon = '<i class="fa-solid fa-eye-low-vision"></i>'
        title = _("Deactivate Filter Set")
    else:
        icon = '<i class="fa-solid fa-eye"></i>'
        title = _("Activate Filter Set")

    # Create the HTML for the delete icon button
    filter_set_info_button = (
        '<button id="taxsystem-switch-filter-set-button" '
        f'data-action="{button_request_switch_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-tooltip="aa-taxsystem" '
        f'title="{title}">{icon}</button>'
    )
    return filter_set_info_button


def get_filter_set_delete_button(
    filter_set: CorporationFilterSet | AllianceFilterSet,
) -> str:
    """
    Generate a Filter Set Delete button for the Manage Filter View.

    This function creates a HTML delete button for deleting a given Filter Set object.
    When clicked, it triggers a modal to confirm the deletion of the Filter Set.

    Args:
        filter_set (CorporationFilterSet | AllianceFilterSet): The filter set object to be deleted.
    Returns:
        String: HTML string containing the delete button.
    """

    # Generate the URL for the delete Request
    button_request_delete_url = reverse(
        viewname="taxsystem:api:delete_filter_set",
        kwargs={
            "filterset_pk": filter_set.pk,
            "owner_id": filter_set.owner.eve_id,
        },
    )

    # Define the icon and tooltip for the delete button
    icon = '<i class="fa-solid fa-trash"></i>'
    title = _("Delete Filter Set")
    color = "danger"

    # Create the HTML for the delete icon button
    filter_set_delete_button = (
        f'<button data-action="{button_request_delete_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-delete-filter-set" '
        f'title="{title}">{icon}</button>'
    )
    return filter_set_delete_button


def get_filter_set_active_icon(
    filter_set: CorporationFilterSet | AllianceFilterSet,
) -> str:
    """
    Generate a Filter Set Active icon for the Filter Set View.

    This function creates a HTML active icon button for showing active status of a given Filter Set object

    Args:
        filter_set (CorporationFilterSet | AllianceFilterSet): The filter set object to be deleted.
    Returns:
        String: HTML string containing the delete button.
    """
    # Define the icon, color and tooltip for the active icon
    if filter_set.enabled:
        icon = '<i class="fa-solid fa-check"></i>'
        title = _("Active")
        color = "success"
    else:
        icon = '<i class="fa-solid fa-xmark"></i>'
        title = _("Inactive")
        color = "danger"
    # Create the HTML for the delete icon button
    filter_set_active_button = (
        f"<button "
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-tooltip="aa-taxsystem" '
        f'title="{title}">{icon}</button>'
    )
    return filter_set_active_button


def get_filter_delete_button(filter_obj: CorporationFilter | AllianceFilter) -> str:
    """
    Generate a Filter Delete button for the Manage Filter View.

    This function creates a HTML delete button for deleting a given Filter object.
    When clicked, it triggers a modal to confirm the deletion of the Filter, optionally loading previous modal.

    Args:
        filter_obj (CorporationFilter | AllianceFilter): The filter object to be deleted.
    Returns:
        String: HTML string containing the delete button.
    """

    # Generate the URL for the delete Request
    button_request_delete_url = reverse(
        viewname="taxsystem:api:delete_filter",
        kwargs={
            "filter_pk": filter_obj.pk,
            "owner_id": filter_obj.filter_set.owner.eve_id,
        },
    )
    # Generate the URL for reloading the Modal Data
    modal_request_url = reverse(
        "taxsystem:api:get_filter",
        kwargs={
            "filterset_pk": filter_obj.filter_set.pk,
            "owner_id": filter_obj.filter_set.owner.eve_id,
        },
    )
    # Define the icon and tooltip for the delete button
    icon = '<i class="fa-solid fa-trash"></i>'
    title = _("Delete Filter")
    color = "danger"

    # Create the HTML for the delete icon button
    filter_delete_button = (
        f'<button data-action="{button_request_delete_url}" '
        f'data-previous-modal="{modal_request_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-delete-filter" '
        f'title="{title}">{icon}</button>'
    )
    return filter_delete_button


def get_tax_account_switch_button(
    account: CorporationPaymentAccount | AlliancePaymentAccount,
) -> str:
    """
    Generate a Tax Account Switch button for the Tax System Management view.

    This function creates a HTML Switch button for switching Tax Account Status depending on it's current state.
    When clicked, it toggles the active state of the Tax Account.

    Args:
        account (CorporationPaymentAccount | AlliancePaymentAccount): The tax account object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the switch Request
    button_request_switch_url = reverse(
        "taxsystem:api:switch_tax_account",
        kwargs={
            "account_pk": account.pk,
            "owner_id": account.owner.eve_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "warning"
    if account.status == AccountStatus.ACTIVE:
        icon = '<i class="fa-solid fa-eye-low-vision"></i>'
        title = _("Deactivate Account")
    else:
        icon = '<i class="fa-solid fa-eye"></i>'
        title = _("Activate Account")

    # Create the HTML for the switch icon button
    tax_account_switch_button = (
        "<button "
        f'data-action="{button_request_switch_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-switch-tax-account" '
        f'title="{title}">{icon}</button>'
    )
    return tax_account_switch_button


def get_tax_account_add_button(
    account: CorporationPaymentAccount | AlliancePaymentAccount,
) -> str:
    """
    Generate a Add Payment button for the Tax System Management view.

    This function creates a HTML Add Payment button for adding payments to a tax account.
    When clicked, it triggers a modal to confirm the addition of a payment.

    Args:
        account (CorporationPaymentAccount | AlliancePaymentAccount): The tax account object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_switch_url = reverse(
        "taxsystem:api:add_payment",
        kwargs={
            "account_pk": account.pk,
            "owner_id": account.owner.eve_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "success"
    icon = '<i class="fa-solid fa-dollar-sign"></i>'
    title = _("Add Payment")

    # Create the HTML for the add payment icon button
    tax_account_add_button = (
        "<button "
        f'data-action="{button_request_switch_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-add-payment" '
        f'title="{title}">{icon}</button>'
    )
    return tax_account_add_button


def get_tax_account_info_button(
    account: CorporationPaymentAccount | AlliancePaymentAccount,
) -> str:
    """
    Generate a Tax Account Info button for the Tax System Management view.

    This function creates a HTML info button for viewing a Tax Account object.
    When clicked, it triggers a modal to display detailed information about the Tax Account with managing tools.

    Args:
        account (CorporationPaymentAccount | AlliancePaymentAccount): The tax account object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the delete Request
    button_request_info_url = reverse(
        "taxsystem:api:get_member_payments",
        kwargs={
            "owner_id": account.owner.eve_id,
            "character_id": account.user.profile.main_character.character_id,
        },
    )

    # Define the icon and tooltip for the info button
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("View Tax Account")
    color = "primary"

    # Create the HTML for the info icon button
    tax_account_info_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-view-tax-account" '
        f'title="{title}">{icon}</button>'
    )
    return tax_account_info_button


def get_payments_approve_button(payment: CorporationPayments | AlliancePayments) -> str:
    """
    Generate a Approve Payment button for the Payments Modal view.

    This function creates a HTML Approve Payment button for approving payments to the according tax account.
    When clicked, it triggers a modal to confirm the approval the according payment.

    Args:
        payment (CorporationPayments | AlliancePayments): The payment object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_approve_url = reverse(
        "taxsystem:api:approve_payment",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "payment_pk": payment.pk,
        },
    )
    # Generate the URL for reloading the Modal Data
    modal_request_url = reverse(
        "taxsystem:api:get_member_payments",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "character_id": payment.account.user.profile.main_character.character_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "success"
    icon = '<i class="fa-solid fa-check"></i>'
    title = _("Approve Payment")

    # Create the HTML for the add payment icon button
    payments_approve_button = (
        "<button "
        f'data-action="{button_request_approve_url}" '
        f'data-previous-modal="{modal_request_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-approve-payment" '
        f'title="{title}">{icon}</button>'
    )
    return payments_approve_button


def get_payments_undo_button(payment: CorporationPayments | AlliancePayments) -> str:
    """
    Generate a Undo Payment button for the Payments Modal view.

    This function creates a HTML Undo Payment button for undoing payments to the according tax account.
    When clicked, it triggers a modal to confirm the undo the according payment.

    Args:
        payment (CorporationPayments | AlliancePayments): The payment object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_undo_url = reverse(
        "taxsystem:api:undo_payment",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "payment_pk": payment.pk,
        },
    )
    # Generate the URL for reloading the Modal Data
    modal_request_url = reverse(
        "taxsystem:api:get_member_payments",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "character_id": payment.account.user.profile.main_character.character_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "warning"
    icon = '<i class="fa-solid fa-undo"></i>'
    title = _("Undo Payment")

    # Create the HTML for the add payment icon button
    payments_undo_button = (
        "<button "
        f'data-action="{button_request_undo_url}" '
        f'data-previous-modal="{modal_request_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-undo-payment" '
        f'title="{title}">{icon}</button>'
    )
    return payments_undo_button


def get_payments_info_button(payment: CorporationPayments | AlliancePayments) -> str:
    """
    Generate a Information Payment button for the Payments Modal view.

    This function creates a HTML Information Payment button for viewing information about the according payment.
    When clicked, it triggers a modal to display detailed payment information.

    Args:
        payment (CorporationPayments | AlliancePayments): The payment object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_info_url = reverse(
        "taxsystem:api:get_payment_details",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "payment_pk": payment.pk,
        },
    )
    # Generate the URL for reloading the Modal Data
    modal_request_url = reverse(
        "taxsystem:api:get_member_payments",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "character_id": payment.account.user.profile.main_character.character_id,
        },
    )

    # Define the icon, color and tooltip for the info button
    color = "primary"
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("Show Details")

    # Create the HTML for the info icon button
    payments_info_button = (
        "<button "
        f'data-action="{button_request_info_url}" '
        f'data-previous-modal="{modal_request_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-view-payment-details" '
        f'title="{title}">{icon}</button>'
    )
    return payments_info_button


def get_payments_delete_button(payment: CorporationPayments | AlliancePayments) -> str:
    """
    Generate a Delete Payment button for the Payments Modal view.

    This function creates a HTML Delete Payment button for deleting payments to the according tax account.
    When clicked, it triggers a modal to confirm the deletion of the according payment.

    Args:
        payment (CorporationPayments | AlliancePayments): The payment object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_delete_url = reverse(
        "taxsystem:api:delete_payment",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "payment_pk": payment.pk,
        },
    )
    # Generate the URL for reloading the Modal Data
    modal_request_url = reverse(
        "taxsystem:api:get_member_payments",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "character_id": payment.account.user.profile.main_character.character_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "danger"
    icon = '<i class="fa-solid fa-trash"></i>'
    title = _("Delete Payment")

    # Create the HTML for the delete payment icon button
    payments_delete_button = (
        "<button "
        f'data-action="{button_request_delete_url}" '
        f'data-previous-modal="{modal_request_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-delete-payment" '
        f'title="{title}">{icon}</button>'
    )
    return payments_delete_button


def get_payments_reject_button(payment: CorporationPayments | AlliancePayments) -> str:
    """
    Generate a Reject Payment button for the Payments Modal view.

    This function creates a HTML Reject Payment button for rejecting payments to the according tax account.
    When clicked, it triggers a modal to confirm the rejection of the according payment.

    Args:
        payment (CorporationPayments | AlliancePayments): The payment object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_reject_url = reverse(
        "taxsystem:api:reject_payment",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "payment_pk": payment.pk,
        },
    )
    # Generate the URL for reloading the Modal Data
    modal_request_url = reverse(
        "taxsystem:api:get_member_payments",
        kwargs={
            "owner_id": payment.account.owner.eve_id,
            "character_id": payment.account.user.profile.main_character.character_id,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "danger"
    icon = '<i class="fa-solid fa-xmark"></i>'
    title = _("Reject Payment")

    # Create the HTML for the reject payment icon button
    payments_reject_button = (
        "<button "
        f'data-action="{button_request_reject_url}" '
        f'data-previous-modal="{modal_request_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-reject-payment" '
        f'title="{title}">{icon}</button>'
    )
    return payments_reject_button


def get_members_delete_button(member: Members) -> str:
    """
    Generate a Delete Member button for the Tax System Manage view.

    This function creates a HTML Delete Member button for deleting members in the Tax System Manage view.
    When clicked, it triggers a modal to confirm the deletion of the according member.

    Args:
        member (Members): The payment object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the add payment Request
    button_request_delete_url = reverse(
        "taxsystem:api:delete_member",
        kwargs={
            "owner_id": member.owner.eve_id,
            "member_pk": member.pk,
        },
    )

    # Define the icon, color and tooltip for the delete button
    color = "danger"
    icon = '<i class="fa-solid fa-trash"></i>'
    title = _("Delete Payment")

    # Create the HTML for the delete member icon button
    members_delete_button = (
        "<button "
        f'data-action="{button_request_delete_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-taxsystem" '
        'data-bs-target="#taxsystem-accept-delete-member" '
        f'title="{title}">{icon}</button>'
    )
    return members_delete_button

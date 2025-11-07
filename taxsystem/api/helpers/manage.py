# Django
from django.core.handlers.wsgi import WSGIRequest
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# AA TaxSystem
from taxsystem.api.helpers import core
from taxsystem.models.tax import Members, Payments


def manage_payments(request: WSGIRequest, perms: str, payment: Payments) -> str:
    """Generate the management action buttons for a payment"""
    # Create the action buttons
    actions = []
    if perms:
        if payment.is_pending or payment.is_needs_approval:
            actions.append(generate_payment_approve_button(payment=payment))
            actions.append(generate_payment_reject_button(payment=payment))
        elif payment.is_approved or payment.is_rejected:
            actions.append(generate_payment_undo_button(payment=payment))
        if payment.entry_id == 0:
            # Only allow deleting payments that are not ESI recorded
            actions.append(generate_payment_delete_button(payment=payment))
    # Get Payment Info Button
    if payment.account.user == request.user or perms:
        actions.append(core.generate_info_button(payment=payment))

    return format_html(
        f'<div class="d-flex justify-content-end">{format_html("".join(actions))}</div>'
    )


def generate_payment_approve_button(payment: Payments) -> mark_safe:
    """Generate a payment approve button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/payment-approve.html",
            {
                "payment": payment,
            },
        )
    )


def generate_payment_reject_button(payment: Payments) -> mark_safe:
    """Generate a payment reject button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/payment-reject.html",
            {
                "payment": payment,
            },
        )
    )


def generate_payment_undo_button(payment: Payments) -> mark_safe:
    """Generate a payment undo button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/payment-undo.html",
            {
                "payment": payment,
            },
        )
    )


def generate_payment_delete_button(payment: Payments) -> mark_safe:
    """Generate a payment delete button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/payment-delete.html",
            {
                "payment": payment,
            },
        )
    )


def generate_member_delete_button(member: Members) -> mark_safe:
    """Generate a member delete button for the tax system"""
    return format_html(
        render_to_string(
            "taxsystem/partials/buttons/member-delete.html",
            {
                "member": member,
            },
        )
    )

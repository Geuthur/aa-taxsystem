from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button, generate_settings
from taxsystem.models.tax import Payments


def _payments_actions(corporation_id, payment: Payments, perms, request):
    # Check if user has permission to view the actions
    if not perms:
        return ""

    template = "taxsystem/partials/form/button.html"
    amount = intcomma(payment.amount)
    confirm_text = (
        _("Are you sure to Confirm")
        + f"?<br><span class='fw-bold'>{amount} ISK (ID: {payment.pk}) "
        + _("from")
        + f" {payment.account.name}</span>"
    )

    actions = []
    if payment.is_pending or payment.is_needs_approval:
        url = reverse(
            viewname="taxsystem:approve_payment",
            kwargs={
                "corporation_id": corporation_id,
                "payment_pk": payment.pk,
            },
        )
        approve = generate_settings(
            title=_("Approve Payment"),
            icon="fas fa-check",
            color="success",
            text=confirm_text,
            modal="payments-approve",
            action=url,
            ajax="action",
        )
        urlreject = reverse(
            viewname="taxsystem:reject_payment",
            kwargs={
                "corporation_id": corporation_id,
                "payment_pk": payment.pk,
            },
        )
        rejectsettings = generate_settings(
            title=_("Reject Payment"),
            icon="fas fa-times",
            color="danger",
            text=confirm_text,
            modal="payments-reject",
            action=urlreject,
            ajax="action",
        )
        actions.append(
            generate_button(corporation_id, template, payment, rejectsettings, request)
        )
        actions.append(
            generate_button(corporation_id, template, payment, approve, request)
        )
    elif payment.is_approved or payment.is_rejected:
        url = reverse(
            viewname="taxsystem:undo_payment",
            kwargs={
                "corporation_id": corporation_id,
                "payment_pk": payment.pk,
            },
        )
        settings = {
            "title": _("Undo Payment") if payment.is_approved else _("Undo Action"),
            "icon": "fas fa-undo",
            "color": "danger",
            "text": confirm_text,
            "modal": "payments-undo",
            "action": url,
            "ajax": "action",
        }
        actions.append(
            generate_button(corporation_id, template, payment, settings, request)
        )

    details = generate_settings(
        title=_("Payment Details"),
        icon="fas fa-info",
        color="info",
        text=_("View Payment Details"),
        modal="modalViewDetailsContainer",
        action=f"/taxsystem/api/corporation/{corporation_id}/character/{payment.account.user.profile.main_character.character_id}/payment/{payment.pk}/view/details/",
        ajax="ajax_details",
    )
    actions.append(generate_button(corporation_id, template, payment, details, request))

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

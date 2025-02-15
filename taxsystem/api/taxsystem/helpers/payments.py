from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button, generate_settings
from taxsystem.models.tax import Payments


# pylint: disable=too-many-arguments, too-many-positional-arguments
def generate_action_settings(
    corporation_id, payment, action_type, icon, color, modal, viewname, request
):
    url = reverse(
        viewname=viewname,
        kwargs={
            "corporation_id": corporation_id,
            "payment_pk": payment.pk,
        },
    )
    amount = intcomma(payment.amount, use_l10n=True)
    text = (
        _(f"{action_type} Payment")
        + f" {amount} ISK "
        + _("from")
        + f" {payment.account.user.username}"
    )
    settings = generate_settings(
        title=_(f"{action_type} Payment"),
        icon=icon,
        color=color,
        text=text,
        modal=modal,
        action=url,
        ajax="action",
    )
    return generate_button(
        corporation_id,
        "taxsystem/partials/form/button.html",
        payment,
        settings,
        request,
    )


def _payments_actions(corporation_id, payment: Payments, perms, request):
    # Check if user has permission to view the actions
    if not perms:
        return ""

    actions = []
    if payment.is_pending or payment.is_needs_approval:
        actions.append(
            generate_action_settings(
                corporation_id,
                payment,
                "Approve",
                "fas fa-check",
                "success",
                "payments-approve",
                "taxsystem:approve_payment",
                request,
            )
        )
        actions.append(
            generate_action_settings(
                corporation_id,
                payment,
                "Reject",
                "fas fa-times",
                "danger",
                "payments-reject",
                "taxsystem:reject_payment",
                request,
            )
        )
    elif payment.is_approved or payment.is_rejected:
        actions.append(
            generate_action_settings(
                corporation_id,
                payment,
                "Undo",
                "fas fa-undo",
                "danger",
                "payments-undo",
                "taxsystem:undo_payment",
                request,
            )
        )

    details = generate_settings(
        title=_("Payment Details"),
        icon="fas fa-info",
        color="primary",
        text=_("View Payment Details"),
        modal="modalViewDetailsContainer",
        action=f"/taxsystem/api/corporation/{corporation_id}/character/{payment.account.user.profile.main_character.character_id}/payment/{payment.pk}/view/details/",
        ajax="ajax_details",
    )
    actions.append(
        generate_button(
            corporation_id,
            "taxsystem/partials/form/button.html",
            payment,
            details,
            request,
        )
    )

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

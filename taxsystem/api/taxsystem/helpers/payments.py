from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button, generate_settings, get_info_button
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
    actions = []
    if perms:
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
                    corporation_id=corporation_id,
                    payment=payment,
                    action_type="Undo",
                    icon="fas fa-undo",
                    color="danger",
                    modal="payments-undo",
                    viewname="taxsystem:undo_payment",
                    request=request,
                )
            )
    if payment.account.user == request.user or perms:
        actions.append(get_info_button(corporation_id, payment, request))

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

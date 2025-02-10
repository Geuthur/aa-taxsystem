from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button
from taxsystem.models.tax import Payments


def _payments_actions(corporation_id, payment: Payments, perms, request):
    actions = []
    if not perms:
        return actions

    template = "taxsystem/forms/standard/confirm.html"
    amount = intcomma(payment.amount)
    confirm_text = (
        _("Are you sure to Confirm")
        + f"?<br><span class='fw-bold'>{amount} ISK (ID: {payment.pk}) "
        + _("from")
        + f" {payment.payment_user.name}</span>"
    )

    if payment.is_pending or payment.is_needs_approval:
        url = reverse(
            viewname="taxsystem:approve_payment",
            kwargs={
                "corporation_id": corporation_id,
                "payment_pk": payment.pk,
            },
        )
        settings = {
            "icon": "fas fa-check",
            "color": "success",
            "confirm_text": confirm_text,
            "title": _("Approve Payment"),
            "action": url,
        }

        urldecline = reverse(
            viewname="taxsystem:decline_payment",
            kwargs={
                "corporation_id": corporation_id,
                "payment_pk": payment.pk,
            },
        )

        settingsdecline = {
            "icon": "fas fa-times",
            "color": "danger",
            "confirm_text": confirm_text,
            "title": _("Decline Payment"),
            "action": urldecline,
        }
        actions.append(
            generate_button(corporation_id, template, payment, settingsdecline, request)
        )
        actions.append(
            generate_button(corporation_id, template, payment, settings, request)
        )
    elif payment.is_paid:
        url = reverse(
            viewname="taxsystem:undo_payment",
            kwargs={
                "corporation_id": corporation_id,
                "payment_pk": payment.pk,
            },
        )
        settings = {
            "icon": "fas fa-undo",
            "color": "danger",
            "confirm_text": confirm_text,
            "title": _("Undo Payment"),
            "action": url,
        }
        actions.append(
            generate_button(corporation_id, template, payment, settings, request)
        )

    if actions:
        actions_html = format_html("".join(actions))
        return format_html(
            '<div class="d-flex justify-content-end">{}</div>', actions_html
        )
    return actions

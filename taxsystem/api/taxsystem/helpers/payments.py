# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api.helpers import generate_button, get_info_button
from taxsystem.models.tax import Payments


def _payments_actions(corporation_id, payment: Payments, perms, request):
    actions = []
    if perms:
        amount = intcomma(payment.amount, use_l10n=True)
        if payment.is_pending or payment.is_needs_approval:
            actions.append(
                generate_button(
                    corporation_id=corporation_id,
                    template="taxsystem/partials/form/button.html",
                    queryset=payment,
                    settings={
                        "title": _("Approve Payment"),
                        "icon": "fas fa-check",
                        "color": "success",
                        "text": _("Approve Payment")
                        + f" {amount} ISK "
                        + _("from")
                        + f" {payment.account.user.username}",
                        "modal": "payments-approve",
                        "action": reverse(
                            viewname="taxsystem:approve_payment",
                            kwargs={
                                "corporation_id": corporation_id,
                                "payment_pk": payment.pk,
                            },
                        ),
                        "ajax": "action",
                    },
                    request=request,
                )
            )
            actions.append(
                generate_button(
                    corporation_id=corporation_id,
                    template="taxsystem/partials/form/button.html",
                    queryset=payment,
                    settings={
                        "title": _("Reject Payment"),
                        "icon": "fas fa-times",
                        "color": "danger",
                        "text": _("Reject Payment")
                        + f" {amount} ISK "
                        + _("from")
                        + f" {payment.account.user.username}",
                        "modal": "payments-reject",
                        "action": reverse(
                            viewname="taxsystem:reject_payment",
                            kwargs={
                                "corporation_id": corporation_id,
                                "payment_pk": payment.pk,
                            },
                        ),
                        "ajax": "action",
                    },
                    request=request,
                )
            )
        elif payment.is_approved or payment.is_rejected:
            actions.append(
                generate_button(
                    corporation_id=corporation_id,
                    template="taxsystem/partials/form/button.html",
                    queryset=payment,
                    settings={
                        "title": _("Undo Payment"),
                        "icon": "fas fa-undo",
                        "color": "danger",
                        "text": _("Undo Payment")
                        + f" {amount} ISK "
                        + _("from")
                        + f" {payment.account.user.username}",
                        "modal": "payments-undo",
                        "action": reverse(
                            viewname="taxsystem:undo_payment",
                            kwargs={
                                "corporation_id": corporation_id,
                                "payment_pk": payment.pk,
                            },
                        ),
                        "ajax": "action",
                    },
                    request=request,
                )
            )
    if payment.account.user == request.user or perms:
        actions.append(get_info_button(corporation_id, payment, request))

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

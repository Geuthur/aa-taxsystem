# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api.helpers import generate_button, get_info_button
from taxsystem.models.tax import Payments


def _approve_payment(actions: list, corporation_id: int, payment: Payments, request):
    amount = intcomma(payment.amount, use_l10n=True)
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


def _reject_payment(actions: list, corporation_id: int, payment: Payments, request):
    amount = intcomma(payment.amount, use_l10n=True)
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


def _undo_payment(actions: list, corporation_id: int, payment: Payments, request):
    amount = intcomma(payment.amount, use_l10n=True)
    actions.append(
        generate_button(
            corporation_id=corporation_id,
            template="taxsystem/partials/form/button.html",
            queryset=payment,
            settings={
                "title": _("Undo Payment"),
                "icon": "fas fa-undo",
                "color": "warning",
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


def _delete_payment(actions: list, corporation_id: int, payment: Payments, request):
    amount = intcomma(payment.amount, use_l10n=True)
    actions.append(
        generate_button(
            corporation_id=corporation_id,
            template="taxsystem/partials/form/button.html",
            queryset=payment,
            settings={
                "title": _("Delete Payment"),
                "icon": "fas fa-trash",
                "color": "danger",
                "text": _("Delete Payment")
                + f" {amount} ISK "
                + _("from")
                + f" {payment.account.user.username}",
                "modal": "payments-delete",
                "action": reverse(
                    viewname="taxsystem:delete_payment",
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


def payments_actions(corporation_id, payment: Payments, perms, request):
    actions = []
    if perms:
        if payment.is_pending or payment.is_needs_approval:
            _approve_payment(actions, corporation_id, payment, request)
            _reject_payment(actions, corporation_id, payment, request)
        elif payment.is_approved or payment.is_rejected:
            _undo_payment(actions, corporation_id, payment, request)
    if payment.account.user == request.user or perms:
        # Only allow deleting payments that are not ESI recorded
        if payment.entry_id == 0:
            _delete_payment(actions, corporation_id, payment, request)

        actions.append(get_info_button(corporation_id, payment, request))

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

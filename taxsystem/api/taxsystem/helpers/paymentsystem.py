# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api.helpers import generate_button, generate_settings
from taxsystem.models.tax import PaymentSystem


def _payments_info(corporation_id, user: PaymentSystem, perms, request):
    if not perms:
        return ""

    view_payments = generate_button(
        corporation_id,
        "taxsystem/partials/form/button.html",
        user,
        {
            "title": _("View Payments"),
            "icon": "fas fa-info",
            "color": "primary",
            "text": _("View Payments"),
            "modal": "modalViewPaymentsContainer",
            "action": f"/taxsystem/api/corporation/{corporation_id}/character/{user.user.profile.main_character.character_id}/view/payments/",
            "ajax": "ajax_payments",
        },
        request,
    )

    return format_html(f"{intcomma(user.deposit, use_l10n=True)} ISK {view_payments}")


def _payment_system_actions(
    corporation_id, payment_system: PaymentSystem, perms, request
):
    # Check if user has permission to view the actions
    if not perms:
        return ""

    template = "taxsystem/partials/form/button.html"
    url = reverse(
        viewname="taxsystem:switch_user",
        kwargs={
            "corporation_id": corporation_id,
            "payment_system_pk": payment_system.pk,
        },
    )

    if payment_system.is_active:
        confirm_text = (
            _("Are you sure to Confirm")
            + f"?<br><span class='fw-bold'>{payment_system.name} "
            + _("Deactivate")
            + "</span>"
        )
        title = _("Deactivate User")
        icon = "fas fa-eye-low-vision"
        color = "warning"
    else:
        confirm_text = (
            _("Are you sure to Confirm")
            + f"?<br><span class='fw-bold'>{payment_system.name} "
            + _("Activate")
            + "</span>"
        )
        title = _("Activate User")
        icon = "fas fa-eye"
        color = "success"

    settings = generate_settings(
        title=title,
        icon=icon,
        color=color,
        text=confirm_text,
        modal="paymentsystem-switchuser",
        action=url,
        ajax="action",
    )
    # Generate the buttons
    actions = []
    actions.append(
        generate_button(corporation_id, template, payment_system, settings, request)
    )

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

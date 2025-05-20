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


def _payment_system_actions(corporation_id, user: PaymentSystem, perms, request):
    # Check if user has permission to view the actions
    if not perms:
        return ""

    template = "taxsystem/partials/form/button.html"
    url = reverse(
        viewname="taxsystem:switch_user",
        kwargs={"corporation_id": corporation_id, "user_pk": user.pk},
    )

    if user.is_active:
        confirm_text = (
            _("Are you sure to Confirm")
            + f"?<br><span class='fw-bold'>{user.name} "
            + _("Deactivate")
            + "</span>"
        )
        title = _("Deactivate User")
        icon = "fas fa-eye-low-vision"
        color = "warning"
    else:
        confirm_text = (
            _("Are you sure to Confirm")
            + f"?<br><span class='fw-bold'>{user.name} "
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
    actions.append(generate_button(corporation_id, template, user, settings, request))

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)


def _get_has_paid_icon(user: PaymentSystem) -> dict:
    if user.is_active:
        has_paid_filter = _("Yes") if user.has_paid else _("No")
        if user.has_paid:
            button = format_html(
                '<button class="btn btn-success btn-sm d-flex align-items-center justify-content-center" '
                'style="height: 30px; width: 30px;" title="{}" data-tooltip-toggle="taxsystem-tooltip">'
                '<i class="fas fa-check"></i></button>',
                _("Paid"),
            )
        else:
            button = format_html(
                '<button class="btn btn-danger btn-sm d-flex align-items-center justify-content-center" '
                'style="height: 30px; width: 30px;" title="{}" data-tooltip-toggle="taxsystem-tooltip">'
                '<i class="fas fa-times"></i></button>',
                _("Unpaid"),
            )
        has_paid = {
            "display": button,
            "sort": has_paid_filter,
            "raw": user.has_paid,
        }
    else:
        button = format_html(
            '<button class="btn btn-warning btn-sm d-flex align-items-center justify-content-center" '
            'style="height: 30px; width: 30px;" title="{}" data-tooltip-toggle="taxsystem-tooltip">'
            '<i class="fas fa-user-slash"></i></button>',
            _("Inactive"),
        )
        has_paid_filter = ""
        has_paid = {
            "display": button,
            "sort": "",
            "raw": "",
        }
    return has_paid

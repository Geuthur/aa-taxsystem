from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button
from taxsystem.models.tax import PaymentSystem


def _payment_system_actions(corporation_id, user: PaymentSystem, perms, request):
    if not perms:
        return ""

    template = "taxsystem/partials/form/button.html"
    confirm_text = ""
    confirm_text += _("Are you sure to Confirm")
    confirm_text += (
        f"?<br><span class='fw-bold'>{user.name} " + _("Deactivate") + "</span>"
    )
    url = reverse(
        viewname="taxsystem:switch_user",
        kwargs={"corporation_id": corporation_id, "user_pk": user.pk},
    )
    if user.is_active:
        title = _("Deactivate User")
        settings = {
            "title": title,
            "icon": "fas fa-eye-low-vision",
            "color": "warning",
            "text": confirm_text,
            "modal": "paymentsystem-switchuser",
            "action": url,
        }
    else:
        confirm_text = ""
        confirm_text += _("Are you sure to Confirm")
        confirm_text += (
            f"?<br><span class='fw-bold'>{user.name} " + _("Activate") + "</span>"
        )
        title = _("Activate User")
        settings = {
            "title": title,
            "icon": "fas fa-eye",
            "color": "success",
            "text": confirm_text,
            "modal": "paymentsystem-switchuser",
            "action": url,
        }
    return generate_button(corporation_id, template, user, settings, request)


def _get_has_paid_icon(user: PaymentSystem) -> dict:
    if user.is_active:
        has_paid_filter = _("Yes") if user.has_paid else _("No")
        if user.has_paid:
            button = format_html(
                '<button class="btn btn-success btn-sm d-flex align-items-center justify-content-center" style="height: 30px; width: 30px;"><i class="fas fa-check"></i></button>'
            )
        else:
            button = format_html(
                '<button class="btn btn-danger btn-sm d-flex align-items-center justify-content-center" style="height: 30px; width: 30px;"><i class="fas fa-times"></i></button>'
            )
        has_paid = {
            "display": button,
            "sort": has_paid_filter,
            "raw": user.has_paid,
        }
    else:
        button = format_html(
            '<button class="btn btn-warning btn-sm d-flex align-items-center justify-content-center" style="height: 30px; width: 30px;"><i class="fas fa-user-slash"></i></button>'
        )
        has_paid_filter = ""
        has_paid = {
            "display": button,
            "sort": "",
            "raw": "",
        }
    return has_paid

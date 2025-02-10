from django.urls import reverse
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button
from taxsystem.models.tax import PaymentSystem


def _payment_system_actions(corporation_id, user: PaymentSystem, perms, request):
    if not perms:
        return ""

    template = "taxsystem/forms/standard/confirm.html"
    url = reverse(
        viewname="taxsystem:switch_user",
        kwargs={"corporation_id": corporation_id, "user_pk": user.pk},
    )
    if user.is_active:
        confirm_text = (
            _("Are you sure to Confirm")
            + f"?<br><span class='fw-bold'>Deactivate {user.name} (ID: {user.pk}) "
        )
        title = _("Deactivate User")
        settings = {
            "title": title,
            "icon": "fas fa-eye-low-vision",
            "color": "warning",
            "confirm_text": confirm_text,
            "action": url,
        }
    else:
        confirm_text = (
            _("Are you sure to Confirm")
            + f"?<br><span class='fw-bold'>Activate {user.name} (ID: {user.pk}) "
        )
        title = _("Activate User")
        settings = {
            "title": title,
            "icon": "fas fa-eye",
            "color": "success",
            "confirm_text": confirm_text,
            "action": url,
        }
    return generate_button(corporation_id, template, user, settings, request)

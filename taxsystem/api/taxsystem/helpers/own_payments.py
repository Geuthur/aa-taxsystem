from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button, generate_settings
from taxsystem.models.tax import Payments


def _own_payments_actions(corporation_id, payment: Payments, request):
    details = generate_settings(
        title=_("Payment Details"),
        icon="fas fa-info",
        color="primary",
        text=_("View Payment Details"),
        modal="modalViewDetailsContainer",
        action=f"/taxsystem/api/corporation/{corporation_id}/character/{payment.account.user.profile.main_character.character_id}/payment/{payment.pk}/view/details/",
        ajax="ajax_details",
    )
    button = generate_button(
        corporation_id,
        "taxsystem/partials/form/button.html",
        payment,
        details,
        request,
    )
    return format_html('<div class="d-flex justify-content-end">{}</div>', button)

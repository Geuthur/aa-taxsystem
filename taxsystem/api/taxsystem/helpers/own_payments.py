# Django
from django.utils.html import format_html
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api.helpers import get_info_button
from taxsystem.models.tax import Payments


def _own_payments_actions(corporation_id, payment: Payments, request):
    button = get_info_button(corporation_id, payment, request)
    return format_html('<div class="d-flex justify-content-end">{}</div>', button)

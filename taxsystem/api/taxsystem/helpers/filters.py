# Django
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.api.helpers import generate_button
from taxsystem.models.filters import JournalFilter


def _filter_actions(corporation_id, filter_obj: JournalFilter, perms, request):
    action = ""
    if perms:
        action = generate_button(
            corporation_id=corporation_id,
            template="taxsystem/partials/form/button.html",
            queryset=filter_obj,
            settings={
                "title": _("Delete Filter"),
                "icon": "fas fa-trash",
                "color": "danger",
                "text": _("Delete Filter"),
                "modal": "filter-set-delete-filter",
                "action": reverse(
                    viewname="taxsystem:delete_filter",
                    kwargs={
                        "corporation_id": corporation_id,
                        "filter_pk": filter_obj.pk,
                    },
                ),
                "ajax": "action",
            },
            request=request,
        )

    actions_html = format_html(action)
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)

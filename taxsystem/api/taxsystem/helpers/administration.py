from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from taxsystem.api.helpers import generate_button, generate_settings
from taxsystem.models.tax import Members


def _delete_member(corporation_id, member: Members, perms, request):
    # Check if user has permission to view the actions
    if not perms:
        return ""

    template = "taxsystem/partials/form/button.html"
    confirm_text = ""
    confirm_text += _("Are you sure to Confirm")
    url = reverse(
        viewname="taxsystem:delete_user",
        kwargs={"corporation_id": corporation_id, "member_pk": member.pk},
    )

    if member.is_missing:
        confirm_text += (
            f"?<br><span class='fw-bold'>{member.character_name} "
            + _("Delete")
            + "</span>"
        )
        title = _("Delete Member")
        icon = "fas fa-trash"
        color = "danger"

        settings = generate_settings(
            title=title,
            icon=icon,
            color=color,
            text=confirm_text,
            modal="members-delete-member",
            action=url,
            ajax="action",
        )
        # Generate the buttons
        actions = []
        actions.append(
            generate_button(corporation_id, template, member, settings, request)
        )

        actions_html = format_html("".join(actions))
        return format_html(
            '<div class="d-flex justify-content-end">{}</div>', actions_html
        )
    return ""

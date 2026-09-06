# Standard Library
import json

# Third Party
from ninja import NinjaAPI

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__, forms
from taxsystem.api import schema
from taxsystem.api.helpers import core
from taxsystem.api.helpers.icons import (
    get_groups_delete_button,
)
from taxsystem.models.helpers.textchoices import (
    ActionType,
    AdminActions,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class GroupsApiEndpoints:
    tags = ["Group Management"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/groups/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_groups(request: WSGIRequest, owner_id: int):
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            response_groups: list[schema.GroupManagementSchema] = []
            for group in owner.ts_corporation_groups.all():
                group_list: list[schema.GroupSchema] = []
                for aa_group in group.groups.all():
                    group_list.append(
                        schema.GroupSchema(
                            id=aa_group.pk,
                            name=aa_group.name,
                        )
                    )
                response_groups.append(
                    schema.GroupManagementSchema(
                        name=group.name,
                        groups=group_list,
                        actions=get_groups_delete_button(group),
                    )
                )

            return 200, response_groups

        @api.post(
            "owner/{owner_id}/groups/{group_pk}/manage/delete/",
            response={200: dict, 403: dict, 404: dict, 400: dict},
            tags=self.tags,
        )
        def delete_group(request: WSGIRequest, owner_id: int, group_pk: int):
            """
            Delete a specific group for the given owner.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner.
                group_pk (int): The primary key of the group to be deleted.
            Returns:
                200: A success message indicating the group was deleted successfully.
                403: An error message if the user does not have permission or the group is not found.
                404: An error message if the group does not exist.
                400: An error message if the form data is invalid.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Validate the form data
            form = forms.DeleteGroupForm(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            try:
                group = owner.ts_corporation_groups.get(pk=group_pk)
                group.delete()

                # Create log message
                msg = format_lazy(
                    _("{group_obj} deleted - Reason: {reason}"),
                    group_obj=group,
                    reason=form.cleaned_data["comment"],
                )
                # Log the deletion in Admin History
                owner.admin_log_model(
                    user=request.user,
                    owner=owner,
                    target=ActionType.GROUP,
                    action=AdminActions.DELETE,
                    comment=msg,
                ).save()

                return 200, {"success": True, "message": msg}
            except ObjectDoesNotExist:
                return 404, {"error": _("Group not Found.")}

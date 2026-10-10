# Third Party
from ninja import NinjaAPI

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.groupmanagement.models import Group
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api import schema
from taxsystem.api.helpers import core
from taxsystem.models.corporation import CorporationOwner
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
            response={
                200: list[schema.GroupManagementSchema],
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
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
            for group in owner.group_model.objects.filter(owner=owner):
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
                        id=group.pk,
                        name=group.name,
                        groups=group_list,
                    )
                )

            return 200, response_groups

        @api.post(
            "owner/{owner_id}/groups/{group_pk}/manage/delete/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def delete_group(
            request: WSGIRequest,
            owner_id: int,
            group_pk: int,
            payload: schema.ActionCommentRequest = schema.ActionCommentRequest(),
        ):
            """
            Delete a specific group for the given owner.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner.
                group_pk (int): The primary key of the group to be deleted.
                payload (ActionCommentRequest): The action comment request payload.
            Returns:
                200: A success message indicating the group was deleted successfully.
                403: An error message if the user does not have permission or the group is not found.
                404: An error message if the group does not exist.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            try:
                group = owner.group_model.objects.get(pk=group_pk, owner=owner)
                group.delete()

                # Create log message
                msg = format_lazy(
                    _("{group_obj} deleted - Reason: {reason}"),
                    group_obj=group,
                    reason=payload.comment,
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

        @api.get(
            "owner/{owner_id}/groups/available/",
            response={
                200: list[schema.GroupSchema],
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
            tags=self.tags,
        )
        def get_available_groups(request: WSGIRequest, owner_id: int):
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            groups = Group.objects.order_by("name")
            return 200, [schema.GroupSchema(id=g.pk, name=g.name) for g in groups]

        @api.post(
            "owner/{owner_id}/groups/create/",
            response={
                200: schema.MessageSchema,
                400: schema.ErrorSchema,
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
            tags=self.tags,
        )
        def create_group(
            request: WSGIRequest, owner_id: int, payload: schema.CreateGroupRequest
        ):
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            if not isinstance(owner, CorporationOwner):
                return 400, {
                    "error": _("Groups are only supported for Corporation owners.")
                }

            name = payload.name.strip()
            if not name:
                return 400, {"error": _("Group name is required.")}

            if owner.group_model.objects.filter(name=name, owner=owner).exists():
                return 400, {"error": _("A group with this name already exists.")}

            group = owner.group_model.objects.create(name=name, owner=owner)
            if payload.group_ids:
                group.groups.set(payload.group_ids)

            msg = format_lazy(_('Tax free group "{name}" created.'), name=group.name)
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                target=ActionType.GROUP,
                action=AdminActions.ADD,
                comment=msg,
            ).save()

            return 200, schema.MessageSchema(message=str(msg))

# Standard Library
import json

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.icons import (
    get_members_delete_button,
)
from taxsystem.api.schema import (
    CharacterSchema,
    MembersSchema,
)
from taxsystem.forms import DeleteMemberForm
from taxsystem.helpers import lazy
from taxsystem.models.alliance import (
    AllianceOwner,
)
from taxsystem.models.corporation import (
    CorporationOwner,
    Members,
)
from taxsystem.models.helpers.textchoices import AdminActions

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/view/members/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_members(request, owner_id: int):
            """
            This Endpoint retrieves the members of the according Owner.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose members are to be retrieved.
            Returns:
                MembersResponse: A response object containing the list of members.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Handle Alliance Members or Corporation Members
            if isinstance(owner, AllianceOwner):
                members = Members.objects.filter(
                    owner__eve_corporation__alliance__alliance_id=owner_id
                )
            else:
                members = (
                    Members.objects.filter(owner=owner)
                    .select_related("owner")
                    .order_by("character_name")
                )

            response_members_list: list[MembersSchema] = []
            for member in members:
                actions = ""
                # Create the delete button if member is missing and is Corporation Owner
                if perms and member.is_missing and isinstance(owner, CorporationOwner):
                    actions = get_members_delete_button(member=member)

                response_member = MembersSchema(
                    character=CharacterSchema(
                        character_id=member.character_id,
                        character_name=member.character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            member.character_id, size=32, as_html=True
                        ),
                    ),
                    is_faulty=member.is_faulty,
                    status=member.get_status_display(),
                    joined=member.joined,
                    actions=actions,
                )
                response_members_list.append(response_member)
            return response_members_list

        @api.post(
            "owner/{owner_id}/member/{member_pk}/manage/delete-member/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def delete_member(request: WSGIRequest, owner_id: int, member_pk: int):
            """
            Handle an Request to Delete a Member

            This Endpoint deletes a member from an associated tax account.
            It validates the request, checks permissions, and deletes the member from the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                member_pk (int): The ID of the member to be deleted.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            # Check if owner exists
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # Check permissions
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Validate the form data
            form = DeleteMemberForm(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            reason = form.cleaned_data["comment"]

            member = Members.objects.get(owner=owner, pk=member_pk)
            if member.is_missing:
                msg = format_lazy(
                    _("Member {member} deleted - {reason}"),
                    member=member.character_name,
                    reason=reason,
                )
                member.delete()
                owner.admin_log_model(
                    user=request.user,
                    owner=owner,
                    action=AdminActions.DELETE,
                    comment=msg,
                ).save()
                return 200, {"success": True, "message": msg}
            msg = _("Member is not marked as missing.")
            return 400, {"success": False, "message": msg}

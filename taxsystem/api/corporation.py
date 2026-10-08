# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.icons import (
    get_members_delete_button,
)
from taxsystem.api.schema import (
    ActionCommentRequest,
    CharacterSchema,
    ErrorSchema,
    MembersSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.alliance import (
    AllianceOwner,
)
from taxsystem.models.corporation import (
    CorporationOwner,
    Members,
)
from taxsystem.models.helpers.textchoices import (
    ActionType,
    AdminActions,
    PaymentRequestStatus,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/view/members/",
            response={200: list[MembersSchema], 403: ErrorSchema, 404: ErrorSchema},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals, too-many-branches
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

            open_char_invoices_map = dict(
                owner.payment_model.objects.filter(
                    owner=owner,
                    request_status__in=[
                        PaymentRequestStatus.PENDING,
                        PaymentRequestStatus.NEEDS_APPROVAL,
                    ],
                )
                .values("account__user__character_ownerships__character__character_id")
                .annotate(count=Count("id", distinct=True))
                .values_list(
                    "account__user__character_ownerships__character__character_id",
                    "count",
                )
            )

            member_char_ids = [m.character_id for m in members]
            ownerships = (
                CharacterOwnership.objects.filter(
                    character__character_id__in=member_char_ids
                )
                .select_related("user__profile__main_character", "character")
                .prefetch_related("user__character_ownerships__character")
            )
            char_to_ownership: dict[int, CharacterOwnership] = {
                co.character.character_id: co for co in ownerships
            }

            user_to_corp_members: dict[int, list[Members]] = {}
            for m in members:
                co = char_to_ownership.get(m.character_id)
                if co:
                    user_to_corp_members.setdefault(co.user_id, []).append(m)

            primary_member_ids: set[int] = set()
            alt_member_ids: set[int] = set()

            for user_members in user_to_corp_members.values():
                first_co = char_to_ownership.get(user_members[0].character_id)
                main_char = (
                    getattr(
                        getattr(first_co.user, "profile", None),
                        "main_character",
                        None,
                    )
                    if first_co
                    else None
                )
                main_in_corp = (
                    next(
                        (
                            m
                            for m in user_members
                            if main_char and m.character_id == main_char.character_id
                        ),
                        None,
                    )
                    if main_char
                    else None
                )
                primary = main_in_corp if main_in_corp else user_members[0]
                primary_member_ids.add(primary.character_id)
                for m in user_members:
                    if m.character_id != primary.character_id:
                        alt_member_ids.add(m.character_id)

            response_members_list: list[MembersSchema] = []
            for member in members:
                actions = ""
                # Create the delete button if member is missing and is Corporation Owner
                if perms and member.is_missing and isinstance(owner, CorporationOwner):
                    actions = get_members_delete_button(member=member)

                co = char_to_ownership.get(member.character_id)
                member_is_alt = member.character_id in alt_member_ids or (
                    member.is_alt and member.character_id not in primary_member_ids
                )

                member_alts: list[CharacterSchema] = []
                if co and not member_is_alt:
                    for o in co.user.character_ownerships.all():
                        if o.character.character_id != member.character_id:
                            member_alts.append(
                                CharacterSchema(
                                    character_id=o.character.character_id,
                                    character_name=o.character.character_name,
                                    character_portrait=lazy.get_character_portrait_url(
                                        o.character.character_id, size=32
                                    ),
                                    corporation_id=o.character.corporation_id,
                                    corporation_name=o.character.corporation_name,
                                    corporation_ticker=o.character.corporation_ticker,
                                )
                            )

                response_member = MembersSchema(
                    character=CharacterSchema(
                        character_id=member.character_id,
                        character_name=member.character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            member.character_id, size=32
                        ),
                    ),
                    is_missing=member.is_missing,
                    is_noaccount=member.is_noaccount,
                    status=member.get_status_display(),
                    joined=member.joined,
                    actions=actions,
                    open_invoices=open_char_invoices_map.get(member.character_id, 0),
                    is_alt=member_is_alt,
                    alts=member_alts,
                )
                response_members_list.append(response_member)
            return response_members_list

        @api.post(
            "owner/{owner_id}/member/{member_pk}/manage/delete-member/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def delete_member(
            request: WSGIRequest,
            owner_id: int,
            member_pk: int,
            payload: ActionCommentRequest = ActionCommentRequest(),
        ):
            """
            Handle an Request to Delete a Member

            This Endpoint deletes a member from an associated tax account.
            It validates the request, checks permissions, and deletes the member from the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                member_pk (int): The ID of the member to be deleted.
                payload (ActionCommentRequest): Optional action comment payload.
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

            reason = payload.comment if payload else ""

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
                    target=ActionType.CORPORATION,
                    action=AdminActions.DELETE,
                    comment=msg,
                ).save()
                return 200, {"success": True, "message": msg}
            msg = _("Member is not marked as missing.")
            return 400, {"success": False, "message": msg}

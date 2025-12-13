# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
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
    get_payments_info_button,
)
from taxsystem.api.schema import (
    CharacterSchema,
    MembersSchema,
    PaymentSchema,
    RequestStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.alliance import (
    AllianceOwner,
    AlliancePayments,
)
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationPayments,
    Members,
)
from taxsystem.models.helpers.textchoices import PaymentRequestStatus

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentCorporationSchema(PaymentSchema):
    character: CharacterSchema


class MembersResponse(Schema):
    corporation: list[MembersSchema]


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/view/payments/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_payments(request: WSGIRequest, owner_id: int):
            """
            This Endpoint retrieves all payments to the accordicng owner.
            It checks for the owner's existence and the user's permissions
            before fetching and returning the payment data.

            Args:
                request (WSGIRequest): The incoming HTTP request.
                owner_id (int): The ID of the owner whose payments are to be retrieved.
            Returns:
                A list of payment data if successful, or an error message with appropriate status code.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": "Owner not Found."}

            if perms is False:
                return 403, {"error": "Permission Denied."}

            payments_instance = (
                CorporationPayments
                if isinstance(owner, CorporationOwner)
                else AlliancePayments
            )

            # Get Payments
            payments = (
                payments_instance.objects.filter(
                    account__owner=owner,
                    owner_id=owner.eve_id,
                )
                .select_related(
                    "account",
                    "account__user",
                    "account__user__profile",
                    "account__user__profile__main_character",
                )
                .order_by("-date")
            )

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                character_portrait = lazy.get_character_portrait_url(
                    payment.character_id, size=32, as_html=True
                )
                # Create the action buttons
                actions_html = get_payments_info_button(payment=payment)

                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=PaymentRequestStatus(payment.request_status).color(),
                )

                response_payment = PaymentCorporationSchema(
                    payment_id=payment.pk,
                    character=CharacterSchema(
                        character_id=payment.character_id,
                        character_name=payment.account.name,
                        character_portrait=character_portrait,
                    ),
                    amount=payment.amount,
                    date=payment.formatted_payment_date,
                    request_status=response_request_status,
                    division_name=payment.division_name,
                    reviser=payment.reviser,
                    reason=payment.reason,
                    actions=actions_html,
                )
                response_payments_list.append(response_payment)
            return response_payments_list

        @api.get(
            "owner/{owner_id}/view/my-payments/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_my_payments(request: WSGIRequest, owner_id: int):
            """
            This Endpoint retrieves all payments made by the requesting user
            according to the owner. It checks for the owner's existence
            before fetching and returning the payment data.
            Args:
                request (WSGIRequest): The incoming HTTP request.
                owner_id (int): The ID of the owner whose payments are to be retrieved.
            Returns:
                A list of payment data if successful, or an error message with appropriate status code.
            """
            owner = core.get_owner(request, owner_id)[0]

            if owner is None:
                return 404, {"error": "Owner not Found."}

            payments_instance = (
                CorporationPayments
                if isinstance(owner, CorporationOwner)
                else AlliancePayments
            )

            # Get Payments
            payments = (
                payments_instance.objects.filter(
                    account__owner=owner,
                    account__user=request.user,
                    owner_id=owner.eve_id,
                )
                .select_related(
                    "account",
                    "account__user",
                    "account__user__profile",
                    "account__user__profile__main_character",
                )
                .order_by("-date")
            )

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                character_portrait = lazy.get_character_portrait_url(
                    payment.character_id, size=32, as_html=True
                )

                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=PaymentRequestStatus(payment.request_status).color(),
                )

                response_payment = PaymentSchema(
                    payment_id=payment.pk,
                    character=CharacterSchema(
                        character_id=payment.character_id,
                        character_name=payment.account.name,
                        character_portrait=character_portrait,
                    ),
                    amount=payment.amount,
                    date=payment.formatted_payment_date,
                    request_status=response_request_status,
                    division_name=payment.division_name,
                    reviser=payment.reviser,
                    reason=payment.reason,
                )
                response_payments_list.append(response_payment)
            return response_payments_list

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

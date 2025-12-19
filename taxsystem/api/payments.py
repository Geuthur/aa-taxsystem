# Standard Library
import json

# Third Party
from humanize import intcomma
from ninja import NinjaAPI, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__, forms
from taxsystem.api.helpers import core
from taxsystem.api.helpers.icons import (
    get_taxsystem_manage_payments_action_icons,
    get_taxsystem_payments_action_icons,
)
from taxsystem.api.schema import (
    CharacterSchema,
    MembersSchema,
    OwnerSchema,
    PaymentHistorySchema,
    PaymentSchema,
    RequestStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.corporation import (
    CorporationOwner,
)
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    AdminActions,
    PaymentActions,
    PaymentRequestStatus,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class PaymentCorporationSchema(PaymentSchema):
    character: CharacterSchema


class MembersResponse(Schema):
    corporation: list[MembersSchema]


class TaxAccountSchema(Schema):
    account_id: int
    account_name: str
    account_status: str
    character: CharacterSchema
    payment_pool: int


class PaymentsDetailsResponse(Schema):
    owner: OwnerSchema
    account: TaxAccountSchema
    payment: PaymentSchema
    payment_histories: list[PaymentHistorySchema]


class PaymentsApiEndpoints:
    tags = ["Payments"]

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
            owner, perms = core.get_owner(request, owner_id)

            if owner is None:
                return 404, {"error": "Owner not Found."}

            if perms is False:
                return 403, {"error": "Permission Denied."}

            # Get Payments
            payments = (
                owner.payment_model.objects.get_visible(user=request.user, owner=owner)
                .select_related(
                    "account",
                    "account__user",
                    "account__user__profile",
                    "account__user__profile__main_character",
                )
                .order_by("-date")
            )

            # TODO for Larger datasets implement pagination and server side DataTables
            # Limit to last 10,000 payments
            payments = payments[:10000]

            response_payments_list: list[PaymentCorporationSchema] = []
            for payment in payments:
                character_portrait = lazy.get_character_portrait_url(
                    payment.character_id, size=32, as_html=True
                )
                # Create the action buttons
                actions_html = str(get_taxsystem_payments_action_icons(payment=payment))

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

            # Get Payments
            payments = (
                owner.payment_model.objects.filter(
                    owner=owner,
                    account__user=request.user,
                )
                .select_related(
                    "account",
                    "account__user",
                    "account__user__profile",
                    "account__user__profile__main_character",
                )
                .order_by("-date")
            )
            # Limit to last 10,000 payments
            payments = payments[:10000]

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
            "owner/{owner_id}/payment/{payment_pk}/view/details/",
            response={200: PaymentsDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_payment_details(request, owner_id: int, payment_pk: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            payment = get_object_or_404(owner.payment_model, pk=payment_pk)
            perms = perms or core.get_character_permissions(
                request, payment.character_id
            )

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            response_payment_histories: list[PaymentHistorySchema] = []
            payments_history = owner.payment_history_model.objects.filter(
                payment=payment,
            ).order_by("-date")

            # Create a list for the payment histories
            for log in payments_history:
                response_log = PaymentHistorySchema(
                    log_id=log.pk,
                    reviser=log.user.username if log.user else _("System"),
                    date=log.date.strftime("%Y-%m-%d %H:%M:%S"),
                    action=log.get_action_display(),
                    comment=log.comment,
                    status=log.get_new_status_display(),
                )
                response_payment_histories.append(response_log)

            # Create the tax account
            response_account = TaxAccountSchema(
                account_id=payment.account.pk,
                account_name=payment.account.name,
                account_status=AccountStatus(payment.account.status).html(),
                character=CharacterSchema(
                    character_id=payment.character_id,
                    character_name=payment.account.name,
                    character_portrait=lazy.get_character_portrait_url(
                        payment.character_id, size=32, as_html=True
                    ),
                    corporation_id=payment.account.owner.pk,
                    corporation_name=payment.account.owner.name,
                ),
                payment_pool=payment.account.deposit,
            )

            response_request_status = RequestStatusSchema(
                status=payment.get_request_status_display(),
                html=PaymentRequestStatus(payment.request_status).alert(),
            )

            # Create the payment
            response_payment = PaymentSchema(
                payment_id=payment.pk,
                amount=payment.amount,
                date=payment.formatted_payment_date,
                request_status=response_request_status,
                division_name=payment.division_name,
                reason=payment.reason,
                reviser=payment.reviser,
            )

            response_owner = OwnerSchema(
                owner_id=owner.eve_id,
                owner_name=owner.name,
            )

            payment_details_response = PaymentsDetailsResponse(
                owner=response_owner,
                account=response_account,
                payment=response_payment,
                payment_histories=response_payment_histories,
            )

            return payment_details_response

        @api.get(
            "owner/{owner_id}/character/{character_id}/view/payments/",
            response={200: list[PaymentSchema], 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_member_payments(request, owner_id: int, character_id: int):
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Corporation Not Found")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Filter payments by character
            payments = owner.payment_model.objects.filter(
                account__user__profile__main_character__character_id=character_id,
                owner=owner,
            ).order_by("-date")
            # Limit to last 10,000 payments
            payments = payments[:10000]

            response_payments_list: list[PaymentSchema] = []
            for payment in payments:
                # Create the actions
                actions_html = str(
                    get_taxsystem_manage_payments_action_icons(
                        request=request, payment=payment
                    )
                )

                # pylint: disable=duplicate-code
                # Create the request status
                response_request_status = RequestStatusSchema(
                    status=payment.get_request_status_display(),
                    color=PaymentRequestStatus(payment.request_status).color(),
                )

                response_payment = PaymentSchema(
                    payment_id=payment.pk,
                    amount=payment.amount,
                    date=payment.formatted_payment_date,
                    request_status=response_request_status,
                    division_name=payment.division_name,
                    reason=payment.reason,
                    actions=actions_html,
                    reviser=payment.reviser,
                )
                response_payments_list.append(response_payment)

            return response_payments_list

        @api.post(
            "owner/{owner_id}/account/{account_pk}/manage/add-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def add_payment(request: WSGIRequest, owner_id: int, account_pk: int):
            """
            Handle an Request to Add a custom Payment

            This Endpoint adds a custom payment for a tax account.
            It validates the request, checks permissions, and adds the payment to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                account_pk (int): The ID of the tax account to which the payment will be added.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            # Check if owner exists
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # Check permissions
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Validate the form data
            form = forms.PaymentAddForm(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            amount = form.cleaned_data["amount"]
            reason = form.cleaned_data["comment"]

            # Begin transaction
            try:
                with transaction.atomic():
                    account = owner.account_model.objects.get(
                        owner=owner, pk=account_pk
                    )
                    payment = owner.payment_model(
                        owner=owner,
                        name=account.user.username,
                        journal=None,  # Manual Entry (use NULL to allow multiple manual payments)
                        amount=amount,
                        account=account,
                        date=timezone.now(),
                        reason=reason,
                        request_status=PaymentRequestStatus.APPROVED,
                        reviser=request.user.username,
                    )

                    # Create log message
                    msg = format_lazy(
                        _("Payment ID: {pid} - Amount: {amount} - Name: {name} added"),
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )

                    payment.save()
                    account.deposit += amount
                    account.save()

                    # Log the Payment Action
                    payment.transaction_log(
                        user=request.user,
                        action=PaymentActions.PAYMENT_ADDED,
                        new_status=PaymentRequestStatus.APPROVED,
                        comment=msg,
                    ).save()

                return 200, {"success": True, "message": msg}
            except IntegrityError:
                msg = _("Transaction failed. Please try again.")
                return 400, {"success": False, "message": msg}

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/approve-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def approve_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
            """
            Handle an Request to Approve a Payment

            This Endpoint approves a payment from an associated tax account.
            It validates the request, checks permissions, and approves the payment to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                payment_pk (int): The ID of the payment to be approved.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            # Check if owner exists
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # Check permissions
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            payment_form_instance = (
                forms.AcceptCorporationPaymentForm
                if isinstance(owner, CorporationOwner)
                else forms.AcceptAlliancePaymentForm
            )

            # Validate the form data
            form = payment_form_instance(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            reason = form.cleaned_data["comment"]

            # Begin transaction
            try:
                with transaction.atomic():
                    payment = owner.payment_model.objects.get(
                        pk=payment_pk,
                    )
                    # Check if payment is pending or needs approval
                    if payment.is_pending or payment.is_needs_approval:
                        # Approve Payment
                        payment.request_status = PaymentRequestStatus.APPROVED
                        payment.reviser = (
                            request.user.profile.main_character.character_name
                        )
                        payment.save()

                        # Update Account Deposit
                        payment.account.deposit += payment.amount
                        payment.account.save()

                        # Log the Payment Action
                        payment.transaction_log(
                            user=request.user,
                            action=PaymentActions.STATUS_CHANGE,
                            comment=reason,
                            new_status=PaymentRequestStatus.APPROVED,
                        ).save()

                        # Create response message
                        msg = format_lazy(
                            _(
                                "Payment ID: {pid} - Amount: {amount} - Name: {name} approved"
                            ),
                            pid=payment.pk,
                            amount=intcomma(payment.amount),
                            name=payment.name,
                        )
                        return 200, {"success": True, "message": msg}
                    msg = _("Payment is not pending or does not need approval.")
                    return 400, {"success": True, "message": msg}
            except IntegrityError:
                msg = _("Transaction failed. Please try again.")
                return 400, {"success": False, "message": msg}

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/undo-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def undo_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
            """
            Handle an Request to Undo a Payment

            This Endpoint undoes a payment from an associated tax account.
            It validates the request, checks permissions, and undoes the payment to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                payment_pk (int): The ID of the payment to be approved.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            # Check if owner exists
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # Check permissions
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            payment_form_instance = (
                forms.AcceptCorporationPaymentForm
                if isinstance(owner, CorporationOwner)
                else forms.AcceptAlliancePaymentForm
            )

            # Validate the form data
            form = payment_form_instance(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            reason = form.cleaned_data["comment"]

            # Begin transaction
            try:
                with transaction.atomic():
                    payment = owner.payment_model.objects.get(
                        pk=payment_pk,
                    )
                    # Check if payment is approved or needs approval
                    if payment.is_approved or payment.is_rejected:
                        if not payment.is_rejected:
                            # Update Account Deposit
                            payment.account.deposit -= payment.amount
                            payment.account.save()
                        payment.request_status = PaymentRequestStatus.PENDING
                        payment.reviser = ""
                        payment.save()

                        # Log the Payment Action
                        payment.transaction_log(
                            user=request.user,
                            action=PaymentActions.STATUS_CHANGE,
                            comment=reason,
                            new_status=PaymentRequestStatus.PENDING,
                        ).save()

                        # Create response message
                        msg = format_lazy(
                            _(
                                "Payment ID: {pid} - Amount: {amount} - Name: {name} undone"
                            ),
                            pid=payment.pk,
                            amount=intcomma(payment.amount),
                            name=payment.name,
                        )
                        return 200, {"success": True, "message": msg}
                    msg = _("Payment is approved or rejected.")
                    return 400, {"success": True, "message": msg}
            except IntegrityError:
                msg = _("Transaction failed. Please try again.")
                return 400, {"success": False, "message": msg}

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/delete-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def delete_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
            """
            Handle an Request to Delete a Payment

            This Endpoint deletes a payment from an associated tax account.
            It validates the request, checks permissions, and deletes the payment to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                payment_pk (int): The ID of the payment to be approved.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            # Check if owner exists
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # Check permissions
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            payment_form_instance = (
                forms.DeleteCorporationPaymentForm
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAlliancePaymentForm
            )

            # Validate the form data
            form = payment_form_instance(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            reason = form.cleaned_data["comment"]

            # Begin transaction
            try:
                with transaction.atomic():
                    payment = owner.payment_model.objects.get(
                        pk=payment_pk,
                    )
                    if (
                        payment.entry is not None
                    ):  # Prevent deletion of ESI imported payments
                        msg = format_lazy(
                            _(
                                "Payment ID: {pid} - Amount: {amount} - Name: {name} deletion failed - ESI imported payments cannot be deleted"
                            ),
                            pid=payment.pk,
                            amount=intcomma(payment.amount),
                            name=payment.name,
                        )
                        return 400, {"success": False, "message": msg}

                    # Refund if approved
                    if payment.is_approved:
                        payment.account.deposit -= payment.amount
                        payment.account.save()

                    # Delete Payment
                    payment.delete()

                    msg = format_lazy(
                        _(
                            "Payment ID: {pid} - Amount: {amount} - Name: {name} deleted - {reason}"
                        ),
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                        reason=reason,
                    )

                    # Log the action in Admin History
                    owner.admin_log_model(
                        owner=owner,
                        user=request.user,
                        action=AdminActions.DELETE,
                        comment=msg,
                    ).save()

                    # Create response message
                    msg = format_lazy(
                        _("Payment ID: {pid} - Amount: {amount} - Name: {name} undone"),
                        pid=payment.pk,
                        amount=intcomma(payment.amount),
                        name=payment.name,
                    )
                    return 200, {"success": True, "message": msg}
            except IntegrityError:
                msg = _("Transaction failed. Please try again.")
                return 400, {"success": False, "message": msg}

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/reject-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def reject_payment(request: WSGIRequest, owner_id: int, payment_pk: int):
            """
            Handle an Request to Reject a Payment

            This Endpoint rejects a payment from an associated tax account.
            It validates the request, checks permissions, and rejects the payment to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                payment_pk (int): The ID of the payment to be approved.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            owner, perms = core.get_manage_owner(request, owner_id)

            # Check if owner exists
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # Check permissions
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            payment_form_instance = (
                forms.DeleteCorporationPaymentForm
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAlliancePaymentForm
            )

            # Validate the form data
            form = payment_form_instance(data=json.loads(request.body))
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            reason = form.cleaned_data["comment"]

            # Begin transaction
            try:
                with transaction.atomic():
                    payment = owner.payment_model.objects.get(
                        pk=payment_pk,
                    )
                    if payment.is_pending or payment.is_needs_approval:
                        payment.request_status = PaymentRequestStatus.REJECTED
                        payment.reviser = (
                            request.user.profile.main_character.character_name
                        )
                        payment.save()

                        msg = format_lazy(
                            _(
                                "Payment ID: {pid} - Amount: {amount} - Name: {name} rejected - {reason}"
                            ),
                            pid=payment.pk,
                            amount=intcomma(payment.amount),
                            name=payment.name,
                            reason=reason,
                        )

                        # Log Admin Action
                        payment.transaction_log(
                            user=request.user,
                            action=PaymentActions.STATUS_CHANGE,
                            comment=reason,
                            new_status=PaymentRequestStatus.REJECTED,
                        ).save()
                        return 200, {"success": True, "message": msg}
                    msg = _("Payment is not pending or does not need approval.")
                    return 400, {"success": True, "message": msg}
            except IntegrityError:
                msg = _("Transaction failed. Please try again.")
                return 400, {"success": False, "message": msg}

# Standard Library
import json

# Third Party
from humanize import intcomma
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, forms
from taxsystem.api.helpers import core
from taxsystem.models.alliance import AlliancePaymentAccount
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationPaymentAccount,
)
from taxsystem.models.helpers.textchoices import PaymentActions, PaymentRequestStatus
from taxsystem.models.logs import (
    AdminActions,
    AdminHistory,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class PaymentsApiEndpoints:
    tags = ["Payments"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.post(
            "owner/{owner_id}/account/{account_pk}/manage/add-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def add_payment(request: WSGIRequest, owner_id: int, account_pk: int):
            """
            Handle an Request to Add a custom Payment

            This Endpoint adds a custom payment for a payment account.
            It validates the request, checks permissions, and adds the payment to the according payment account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                account_pk (int): The ID of the payment account to which the payment will be added.
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

            payment_account_instance = (
                CorporationPaymentAccount
                if isinstance(owner, CorporationOwner)
                else AlliancePaymentAccount
            )

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
                    account = payment_account_instance.objects.get(
                        owner=owner, pk=account_pk
                    )
                    payment = owner.payment_model(
                        name=account.user.username,
                        entry_id=None,  # Manual Entry (use NULL to allow multiple manual payments)
                        amount=amount,
                        account=account,
                        date=timezone.now(),
                        reason=reason,
                        request_status=PaymentRequestStatus.APPROVED,
                        reviser=request.user.username,
                        owner_id=owner_id,
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

            This Endpoint approves a payment from an associated payment account.
            It validates the request, checks permissions, and approves the payment to the according payment account.

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
                        account__owner=owner,
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

            This Endpoint undoes a payment from an associated payment account.
            It validates the request, checks permissions, and undoes the payment to the according payment account.

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
                        account__owner=owner,
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

            This Endpoint deletes a payment from an associated payment account.
            It validates the request, checks permissions, and deletes the payment to the according payment account.

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
                        account__owner=owner,
                        pk=payment_pk,
                    )
                    if (
                        payment.entry_id is not None
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

                    # Log the deletion in Admin History
                    AdminHistory(
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

            This Endpoint rejects a payment from an associated payment account.
            It validates the request, checks permissions, and rejects the payment to the according payment account.

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
                        account__owner=owner,
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

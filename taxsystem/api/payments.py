# Standard Library
from typing import Literal

# Third Party
from ninja import NinjaAPI

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api import schema
from taxsystem.api.helpers import core
from taxsystem.helpers import lazy
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    ActionType,
    AdminActions,
    PaymentActions,
    PaymentRequestStatus,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


def _serialize_payment(payment, can_manage: bool) -> schema.PaymentCorporationSchema:
    character_portrait = lazy.get_character_portrait_url(payment.character_id, size=32)
    raw_status = payment.request_status
    is_custom = payment.journal is None
    can_approve = can_manage and raw_status in [
        PaymentRequestStatus.PENDING,
        PaymentRequestStatus.NEEDS_APPROVAL,
    ]
    can_reject = can_manage and raw_status in [
        PaymentRequestStatus.PENDING,
        PaymentRequestStatus.NEEDS_APPROVAL,
    ]
    can_undo = can_manage and raw_status in [
        PaymentRequestStatus.APPROVED,
        PaymentRequestStatus.REJECTED,
    ]
    can_delete = can_manage and is_custom

    response_request_status = schema.RequestStatusSchema(
        status=payment.get_request_status_display(),
        code=raw_status,
        color=PaymentRequestStatus(raw_status).color(),
    )

    character_name = ""
    if (
        hasattr(payment, "account")
        and payment.account
        and hasattr(payment.account, "name")
    ):
        character_name = payment.account.name
    elif hasattr(payment, "name") and payment.name:
        character_name = payment.name

    return schema.PaymentCorporationSchema(
        payment_id=payment.pk,
        character=schema.CharacterSchema(
            character_id=payment.character_id,
            character_name=character_name,
            character_portrait=character_portrait,
        ),
        amount=payment.amount,
        date=payment.formatted_payment_date,
        request_status=response_request_status,
        division_name=payment.division_name,
        reviser=payment.reviser,
        reason=payment.reason,
        is_custom=is_custom,
        can_delete=can_delete,
        can_approve=can_approve,
        can_reject=can_reject,
        can_undo=can_undo,
    )


# pylint: disable=too-many-statements, too-many-return-statements
def _execute_payment_action(
    user, owner, payment_pk: int, action: str, comment: str = ""
) -> tuple[int, dict]:
    """Execute a payment management action (approve, reject, undo, delete)."""
    try:
        with transaction.atomic():
            payment = owner.payment_model.objects.get(pk=payment_pk)
            reviser_name = getattr(
                getattr(getattr(user, "profile", None), "main_character", None),
                "character_name",
                None,
            ) or getattr(user, "username", "System")

            if action == "approve":
                if not (payment.is_pending or payment.is_needs_approval):
                    msg = _("Payment is not pending or does not need approval.")
                    return 400, {"success": True, "message": msg}

                payment.request_status = PaymentRequestStatus.APPROVED
                payment.reviser = reviser_name
                payment.save()

                payment.account.deposit += payment.amount
                payment.account.save()

                payment.transaction_log(
                    user=user,
                    action=PaymentActions.STATUS_CHANGE,
                    comment=comment,
                    new_status=PaymentRequestStatus.APPROVED,
                ).save()

                msg = format_lazy(
                    _("Payment ID: {pid} - Amount: {amount} - Name: {name} approved"),
                    pid=payment.pk,
                    amount=intcomma(payment.amount),
                    name=payment.name,
                )
                return 200, {"success": True, "message": msg}

            if action == "reject":
                if not (payment.is_pending or payment.is_needs_approval):
                    msg = _("Payment is not pending or does not need approval.")
                    return 400, {"success": True, "message": msg}

                payment.request_status = PaymentRequestStatus.REJECTED
                payment.reviser = reviser_name
                payment.save()

                payment.transaction_log(
                    user=user,
                    action=PaymentActions.STATUS_CHANGE,
                    comment=comment,
                    new_status=PaymentRequestStatus.REJECTED,
                ).save()

                msg = format_lazy(
                    _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} rejected - {reason}"
                    ),
                    pid=payment.pk,
                    amount=intcomma(payment.amount),
                    name=payment.name,
                    reason=comment,
                )
                return 200, {"success": True, "message": msg}

            if action == "undo":
                if not (payment.is_approved or payment.is_rejected):
                    msg = _("Payment is approved or rejected.")
                    return 400, {"success": True, "message": msg}

                if not payment.is_rejected:
                    payment.account.deposit -= payment.amount
                    payment.account.save()

                payment.request_status = PaymentRequestStatus.PENDING
                payment.reviser = ""
                payment.save()

                payment.transaction_log(
                    user=user,
                    action=PaymentActions.STATUS_CHANGE,
                    comment=comment,
                    new_status=PaymentRequestStatus.PENDING,
                ).save()

                msg = format_lazy(
                    _("Payment ID: {pid} - Amount: {amount} - Name: {name} undone"),
                    pid=payment.pk,
                    amount=intcomma(payment.amount),
                    name=payment.name,
                )
                return 200, {"success": True, "message": msg}

            if action == "delete":
                if payment.journal is not None:
                    msg = _("ESI imported payments cannot be deleted")
                    return 400, {"success": False, "message": msg}

                pid = payment.pk
                amount = intcomma(payment.amount)
                name = payment.name
                reason = comment or "Deleted via TaxSystem"

                if payment.is_approved:
                    payment.account.deposit -= payment.amount
                    payment.account.save()

                payment.delete()

                msg = format_lazy(
                    _(
                        "Payment ID: {pid} - Amount: {amount} - Name: {name} deleted - {reason}"
                    ),
                    pid=pid,
                    amount=amount,
                    name=name,
                    reason=reason,
                )

                owner.admin_log_model(
                    owner=owner,
                    user=user,
                    target=ActionType.PAYMENT,
                    action=AdminActions.DELETE,
                    comment=msg,
                ).save()
                return 200, {"success": True, "message": msg}

            return 400, {"success": False, "message": f"Unknown action '{action}'."}

    except owner.payment_model.DoesNotExist:
        return 404, {"error": _("Payment not Found.")}
    except IntegrityError:
        msg = _("Transaction failed. Please try again.")
        return 400, {"success": False, "message": msg}


class PaymentsApiEndpoints:
    tags = ["Payments"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/payments/",
            response={
                200: list[schema.PaymentCorporationSchema],
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get payments for an owner with optional scope/character filtering",
        )
        def get_payments(
            request: WSGIRequest,
            owner_id: int,
            scope: Literal["all", "mine"] = "all",
            character_id: int | None = None,
        ):
            owner, perms = core.get_owner(request, owner_id)
            if owner is None:
                return 404, {"error": "Owner not Found."}
            if perms is False:
                return 403, {"error": "Permission Denied."}

            can_manage = core.get_manage_owner(request, owner_id)[1]

            if character_id is not None:
                char_perm = can_manage or core.get_character_permissions(
                    request, character_id
                )
                if not char_perm:
                    return 403, {"error": "Permission Denied."}
                payments = (
                    owner.payment_model.objects.filter(
                        Q(
                            account__user__profile__main_character__character_id=character_id
                        )
                        | Q(
                            account__user__character_ownerships__character__character_id=character_id
                        ),
                        owner=owner,
                    )
                    .distinct()
                    .order_by("-date")
                )
            elif scope == "mine":
                payments = owner.payment_model.objects.filter(
                    owner=owner,
                    account__user=request.user,
                ).order_by("-date")
            else:
                payments = owner.payment_model.objects.get_visible(
                    user=request.user
                ).order_by("-date")

            payments = payments.select_related(
                "account",
                "account__user",
                "account__user__profile",
                "account__user__profile__main_character",
            )[:10000]

            return [
                _serialize_payment(p, can_manage if scope != "mine" else False)
                for p in payments
            ]

        @api.get(
            "owner/{owner_id}/view/payments/",
            response={
                200: list[schema.PaymentCorporationSchema],
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
            tags=self.tags,
        )
        def get_payments_legacy(request: WSGIRequest, owner_id: int):
            """Legacy route delegating to get_payments with scope='all'."""
            return get_payments(request, owner_id, scope="all")

        @api.get(
            "owner/{owner_id}/view/my-payments/",
            response={
                200: list[schema.PaymentCorporationSchema],
                404: schema.ErrorSchema,
            },
            tags=self.tags,
        )
        def get_my_payments(request: WSGIRequest, owner_id: int):
            """Legacy route delegating to get_payments with scope='mine'."""
            return get_payments(request, owner_id, scope="mine")

        @api.get(
            "owner/{owner_id}/payment/{payment_pk}/view/details/",
            response={200: schema.PaymentsDetailsResponse, 403: dict, 404: dict},
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

            response_payment_histories: list[schema.PaymentHistorySchema] = []
            payments_history = owner.payment_history_model.objects.filter(
                payment=payment,
            ).order_by("-date")

            # Create a list for the payment histories
            for log in payments_history:
                response_log = schema.PaymentHistorySchema(
                    log_id=log.pk,
                    reviser=log.user.username if log.user else _("System"),
                    date=log.date.strftime("%Y-%m-%d %H:%M:%S"),
                    action=log.get_action_display(),
                    comment=log.comment,
                    status=log.get_new_status_display(),
                )
                response_payment_histories.append(response_log)

            # Create the tax account
            response_account = schema.TaxAccountSchema(
                account_id=payment.account.pk,
                account_name=payment.account.name,
                account_status=AccountStatus(payment.account.status).html(),
                character=schema.CharacterSchema(
                    character_id=payment.character_id,
                    character_name=payment.account.name,
                    character_portrait=lazy.get_character_portrait_url(
                        payment.character_id, size=32
                    ),
                    corporation_id=payment.account.owner.pk,
                    corporation_name=payment.account.owner.name,
                ),
                payment_pool=payment.account.deposit,
            )

            raw_status = payment.request_status
            is_custom = payment.journal is None
            can_manage = core.get_manage_owner(request, owner_id)[1]

            response_request_status = schema.RequestStatusSchema(
                status=payment.get_request_status_display(),
                code=raw_status,
                html=PaymentRequestStatus(raw_status).alert(),
            )

            # Create the payment
            response_payment = schema.PaymentSchema(
                payment_id=payment.pk,
                amount=payment.amount,
                date=payment.formatted_payment_date,
                request_status=response_request_status,
                division_name=payment.division_name,
                reason=payment.reason,
                reviser=payment.reviser,
                is_custom=is_custom,
                can_delete=can_manage and is_custom,
                can_approve=can_manage
                and raw_status
                in [
                    PaymentRequestStatus.PENDING,
                    PaymentRequestStatus.NEEDS_APPROVAL,
                ],
                can_reject=can_manage
                and raw_status
                in [
                    PaymentRequestStatus.PENDING,
                    PaymentRequestStatus.NEEDS_APPROVAL,
                ],
                can_undo=can_manage
                and raw_status
                in [
                    PaymentRequestStatus.APPROVED,
                    PaymentRequestStatus.REJECTED,
                ],
            )

            response_owner = schema.OwnerSchema(
                owner_id=owner.eve_id,
                owner_name=owner.name,
            )

            payment_details_response = schema.PaymentsDetailsResponse(
                owner=response_owner,
                account=response_account,
                payment=response_payment,
                payment_histories=response_payment_histories,
            )

            return payment_details_response

        @api.get(
            "owner/{owner_id}/character/{character_id}/view/payments/",
            response={
                200: list[schema.PaymentCorporationSchema],
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get member payments (legacy wrapper)",
        )
        def get_member_payments(request: WSGIRequest, owner_id: int, character_id: int):
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Corporation Not Found")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}
            return get_payments(request, owner_id, character_id=character_id)

        @api.post(
            "owner/{owner_id}/account/{account_pk}/manage/add-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def add_payment(
            request: WSGIRequest,
            owner_id: int,
            account_pk: int,
            payload: schema.AddPaymentRequest,
        ):
            """
            Handle an Request to Add a custom Payment

            This Endpoint adds a custom payment for a tax account.
            It validates the request, checks permissions, and adds the payment to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                account_pk (int): The ID of the tax account to which the payment will be added.
                payload (schema.AddPaymentRequest): Custom payment details (amount and comment).
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

            # Validate the payload (a reason is mandatory)
            amount = payload.amount
            comment = payload.comment.strip()
            if not comment:
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

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
                        reason="",
                        request_status=PaymentRequestStatus.APPROVED,
                        reviser=request.user.username,
                    )

                    # Create log message
                    msg = format_lazy(
                        _("Custom Payment Added: {comment}"),
                        comment=comment,
                    )

                    payment.save()
                    account.deposit += amount
                    account.save()

                    # Log the Payment Action
                    payment.transaction_log(
                        user=request.user,
                        action=PaymentActions.CUSTOM_PAYMENT,
                        new_status=PaymentRequestStatus.APPROVED,
                        comment=comment,
                    ).save()

                    # Log the addition in Admin History
                    owner.admin_log_model(
                        user=request.user,
                        owner=owner,
                        target=ActionType.PAYMENT,
                        action=AdminActions.ADD,
                        comment=msg,
                    ).save()

                return 200, {"success": True, "message": msg}
            except IntegrityError:
                msg = _("Transaction failed. Please try again.")
                return 400, {"success": False, "message": msg}

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/action/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
            summary="Manage payment actions (approve, reject, undo, delete)",
        )
        def manage_payment_action(
            request: WSGIRequest,
            owner_id: int,
            payment_pk: int,
            payload: schema.PaymentActionRequest,
        ):
            """Manage payment actions via unified action endpoint."""
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Owner not Found.")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}
            return _execute_payment_action(
                user=request.user,
                owner=owner,
                payment_pk=payment_pk,
                action=payload.action,
                comment=payload.comment or "",
            )

        @api.post(
            "owner/{owner_id}/manage/payments/bulk-action/",
            response={
                200: schema.BulkPaymentActionResponse,
                400: schema.BulkPaymentActionResponse,
                403: schema.ErrorSchema,
                404: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Execute bulk payment actions (approve, reject, undo, delete)",
        )
        def manage_bulk_payment_action(
            request: WSGIRequest,
            owner_id: int,
            payload: schema.BulkPaymentActionRequest,
        ):
            """Manage multiple payments in bulk."""
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Owner not Found.")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            payment_ids = payload.payment_ids
            if not payment_ids:
                return 400, {
                    "success": False,
                    "processed_count": 0,
                    "total_count": 0,
                    "message": str(_("No payment IDs provided.")),
                }

            processed = 0
            for payment_pk in payment_ids:
                status_code, _res = _execute_payment_action(
                    user=request.user,
                    owner=owner,
                    payment_pk=payment_pk,
                    action=payload.action,
                    comment=payload.comment or "",
                )
                if status_code == 200:
                    processed += 1

            action_labels = {
                "approve": _("approved"),
                "reject": _("rejected"),
                "undo": _("undone"),
                "delete": _("deleted"),
            }
            action_label = action_labels.get(payload.action, payload.action)

            msg = format_lazy(
                _("{processed} of {total} payments successfully {action}."),
                processed=processed,
                total=len(payment_ids),
                action=action_label,
            )

            return 200, {
                "success": processed > 0,
                "processed_count": processed,
                "total_count": len(payment_ids),
                "message": str(msg),
            }

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/approve-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
            summary="Approve payment (legacy wrapper)",
        )
        def approve_payment(
            request: WSGIRequest,
            owner_id: int,
            payment_pk: int,
            payload: schema.ActionCommentRequest = schema.ActionCommentRequest(),
        ):
            """Legacy wrapper to approve a payment."""
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Owner not Found.")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}
            reason = payload.comment if payload else ""
            return _execute_payment_action(
                user=request.user,
                owner=owner,
                payment_pk=payment_pk,
                action="approve",
                comment=reason,
            )

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/undo-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
            summary="Undo payment (legacy wrapper)",
        )
        def undo_payment(
            request: WSGIRequest,
            owner_id: int,
            payment_pk: int,
            payload: schema.ActionCommentRequest = schema.ActionCommentRequest(),
        ):
            """Legacy wrapper to undo a payment."""
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Owner not Found.")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}
            reason = payload.comment if payload else ""
            return _execute_payment_action(
                user=request.user,
                owner=owner,
                payment_pk=payment_pk,
                action="undo",
                comment=reason,
            )

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/delete-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
            summary="Delete payment (legacy wrapper)",
        )
        def delete_payment(
            request: WSGIRequest,
            owner_id: int,
            payment_pk: int,
            payload: schema.DeletePaymentRequest = schema.DeletePaymentRequest(),
        ):
            """Legacy wrapper to delete a payment."""
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Owner not Found.")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}
            reason = (
                payload.comment
                if payload and payload.comment
                else "Deleted via TaxSystem"
            )
            return _execute_payment_action(
                user=request.user,
                owner=owner,
                payment_pk=payment_pk,
                action="delete",
                comment=reason,
            )

        @api.post(
            "owner/{owner_id}/payment/{payment_pk}/manage/reject-payment/",
            response={200: dict, 400: dict, 403: dict, 404: dict},
            tags=self.tags,
            summary="Reject payment (legacy wrapper)",
        )
        def reject_payment(
            request: WSGIRequest,
            owner_id: int,
            payment_pk: int,
            payload: schema.ActionCommentRequest = schema.ActionCommentRequest(),
        ):
            """Legacy wrapper to reject a payment."""
            owner, perms = core.get_manage_owner(request, owner_id)
            if owner is None:
                return 404, {"error": _("Owner not Found.")}
            if perms is False:
                return 403, {"error": _("Permission Denied.")}
            reason = payload.comment if payload else ""
            return _execute_payment_action(
                user=request.user,
                owner=owner,
                payment_pk=payment_pk,
                action="reject",
                comment=reason,
            )

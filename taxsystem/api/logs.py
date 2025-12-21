# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.schema import (
    AdminHistorySchema,
    PaymentHistorySchema,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class AdminLogResponse(Schema):
    owner: list[AdminHistorySchema]


class PaymentsLogResponse(Schema):
    owner: list[AdminHistorySchema]


class LogsApiEndpoints:
    tags = ["Logs"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/admin/{owner_id}/view/logs/",
            response={200: PaymentsLogResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_payments_history(request, owner_id: int):
            """
            This Endpoint retrieves the payments logs associated with a specific owner.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose payments logs are to be retrieved.
            Returns:
                PaymentsLogResponse: A response object containing the list of payments logs.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            logs = (
                owner.admin_log_model.objects.filter(owner=owner)
                .select_related("user")
                .order_by("-date")
            )

            # Use generic helper function
            response_admin_logs_list: list[PaymentHistorySchema] = []
            for log in logs:
                response_log = PaymentHistorySchema(
                    log_id=log.pk,
                    user_name=log.user.username,
                    date=timezone.localtime(log.date).strftime("%Y-%m-%d %H:%M"),
                    action=log.action,
                    comment=log.comment,
                )
                response_admin_logs_list.append(response_log)

            return PaymentsLogResponse(owner=response_admin_logs_list)

        @api.get(
            "owner/admin/{owner_id}/view/logs/",
            response={200: AdminLogResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_owner_admin_logs(request, owner_id: int):
            """
            This Endpoint retrieves the admin logs associated with a specific owner.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose admin logs are to be retrieved.
            Returns:
                AdminLogResponse: A response object containing the list of admin logs.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            logs = (
                owner.admin_log_model.objects.filter(owner=owner)
                .select_related("user")
                .order_by("-date")
            )

            # Use generic helper function
            response_admin_logs_list: list[AdminHistorySchema] = []
            for log in logs:
                response_log = AdminHistorySchema(
                    log_id=log.pk,
                    user_name=log.user.username,
                    date=timezone.localtime(log.date).strftime("%Y-%m-%d %H:%M"),
                    action=log.action,
                    comment=log.comment,
                )
                response_admin_logs_list.append(response_log)

            return AdminLogResponse(owner=response_admin_logs_list)

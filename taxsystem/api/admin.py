# Standard Library
from decimal import Decimal
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__, tasks
from taxsystem.api import schema
from taxsystem.api.helpers import core
from taxsystem.api.helpers.statistics import (
    StatisticsResponse,
    create_dashboard_common_data,
)
from taxsystem.api.schema import (
    AccountSchema,
    DashboardDivisionsSchema,
    ErrorSchema,
    OwnerSchema,
    PaymentSystemSchema,
    UpdateStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationWalletJournalEntry,
)
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    ActionType,
    AdminActions,
    PaymentRequestStatus,
)
from taxsystem.models.wallet import CorporationWalletDivision
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class DashboardResponse(Schema):
    owner: OwnerSchema
    update_status: UpdateStatusSchema
    tax_amount: int
    tax_period: int
    divisions: DashboardDivisionsSchema
    statistics: StatisticsResponse
    activity: float


class AdminApiEndpoints:
    tags = ["Admin"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{owner_id}/view/dashboard/",
            response={200: DashboardResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_dashboard(request: WSGIRequest, owner_id: int):
            """
            This Endpoint retrieves the dashboard information for a specific corporation.
            Args:
                request (WSGIRequest): The HTTP request object.
                corporation_id (int): The ID of the corporation whose dashboard information is to be retrieved.
            Returns:
                DashboardResponse: A response object containing the dashboard information.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            divisions = (
                CorporationWalletDivision.objects.filter(corporation=owner)
                if isinstance(owner, CorporationOwner)
                else []
            )
            wallet_activity = (
                (
                    CorporationWalletJournalEntry.objects.filter(
                        division__corporation=owner,
                        date__gte=timezone.now() - timezone.timedelta(days=30),
                    )
                    .aggregate(total=Sum("amount"))
                    .get("total", 0)
                    or 0
                )
                if isinstance(owner, CorporationOwner)
                else 0
            )

            # Create common dashboard data
            common_data = create_dashboard_common_data(owner, divisions)

            dashboard_response = DashboardResponse(
                owner=OwnerSchema(
                    owner_id=owner.eve_id,
                    owner_name=owner.name,
                    owner_type=(
                        "corporation"
                        if isinstance(owner, CorporationOwner)
                        else "alliance"
                    ),
                ),
                activity=wallet_activity,
                **common_data,
            )
            return dashboard_response

        @api.get(
            "owner/{owner_id}/manage/tax-accounts/",
            response={
                200: list[PaymentSystemSchema],
                403: ErrorSchema,
                404: ErrorSchema,
            },
            tags=self.tags,
        )
        def get_tax_accounts(request, owner_id: int):
            """
            This Endpoint retrieves the tax accounts associated with a specific owner.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose tax accounts are to be retrieved.
            Returns:
                PaymentSystemResponse: A response object containing the list of tax accounts.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            # Get Tax Accounts for Owner except those missing main character
            tax_accounts = (
                owner.account_model.objects.filter(
                    owner=owner,
                    user__profile__main_character__isnull=False,
                )
                .exclude(status=AccountStatus.MISSING)
                .select_related(
                    "user", "user__profile", "user__profile__main_character"
                )
                .prefetch_related("user__character_ownerships__character")
            )

            open_invoices_map = dict(
                owner.payment_model.objects.filter(
                    owner=owner,
                    request_status__in=[
                        PaymentRequestStatus.PENDING,
                        PaymentRequestStatus.NEEDS_APPROVAL,
                    ],
                )
                .values("account_id")
                .annotate(count=Count("id"))
                .values_list("account_id", "count")
            )

            tax_accounts_list: list[PaymentSystemSchema] = []
            for account in tax_accounts:
                # Build tax account data
                tax_account_data = PaymentSystemSchema(
                    account_id=account.pk,
                    account=AccountSchema(
                        character_id=account.user.profile.main_character.character_id,
                        character_name=account.user.profile.main_character.character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            account.user.profile.main_character.character_id,
                            size=32,
                        ),
                        alt_ids=account.get_alt_ids(),
                    ),
                    status=account.get_payment_status(),
                    deposit=account.deposit,
                    has_paid=account.has_paid,
                    last_paid=account.last_paid,
                    next_due=account.next_due,
                    is_active=account.is_active,
                    open_invoices=open_invoices_map.get(account.pk, 0),
                )
                tax_accounts_list.append(tax_account_data)
            return tax_accounts_list

        @api.post(
            "owner/{owner_id}/account/{account_pk}/manage/switch-account/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def switch_tax_account(request: WSGIRequest, owner_id: int, account_pk: int):
            """
            Handle an Request to Switch a Tax Account

            This Endpoint switches a tax account from an associated owner.
            It validates the request, checks permissions, and switches the his state to the according tax account.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                account_pk (int): The ID of the tax account to be switched.
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

            # Get the Tax Account related to the Owner (Corporation / Alliance)
            account = owner.account_model.objects.filter(
                owner=owner, pk=account_pk
            ).first()
            if not account:
                msg = _("Account not found.")
                return 404, {"success": False, "message": msg}

            # Toggle the filter set enabled state
            if account.status == AccountStatus.ACTIVE:
                account.status = AccountStatus.INACTIVE
            else:
                account.status = AccountStatus.ACTIVE
            account.save()

            # Create log message
            msg = format_lazy(
                _("{account} switched to {status}"),
                account=account.name,
                status=account.status,
            )

            # Log the Switch in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                target=ActionType.TAX_ACCOUNT,
                action=AdminActions.CHANGE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

        @api.post(
            "owner/{owner_id}/manage/settings/",
            response={200: dict, 403: dict, 404: dict, 400: dict},
            tags=self.tags,
        )
        def update_owner_settings(
            request: WSGIRequest,
            owner_id: int,
            payload: schema.UpdateOwnerSettingsRequest,
        ):
            """
            Handle a request to update owner settings (tax amount and/or tax period).
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            # pylint: disable=duplicate-code
            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            # pylint: disable=duplicate-code
            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            messages_list = []
            if payload.tax_amount is not None:
                value = Decimal(payload.tax_amount)
                if value < 0:
                    return 400, {
                        "success": False,
                        "message": _("Please enter a valid number"),
                    }
                owner.tax_amount = value
                messages_list.append(
                    format_lazy(
                        _("Tax Amount from {owner} changed to {value}"),
                        owner=owner,
                        value=value,
                    )
                )

            if payload.tax_period is not None:
                value = payload.tax_period
                if value < 0:
                    return 400, {
                        "success": False,
                        "message": _("Please enter a valid number"),
                    }
                owner.tax_period = value
                messages_list.append(
                    format_lazy(
                        _("Tax Period from {owner} changed to {value}"),
                        owner=owner,
                        value=value,
                    )
                )

            if not messages_list:
                return 400, {
                    "success": False,
                    "message": _("No settings provided to update."),
                }

            owner.save()
            msg = (
                str(messages_list[0])
                if len(messages_list) == 1
                else "; ".join(str(m) for m in messages_list)
            )

            owner.admin_log_model(
                user=request.user,
                owner=owner,
                target=ActionType.SETTINGS,
                action=AdminActions.CHANGE,
                comment=msg,
            ).save()

            return 200, {"success": True, "message": msg}

        @api.post(
            "owner/{owner_id}/manage/update-tax/",
            response={200: dict, 403: dict, 404: dict, 400: dict},
            tags=self.tags,
        )
        def update_tax_amount(
            request: WSGIRequest,
            owner_id: int,
            payload: schema.UpdateTaxAmountRequest,
        ):
            """Legacy wrapper delegating to update_owner_settings."""
            return update_owner_settings(
                request,
                owner_id,
                schema.UpdateOwnerSettingsRequest(tax_amount=payload.tax_amount),
            )

        @api.post(
            "owner/{owner_id}/manage/update-period/",
            response={200: dict, 403: dict, 404: dict, 400: dict},
            tags=self.tags,
        )
        def update_tax_period(
            request: WSGIRequest,
            owner_id: int,
            payload: schema.UpdateTaxPeriodRequest,
        ):
            """Legacy wrapper delegating to update_owner_settings."""
            return update_owner_settings(
                request,
                owner_id,
                schema.UpdateOwnerSettingsRequest(tax_period=payload.tax_period),
            )

        @api.post(
            "admin/tasks/run/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.BAD_REQUEST: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Queue update tasks for taxsystem",
        )
        # pylint: disable=too-many-return-statements
        def run_update_tasks(request: WSGIRequest, payload: schema.AdminUpdateRequest):
            if not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            force_refresh = payload.force_refresh
            target = payload.target
            eve_id = payload.eve_id

            if target == "all":
                tasks.update_all_taxsytem.apply_async(
                    kwargs={"force_refresh": force_refresh}, priority=7
                )
                return HTTPStatus.OK, {"message": _("Queued Update All Taxsystem")}

            if target == "corporation":
                if eve_id:
                    try:
                        corp = CorporationOwner.objects.get(
                            eve_corporation__corporation_id=eve_id
                        )
                        tasks.update_corporation.apply_async(
                            args=[corp.eve_id],
                            kwargs={"force_refresh": force_refresh},
                            priority=7,
                        )
                        return HTTPStatus.OK, {
                            "message": _("Queued Update for Corporation: %s")
                            % corp.name
                        }
                    except CorporationOwner.DoesNotExist:
                        return HTTPStatus.BAD_REQUEST, {
                            "error": _("Corporation with ID %s not found") % eve_id
                        }
                else:
                    corporations = CorporationOwner.objects.filter(active=True)
                    for corporation in corporations:
                        tasks.update_corporation.apply_async(
                            args=[corporation.eve_id],
                            kwargs={"force_refresh": force_refresh},
                            priority=7,
                        )
                    return HTTPStatus.OK, {
                        "message": _("Queued Update All Taxsystem Corporations")
                    }

            if target == "alliance":
                if eve_id:
                    try:
                        ally = AllianceOwner.objects.get(
                            eve_alliance__alliance_id=eve_id
                        )
                        tasks.update_alliance.apply_async(
                            args=[ally.eve_alliance.alliance_id],
                            kwargs={"force_refresh": force_refresh},
                            priority=7,
                        )
                        return HTTPStatus.OK, {
                            "message": _("Queued Update for Alliance: %s") % ally.name
                        }
                    except AllianceOwner.DoesNotExist:
                        return HTTPStatus.BAD_REQUEST, {
                            "error": _("Alliance with ID %s not found") % eve_id
                        }
                else:
                    alliances = AllianceOwner.objects.filter(active=True)
                    for alliance in alliances:
                        tasks.update_alliance.apply_async(
                            args=[alliance.eve_alliance.alliance_id],
                            kwargs={"force_refresh": force_refresh},
                            priority=7,
                        )
                    return HTTPStatus.OK, {
                        "message": _("Queued Update All Taxsystem Alliances")
                    }

            return HTTPStatus.BAD_REQUEST, {"error": _("Invalid target specified.")}

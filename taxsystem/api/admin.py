# Standard Library
import json

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api.helpers import core
from taxsystem.api.helpers.icons import (
    get_taxsystem_manage_action_icons,
)
from taxsystem.api.helpers.statistics import (
    StatisticsResponse,
    create_dashboard_common_data,
)
from taxsystem.api.schema import (
    AccountSchema,
    DashboardDivisionsSchema,
    DataTableSchema,
    OwnerSchema,
    PaymentSystemSchema,
    UpdateStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationWalletJournalEntry,
)
from taxsystem.models.helpers.textchoices import AccountStatus, AdminActions
from taxsystem.models.wallet import CorporationWalletDivision

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
            response={200: list, 403: dict, 404: dict},
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
                return 404, {"error": _("Owner Not Found")}

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

            tax_accounts_list: list[PaymentSystemSchema] = []
            for account in tax_accounts:
                # Build tax account data
                tax_account_data = PaymentSystemSchema(
                    payment_id=account.pk,
                    account=AccountSchema(
                        character_id=account.user.profile.main_character.character_id,
                        character_name=account.user.profile.main_character.character_name,
                        character_portrait=lazy.get_character_portrait_url(
                            account.user.profile.main_character.character_id,
                            size=32,
                            as_html=True,
                        ),
                        alt_ids=account.get_alt_ids(),
                    ),
                    status=account.get_payment_status(),
                    deposit=account.deposit,
                    has_paid=DataTableSchema(
                        raw=account.has_paid,
                        display=account.has_paid_icon(badge=True),
                        sort=str(int(account.has_paid)),
                    ),
                    last_paid=account.last_paid,
                    next_due=account.next_due,
                    is_active=account.is_active,
                    actions=get_taxsystem_manage_action_icons(
                        request=request, account=account
                    ),
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
                account=account,
                status=account.status,
            )

            # Log the Switch in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                action=AdminActions.DELETE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

        @api.post(
            "owner/{owner_id}/manage/update-tax/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def update_tax_amount(request: WSGIRequest, owner_id: int):
            """
            Handle an Request to Update Tax Amount

            This Endpoint updates the tax amount for an associated owner.
            It validates the request, checks permissions, and updates the tax amount accordingly.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
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

            value = float(json.loads(request.body).get("tax_amount", 0))

            if value < 0:
                msg = _("Please enter a valid number")
                return 400, {"success": False, "message": msg}

            logger.debug(
                f"Updating tax amount for owner ID {owner_id} to {value}. Permissions: {perms}"
            )

            owner.tax_amount = value
            owner.save()

            # Create log message
            msg = format_lazy(
                _("Tax Period from {owner} changed to {value}"),
                owner=owner,
                value=value,
            )

            # Log Action in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                action=AdminActions.CHANGE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

        @api.post(
            "owner/{owner_id}/manage/update-period/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def update_tax_period(request: WSGIRequest, owner_id: int):
            """
            Handle an Request to Update Tax Period

            This Endpoint updates the tax period for an associated owner.
            It validates the request, checks permissions, and updates the tax period accordingly.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
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

            value = int(json.loads(request.body).get("tax_period", 0))

            if value < 0:
                msg = _("Please enter a valid number")
                return 400, {"success": False, "message": msg}

            logger.debug(
                f"Updating tax period for owner ID {owner_id} to {value}. Permissions: {perms}"
            )

            owner.tax_period = value
            owner.save()

            # Create log message
            msg = format_lazy(
                _("Tax Period from {owner} changed to {value}"),
                owner=owner,
                value=value,
            )

            # Log Action in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                action=AdminActions.CHANGE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

        @api.post(
            "owner/{owner_id}/manage/bulk-actions/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def perform_bulk_actions_tax_accounts(request: WSGIRequest, owner_id: int):
            """
            Handle an Request to Bulk Actions

            This Endpoint performs bulk actions for an associated owner.
            It validates the request, checks permissions, and performs the bulk actions accordingly.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
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

            pks_ids = json.loads(request.body).get("pks", [])
            action = json.loads(request.body).get("action", "")

            if len(pks_ids) == 0:
                msg = _("Please select at least one account")
                return 400, {"success": False, "message": msg}

            if action == "activate":
                status = AccountStatus.ACTIVE
                items = owner.account_model.objects.filter(
                    owner=owner,
                    pk__in=pks_ids,
                ).update(status=status)
            elif action == "deactivate":
                status = AccountStatus.DEACTIVATED
                items = owner.account_model.objects.filter(
                    owner=owner,
                    pk__in=pks_ids,
                ).update(status=status)
            else:
                msg = _("Please select a valid action")
                return 400, {"success": False, "message": msg}

            # Create log message
            msg = format_lazy(
                _("Bulk '{status}' performed for {items} accounts({pks}) for {owner}"),
                items=items,
                status=status,
                owner=owner,
                pks=pks_ids,
            )

            # Log Action in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                action=AdminActions.CHANGE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem import tasks
from taxsystem.api import admin, schema
from taxsystem.api.helpers import core
from taxsystem.api.helpers.statistics import create_dashboard_common_data
from taxsystem.helpers import lazy
from taxsystem.models.alliance import AllianceOwner, AllianceUpdateStatus
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationUpdateStatus,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)
from taxsystem.models.helpers.textchoices import PaymentRequestStatus

# Corporation IDs below this value belong to NPC corporations
MIN_PLAYER_CORPORATION_ID = 10_000_000


class AdministrationApiEndpoints:
    tags = ["Administration"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "administration/owners/",
            response={
                HTTPStatus.OK: list[schema.AdministrationTaxOwnerSchema],
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="List all corporation and alliance owners for administration management",
        )
        def list_administration_owners(request: WSGIRequest):
            if not core.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, {
                    "error": _("Administration permission required.")
                }

            owners_list: list[schema.AdministrationTaxOwnerSchema] = []

            # 1. Corporation Owners
            # NPC corporations are never listed in the Administration
            corporations = CorporationOwner.objects.select_related(
                "eve_corporation"
            ).filter(eve_corporation__corporation_id__gte=MIN_PLAYER_CORPORATION_ID)
            for corp in corporations:
                last_sync = (
                    CorporationUpdateStatus.objects.filter(owner=corp)
                    .order_by("-last_run_finished_at")
                    .values_list("last_run_finished_at", flat=True)
                    .first()
                )
                first_err = (
                    CorporationUpdateStatus.objects.filter(owner=corp, is_success=False)
                    .exclude(error_message="")
                    .values_list("error_message", flat=True)
                    .first()
                )
                open_inv = corp.payment_model.objects.filter(
                    owner=corp,
                    request_status__in=[
                        PaymentRequestStatus.PENDING,
                        PaymentRequestStatus.NEEDS_APPROVAL,
                    ],
                ).count()
                ticker = (
                    corp.eve_corporation.ticker
                    if hasattr(corp, "eve_corporation") and corp.eve_corporation
                    else None
                )

                owners_list.append(
                    schema.AdministrationTaxOwnerSchema(
                        id=corp.id,
                        owner_id=corp.eve_id,
                        owner_type="corporation",
                        name=corp.name,
                        icon=lazy.get_corporation_logo_url(corp.eve_id, size=64),
                        ticker=ticker,
                        status=str(corp.get_status),
                        is_active=bool(corp.active),
                        tax_amount=float(corp.tax_amount),
                        tax_period=int(corp.tax_period),
                        open_invoices=open_inv,
                        last_sync=last_sync,
                        error_message=first_err or None,
                    )
                )

            # 2. Alliance Owners
            alliances = AllianceOwner.objects.select_related("eve_alliance").all()
            for ally in alliances:
                last_sync = (
                    AllianceUpdateStatus.objects.filter(owner=ally)
                    .order_by("-last_run_finished_at")
                    .values_list("last_run_finished_at", flat=True)
                    .first()
                )
                first_err = (
                    AllianceUpdateStatus.objects.filter(owner=ally, is_success=False)
                    .exclude(error_message="")
                    .values_list("error_message", flat=True)
                    .first()
                )
                open_inv = ally.payment_model.objects.filter(
                    owner=ally,
                    request_status__in=[
                        PaymentRequestStatus.PENDING,
                        PaymentRequestStatus.NEEDS_APPROVAL,
                    ],
                ).count()
                ticker = (
                    ally.eve_alliance.ticker
                    if hasattr(ally, "eve_alliance") and ally.eve_alliance
                    else None
                )

                owners_list.append(
                    schema.AdministrationTaxOwnerSchema(
                        id=ally.id,
                        owner_id=ally.eve_id,
                        owner_type="alliance",
                        name=ally.name,
                        icon=lazy.get_alliance_logo_url(ally.eve_id, size=64),
                        ticker=ticker,
                        status=str(ally.get_status),
                        is_active=bool(ally.active),
                        tax_amount=float(ally.tax_amount),
                        tax_period=int(ally.tax_period),
                        open_invoices=open_inv,
                        last_sync=last_sync,
                        error_message=first_err or None,
                    )
                )

            owners_list.sort(key=lambda x: x.name.lower())
            return HTTPStatus.OK, owners_list

        @api.post(
            "administration/owners/{str:owner_type}/{int:owner_id}/update/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.BAD_REQUEST: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Trigger an update for a corporation or alliance owner",
        )
        # pylint: disable=too-many-return-statements
        def update_administration_owner(
            request: WSGIRequest,
            owner_type: str,
            owner_id: int,
            payload: schema.AdministrationTaxOwnerUpdateRequest,
        ):
            if not core.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, {
                    "error": _("Administration permission required.")
                }

            force_refresh = payload.force_refresh
            if force_refresh and not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {
                    "error": _("Superuser permission required.")
                }

            if owner_type == "corporation":
                try:
                    corp = CorporationOwner.objects.get(
                        eve_corporation__corporation_id=owner_id,
                        eve_corporation__corporation_id__gte=MIN_PLAYER_CORPORATION_ID,
                    )
                except CorporationOwner.DoesNotExist:
                    return HTTPStatus.NOT_FOUND, {
                        "error": _("Corporation with ID %(id)s not found")
                        % {"id": owner_id}
                    }

                tasks.update_corporation.apply_async(
                    args=[corp.eve_id],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
                return HTTPStatus.OK, {
                    "message": _("Queued update for %(name)s") % {"name": corp.name}
                }

            if owner_type == "alliance":
                try:
                    ally = AllianceOwner.objects.get(eve_alliance__alliance_id=owner_id)
                except AllianceOwner.DoesNotExist:
                    return HTTPStatus.NOT_FOUND, {
                        "error": _("Alliance with ID %(id)s not found")
                        % {"id": owner_id}
                    }

                tasks.update_alliance.apply_async(
                    args=[ally.eve_id],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
                return HTTPStatus.OK, {
                    "message": _("Queued update for %(name)s") % {"name": ally.name}
                }

            return HTTPStatus.BAD_REQUEST, {"error": _("Invalid owner type specified.")}

        @api.delete(
            "administration/owners/{str:owner_type}/{int:owner_id}/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.BAD_REQUEST: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Delete a corporation or alliance owner",
        )
        def delete_administration_owner(
            request: WSGIRequest,
            owner_type: str,
            owner_id: int,
        ):
            if not core.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, {
                    "error": _("Administration permission required.")
                }

            if owner_type == "corporation":
                try:
                    corp = CorporationOwner.objects.get(
                        eve_corporation__corporation_id=owner_id,
                        eve_corporation__corporation_id__gte=MIN_PLAYER_CORPORATION_ID,
                    )
                except CorporationOwner.DoesNotExist:
                    return HTTPStatus.NOT_FOUND, {
                        "error": _("Corporation with ID %(id)s not found")
                        % {"id": owner_id}
                    }

                name = corp.name
                AllianceOwner.objects.filter(corporation=corp).delete()
                corp.delete()
                return HTTPStatus.OK, {
                    "message": _("Corporation %(name)s deleted successfully.")
                    % {"name": name}
                }

            if owner_type == "alliance":
                try:
                    ally = AllianceOwner.objects.get(eve_alliance__alliance_id=owner_id)
                except AllianceOwner.DoesNotExist:
                    return HTTPStatus.NOT_FOUND, {
                        "error": _("Alliance with ID %(id)s not found")
                        % {"id": owner_id}
                    }

                name = ally.name
                ally.delete()
                return HTTPStatus.OK, {
                    "message": _("Alliance %(name)s deleted successfully.")
                    % {"name": name}
                }

            return HTTPStatus.BAD_REQUEST, {"error": _("Invalid owner type specified.")}

        @api.get(
            "administration/owners/{str:owner_type}/{int:owner_id}/inspect/",
            response={
                HTTPStatus.OK: admin.DashboardResponse,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.BAD_REQUEST: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Inspect a corporation or alliance owner dashboard",
        )
        def inspect_administration_owner(
            request: WSGIRequest,
            owner_type: str,
            owner_id: int,
        ):
            if not core.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, {
                    "error": _("Administration permission required.")
                }

            owner: CorporationOwner | AllianceOwner | None = None
            if owner_type == "corporation":
                try:
                    owner = CorporationOwner.objects.get(
                        eve_corporation__corporation_id=owner_id,
                        eve_corporation__corporation_id__gte=MIN_PLAYER_CORPORATION_ID,
                    )
                except CorporationOwner.DoesNotExist:
                    return HTTPStatus.NOT_FOUND, {
                        "error": _("Corporation with ID %(id)s not found")
                        % {"id": owner_id}
                    }
            elif owner_type == "alliance":
                try:
                    owner = AllianceOwner.objects.get(
                        eve_alliance__alliance_id=owner_id
                    )
                except AllianceOwner.DoesNotExist:
                    return HTTPStatus.NOT_FOUND, {
                        "error": _("Alliance with ID %(id)s not found")
                        % {"id": owner_id}
                    }
            else:
                return HTTPStatus.BAD_REQUEST, {
                    "error": _("Invalid owner type specified.")
                }

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

            common_data = create_dashboard_common_data(owner, divisions)
            dashboard_response = admin.DashboardResponse(
                owner=schema.OwnerSchema(
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
            return HTTPStatus.OK, dashboard_response

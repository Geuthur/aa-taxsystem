# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api import schema
from taxsystem.helpers import lazy
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner


class ApiEndpoints:
    tags = ["Overview"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "overview/",
            response={
                HTTPStatus.OK: schema.OverviewSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get list of all visible Corporation and Alliance owners",
        )
        def get_overview(request: WSGIRequest):
            user = request.user
            if not user.has_perm("taxsystem.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            owner_list: list[schema.OwnerOverviewSchema] = []

            # Get visible corporations
            corporations = (
                CorporationOwner.objects.visible_to(user)
                .select_related("eve_corporation")
                .order_by("eve_corporation__corporation_name")
            )
            manageable_corps = set(CorporationOwner.objects.manage_to(user))
            for corporation in corporations:
                owner_list.append(
                    schema.OwnerOverviewSchema(
                        id=corporation.eve_corporation.corporation_id,
                        name=corporation.eve_corporation.corporation_name,
                        type="corporation",
                        type_display=_("Corporation"),
                        portrait_url=lazy.get_corporation_logo_url(
                            corporation.eve_corporation.corporation_id,
                            size=64,
                        ),
                        active=corporation.active,
                        open_invoices=corporation.payment_model.objects.get_owner_open_invoices(
                            user=user, owner=corporation
                        ),
                        can_manage=corporation in manageable_corps,
                    )
                )

            # Get visible alliances
            alliances = (
                AllianceOwner.objects.visible_to(user)
                .select_related("eve_alliance")
                .order_by("eve_alliance__alliance_name")
            )
            manageable_allies = set(AllianceOwner.objects.manage_to(user))
            for alliance in alliances:
                owner_list.append(
                    schema.OwnerOverviewSchema(
                        id=alliance.eve_alliance.alliance_id,
                        name=alliance.eve_alliance.alliance_name,
                        type="alliance",
                        type_display=_("Alliance"),
                        portrait_url=lazy.get_alliance_logo_url(
                            alliance.eve_alliance.alliance_id,
                            size=64,
                        ),
                        active=alliance.active,
                        open_invoices=alliance.payment_model.objects.get_owner_open_invoices(
                            user=user, owner=alliance
                        ),
                        can_manage=alliance in manageable_allies,
                    )
                )

            return schema.OverviewSchema(
                owners=owner_list,
                total_count=len(owner_list),
            )

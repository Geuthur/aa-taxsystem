# Standard Library
import json

# Third Party
from ninja import NinjaAPI

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.handlers.wsgi import WSGIRequest
from django.utils.text import format_lazy
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__, forms
from taxsystem.api.helpers import core
from taxsystem.api.helpers.icons import (
    get_filter_delete_button,
    get_filter_set_action_icons,
    get_filter_set_active_icon,
)
from taxsystem.api.schema import (
    DataTableSchema,
    FilterModelSchema,
    FilterSetModelSchema,
)
from taxsystem.models.corporation import (
    CorporationOwner,
)
from taxsystem.models.helpers.textchoices import (
    AdminActions,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class FilterApiEndpoints:
    tags = ["Filter Management"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "owner/{owner_id}/filter-set/{filterset_pk}/view/filter/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_filters(request, owner_id: int, filterset_pk: int):
            """
            Handle an Request to retrieve Filters for a Filter Set.
            This Endpoint retrieves the filters for a filter set for a owner.
            It validates the request, checks permissions, and retrieves the according filters.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                filter_pk (int): The ID of the filter set whose filters are to be retrieved.
            Returns:
                list[FilterModelSchema]: A list of filter schema objects.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            filters = owner.filter_model.objects.filter(
                filter_set__pk=filterset_pk,
            ).select_related("filter_set", "filter_set__owner")

            response_filter_list: list[FilterModelSchema] = []
            for filter_obj in filters:
                if filter_obj.filter_type == filter_obj.__class__.FilterType.AMOUNT:
                    display = f"{intcomma(filter_obj.value)} ISK"
                else:
                    display = str(filter_obj.value)

                response_filter = FilterModelSchema(
                    filter_set=FilterSetModelSchema(
                        owner_id=filter_obj.filter_set.owner.pk,
                        name=filter_obj.filter_set.name,
                        description=filter_obj.filter_set.description,
                        enabled=filter_obj.filter_set.enabled,
                    ),
                    filter_type=filter_obj.get_filter_type_display(),
                    value=DataTableSchema(
                        raw=filter_obj.value,
                        display=display,
                        sort=str(filter_obj.value),
                    ),
                    actions=get_filter_delete_button(filter_obj=filter_obj),
                )
                response_filter_list.append(response_filter)

            return response_filter_list

        @api.post(
            "owner/{owner_id}/filter/{filter_pk}/manage/delete-filter/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def delete_filter(request: WSGIRequest, owner_id: int, filter_pk: int):
            """
            Handle an Request to delete a Filter.

            This Endpoint deletes a filter from an associated owner.
            It validates the request, checks permissions, and deletes the according filter.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                filter_pk (int): The ID of the filter to be deleted.
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

            # Validate the form data
            form = (
                forms.DeleteCorporationFilterForm(data=json.loads(request.body))
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAllianceFilterForm(data=json.loads(request.body))
            )
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            # Check if filter set exists
            filter_obj = owner.filter_model.objects.filter(
                filter_set__owner=owner, pk=filter_pk
            ).first()
            if not filter_obj:
                msg = _("Filter not found.")
                return 404, {"success": False, "message": msg}

            # Delete the filter
            filter_obj.delete()

            # Create log message
            msg = format_lazy(
                _('{filter_obj} in "{filter_set}" deleted - Reason: {reason}'),
                filter_obj=filter_obj,
                filter_set=filter_obj.filter_set.name,
                reason=form.cleaned_data["comment"],
            )
            # Log the deletion in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                action=AdminActions.DELETE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

        @api.get(
            "owner/{owner_id}/view/filter-set/",
            response={200: list, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_filter_set(request, owner_id: int):
            """
            This Endpoint retrieves the filter set for an owner.
            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
            Returns:
                list[FilterSetModelSchema]: A list of filter set schema objects.
            """
            # pylint: disable=duplicate-code
            owner, perms = core.get_manage_owner(request, owner_id)

            if owner is None:
                return 404, {"error": _("Owner not Found.")}

            if perms is False:
                return 403, {"error": _("Permission Denied.")}

            filter_sets = owner.filterset_model.objects.filter(
                owner=owner,
            ).select_related("owner")

            response_filter_list: list[FilterSetModelSchema] = []
            for filter_set in filter_sets:
                response_filter = FilterSetModelSchema(
                    owner_id=filter_set.owner.pk,
                    name=filter_set.name,
                    description=filter_set.description,
                    enabled=filter_set.enabled,
                    status=DataTableSchema(
                        raw=filter_set.enabled,
                        display=get_filter_set_active_icon(filter_set=filter_set),
                        sort=str(int(filter_set.enabled)),
                    ),
                    actions=get_filter_set_action_icons(
                        request=request, filter_set=filter_set
                    ),
                )
                response_filter_list.append(response_filter)

            return response_filter_list

        @api.post(
            "owner/{owner_id}/filter-set/{filterset_pk}/manage/delete-filter/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def delete_filter_set(request: WSGIRequest, owner_id: int, filterset_pk: int):
            """
            Handle an Request to delete a Filter Set.

            This Endpoint deletes a filter set for a owner.
            It validates the request, checks permissions, and deletes the according filter set.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                filter_pk (int): The ID of the filter to be deleted.
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

            # Validate the form data
            form = (
                forms.DeleteCorporationFilterSetForm(data=json.loads(request.body))
                if isinstance(owner, CorporationOwner)
                else forms.DeleteAllianceFilterSetForm(data=json.loads(request.body))
            )
            if not form.is_valid():
                msg = _("Invalid form data.")
                return 400, {"success": False, "message": msg}

            # Check if filter set exists
            filter_set = owner.filterset_model.objects.filter(
                owner=owner, pk=filterset_pk
            ).first()
            if not filter_set:
                msg = _("Filter Set not found.")
                return 404, {"success": False, "message": msg}

            # Delete the filter set
            filter_set.delete()

            # Create log message
            msg = format_lazy(
                _("{filter_set} deleted - Reason: {reason}"),
                filter_set=filter_set,
                reason=form.cleaned_data["comment"],
            )

            # Log the deletion in Admin History
            owner.admin_log_model(
                user=request.user,
                owner=owner,
                action=AdminActions.DELETE,
                comment=msg,
            ).save()

            # Return success response
            return 200, {"success": True, "message": msg}

        @api.post(
            "owner/{owner_id}/filter-set/{filterset_pk}/manage/switch-filter/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def switch_filter_set(request: WSGIRequest, owner_id: int, filterset_pk: int):
            """
            Handle an Request to Switch a Filter Set.

            This Endpoint handle an Request to switching a filter set from an associated owner depending on its current state.
            It validates the request, checks permissions, and toggles the enabled state of the according filter set.

            Args:
                request (WSGIRequest): The HTTP request object.
                owner_id (int): The ID of the owner whose filter set is to be retrieved.
                filter_pk (int): The ID of the filter set to be switched.
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

            # Check if filter set exists
            filter_set = owner.filterset_model.objects.filter(
                owner=owner, pk=filterset_pk
            ).first()
            if not filter_set:
                msg = _("Filter Set not found.")
                return 404, {"success": False, "message": msg}

            # Toggle the filter set enabled state
            filter_set.enabled = not filter_set.enabled
            filter_set.save()

            # Create log message
            msg = format_lazy(
                _("{filter_set} switched to {enabled}"),
                filter_set=filter_set,
                enabled=filter_set.enabled,
            )

            # Return success response
            return 200, {"success": True, "message": msg}

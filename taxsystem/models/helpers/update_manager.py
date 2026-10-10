# Standard Library
from http import HTTPStatus
from typing import TYPE_CHECKING, Union

# Third Party
from aiopenapi3 import RequestError

# Django
from django.db import models
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.general import (
    UpdateSectionResult,
    _NeedsUpdate,
)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.alliance import AllianceOwner, AllianceUpdateStatus
    from taxsystem.models.corporation import CorporationOwner, CorporationUpdateStatus
    from taxsystem.models.helpers.textchoices import (
        AllianceUpdateSection,
        CorporationUpdateSection,
    )

# AA TaxSystem
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class UpdateManager:
    """Manager class to handle update operations for CorporationOwner and AllianceOwner.
    This class provides methods to manage and track update statuses for both corporation and alliance owners.

    Args:
        owner (CorporationOwner | AllianceOwner): The owner model (corporation or alliance)
        update_section (CorporationUpdateSection | AllianceUpdateSection): The update section class (CorporationUpdateSection or AllianceUpdateSection)
        update_status (CorporationUpdateStatus | AllianceUpdateStatus): The update status class (CorporationUpdateStatus or AllianceUpdateStatus)
    """

    def __init__(
        self,
        owner: Union["CorporationOwner", "AllianceOwner"],
        update_section: Union["CorporationUpdateSection", "AllianceUpdateSection"],
        update_status: Union["CorporationUpdateStatus", "AllianceUpdateStatus"],
    ):
        self.owner = owner
        self.update_section = update_section
        self.update_status = update_status

    # Shared methods
    def calc_update_needed(self):
        """
        Calculate which sections need an update and save the results in a _NeedsUpdate object.

        Returns:
            _NeedsUpdate: An object containing a mapping of sections to their update needs.
        """
        sections_needs_update = {
            section: True for section in self.update_section.get_sections()
        }
        existing_sections = self.update_status.objects.filter(owner=self.owner)
        needs_update = {
            obj.section: obj.need_update()
            for obj in existing_sections
            if obj.section in sections_needs_update
        }
        sections_needs_update.update(needs_update)
        return _NeedsUpdate(section_map=sections_needs_update)

    def reset_update_status(self, section):
        """
        Create or Reset the update status for a specific section.

        Args:
            section (models.TextChoices): The section to reset.
        Returns:
            UpdateStatus (Object): The reset update status object for the Owner Model.
        """
        update_status_obj = self.update_status.objects.get_or_create(
            owner=self.owner,
            section=section,
        )[0]
        update_status_obj.reset()
        return update_status_obj

    def reset_has_token_error(self) -> None:
        """
        Reset has_token_error for all sections.

        Returns:
            None
        """
        self.update_status.objects.filter(
            has_token_error=True,
        ).update(
            has_token_error=False,
        )

    def update_section_if_changed(
        self, section, fetch_func, force_refresh: bool = False
    ):
        """
        Handle updating a specific section if there are changes.

        Args:
            section (models.TextChoices): The section to update.
            fetch_func (Callable): The function to fetch the data for the section.
            force_refresh (bool): Whether to force a refresh of the data.
        Returns:
            UpdateSectionResult: The result of the update operation.
        """
        section = self.update_section(section)
        try:
            data = fetch_func(owner=self.owner, force_refresh=force_refresh)
            logger.debug(
                "%s: Update has changed, section: %s", self.owner, section.label
            )
        except HTTPNotModified:
            logger.debug(
                "%s: Update has not changed, section: %s", self.owner, section.label
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=False,
                error_message="",
            )
        except (HTTPServerError, RequestError) as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.debug(
                "%s: %s: ESI Server/Request Error encountered: %s",
                self.owner,
                section.label,
                error_message,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=False,
                error_message=error_message,
            )
        except HTTPClientError as exc:
            error_message = f"{type(exc).__name__} ({exc.status_code}): {str(exc)}"
            is_token_problem = exc.status_code in [
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
                HTTPStatus.NOT_FOUND,
            ]
            if is_token_problem:
                logger.warning(
                    "%s: %s: ESI Token/Permission problem: %s",
                    self.owner,
                    section.label,
                    error_message,
                )
            else:
                logger.error(
                    "%s: %s: ESI Client Error: %s",
                    self.owner,
                    section.label,
                    error_message,
                )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=is_token_problem,
                error_message=error_message,
            )
        return UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            data=data,
        )

    def update_section_log(
        self, section: models.TextChoices, result: UpdateSectionResult
    ) -> None:
        """
        Update the status of a specific section.
        Args:
            section (models.TextChoices): The section to update.
            result (UpdateSectionResult): The result of the update operation.
        Returns:
            None
        """
        error_message = result.error_message if result.error_message else ""
        is_success = not result.has_token_error and not bool(error_message)
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": result.has_token_error,
            "last_run_finished_at": timezone.now(),
        }
        obj = self.update_status.objects.update_or_create(
            owner=self.owner,
            section=section,
            defaults=defaults,
        )[0]
        if result.is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self.owner, section.label, status)

    def perform_update_status(
        self, section: models.TextChoices, method, *args, **kwargs
    ) -> UpdateSectionResult:
        """
        Perform update status.
        Args:
            section (models.TextChoices): The section to update.
            method (Callable): The method to perform the update.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.
        Returns:
            UpdateSectionResult: The result of the update operation.
        """
        try:
            result = method(*args, **kwargs)
        except (HTTPServerError, RequestError) as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.debug(
                "%s: %s: Server/Request Error during update: %s",
                self.owner,
                section.label,
                error_message,
            )
            result = UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=False,
                error_message=error_message,
            )
        except TokenError as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.warning(
                "%s: %s: Token error during update: %s",
                self.owner,
                section.label,
                error_message,
            )
            result = UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=True,
                error_message=error_message,
            )
        except Exception as exc:  # pylint: disable=broad-except
            error_message = f"{type(exc).__name__}: {str(exc)}"
            # pylint: disable=no-member
            is_token_problem = isinstance(exc, HTTPClientError) and exc.status_code in [
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
                HTTPStatus.NOT_FOUND,
            ]
            if is_token_problem:
                logger.warning(
                    "%s: %s: Token error during update: %s",
                    self.owner,
                    section.label,
                    error_message,
                )
            else:
                logger.error(
                    "%s: %s: Error during update status: %s",
                    self.owner,
                    section.label,
                    error_message,
                )
            result = UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=is_token_problem,
                error_message=error_message,
            )
        return result

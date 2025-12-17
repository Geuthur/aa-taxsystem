"""General Model"""

# Standard Library
from dataclasses import dataclass
from typing import Any, NamedTuple

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _


class General(models.Model):
    """General model for app permissions"""

    class Meta:
        managed = False
        permissions = (
            ("basic_access", _("Can access the Tax System")),
            ("create_access", _("Can add Corporation/Alliance")),
            ("manage_own_corp", _("Can manage own Corporation")),
            ("manage_corps", _("Can manage all Corporations")),
            ("manage_own_alliance", _("Can manage own Alliance")),
            ("manage_alliances", _("Can manage all Alliances")),
        )
        default_permissions = ()


class UpdateSectionResult(NamedTuple):
    """
    A result of an attempted section update.

    Attributes:
        is_changed (bool | None): Whether the data has changed. None if unknown.
        is_updated (bool): Whether the update was successful.
        has_token_error (bool): Whether there was a token error during the update.
        error_message (str | None): An error message if applicable.
        data (Any): The data fetched during the update.
    """

    is_changed: bool | None
    is_updated: bool
    has_token_error: bool = False
    error_message: str | None = None
    data: Any = None


@dataclass(frozen=True)
class _NeedsUpdate:
    """
    An Object to track if an update is needed.

    Results:
        section_map (dict[str, bool]): A mapping of sections to their update needs.
    """

    section_map: dict[str, bool]

    def __bool__(self) -> bool:
        """Check if any section needs an update."""
        return any(self.section_map.values())

    def for_section(self, section: str) -> bool:
        """Check if an update is needed for a specific section."""
        return self.section_map.get(section, False)

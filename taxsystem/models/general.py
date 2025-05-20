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
            ("create_access", _("Can add Corporation")),
            ("manage_own_corp", _("Can manage own Corporation")),
            ("manage_corps", _("Can manage all Corporations")),
        )
        default_permissions = ()


class UpdateSectionResult(NamedTuple):
    """A result of an attempted section update."""

    is_changed: bool | None
    is_updated: bool
    data: Any = None


@dataclass(frozen=True)
class _NeedsUpdate:
    """An Object to track if an update is needed."""

    section_map: dict[str, bool]

    def __bool__(self) -> bool:
        """Check if any section needs an update."""
        return any(self.section_map.values())

    def for_section(self, section: str) -> bool:
        """Check if an update is needed for a specific section."""
        return self.section_map.get(section, False)

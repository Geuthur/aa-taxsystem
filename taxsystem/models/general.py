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
            ("manage_own_alliance", _("Can manage own Alliance")),
            ("manage_alliances", _("Can manage all Alliances")),
        )
        default_permissions = ()


class UpdateSection(models.TextChoices):
    """Base class for update sections."""

    @classmethod
    def get_sections(cls) -> list[str]:
        """Return list of section values."""
        return [choice.value for choice in cls]

    @property
    def method_name(self) -> str:
        """Return method name for this section."""
        return f"update_{self.value}"


class CorporationUpdateSection(UpdateSection):
    """Sections for corporation updates."""

    DIVISION_NAMES = "division_names", _("Wallet Division Names")
    DIVISION = "division", _("Wallet Division")
    WALLET = "wallet", _("Wallet Journal")
    MEMBERS = "members", _("Members")
    PAYMENT_SYSTEM = "payment_system", _("Payment System")
    PAYMENTS = "payments", _("Payments")
    PAYDAY = "payday", _("Payday")


class AllianceUpdateSection(UpdateSection):
    """Sections for alliance updates."""

    PAYMENT_SYSTEM = "payment_system", _("Payment System")
    PAYMENTS = "payments", _("Payments")
    PAYDAY = "payday", _("Payday")


class UpdateSectionResult(NamedTuple):
    """A result of an attempted section update."""

    is_changed: bool | None
    is_updated: bool
    has_token_error: bool = False
    error_message: str | None = None
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

"""General Model"""

# Standard Library
from dataclasses import dataclass
from typing import Any, NamedTuple

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.managers.eveonline_manager import EveEntityManager


class UserSettings(models.Model):
    """Per-user preferences."""

    class Meta:
        default_permissions = ()

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="taxsystem_settings"
    )

    disable_notifications = models.BooleanField(default=False)


class General(models.Model):
    """A model defining commonly used permissions and helper methods for TaxSystem."""

    class Permission(models.TextChoices):
        """All permissions of the app. The value is the permission codename."""

        BASIC_ACCESS = "basic_access", _("Can access the Tax System")
        CREATE_ACCESS = "create_access", _("Can add Corporation/Alliance")
        MANAGE_OWN_CORP = "manage_own_corp", _("Can manage own Corporation")
        MANAGE_CORPS = "manage_corps", _("Can manage all Corporations")
        MANAGE_OWN_ALLIANCE = "manage_own_alliance", _("Can manage own Alliance")
        MANAGE_ALLIANCES = "manage_alliances", _("Can manage all Alliances")
        ADMIN_ACCESS = "admin_access", _("Has access to the Administration.")

    class Meta:
        managed = False
        verbose_name = "AA-TaxSystem"
        verbose_name_plural = "AA-TaxSystem"
        default_permissions = ()

    # Inject dynamic permissions
    Meta.permissions = Permission.choices

    @classmethod
    def get_perm(cls, perm: "str | Permission") -> str:
        """Return full permission string 'taxsystem.<codename>'."""
        codename = perm.value if isinstance(perm, cls.Permission) else perm
        return f"taxsystem.{codename}"

    @classmethod
    def has_perm(cls, user: Any, perm: "str | General.Permission") -> bool:
        """Check if the user has the permission."""
        if not user or not hasattr(user, "has_perm"):
            return False
        return user.has_perm(cls.get_perm(perm))

    @classmethod
    def has_any_perm(cls, user: Any, *perms: "str | General.Permission") -> bool:
        """Return True if the user has any of the specified permissions."""
        if not user or not hasattr(user, "has_perm"):
            return False
        return any(user.has_perm(cls.get_perm(p)) for p in perms)


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


class EveEntity(models.Model):
    """Model representing an EVE Online entity, such as a character, corporation, or alliance."""

    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()

    objects: EveEntityManager = EveEntityManager()

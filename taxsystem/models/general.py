"""General Model"""

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.managers.eveonline_manager import EveEntityManager
from taxsystem.managers.general import GeneralManager


class UserSettings(models.Model):
    """Per-user preferences."""

    class Meta:
        default_permissions = ()

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="taxsystem_settings"
    )

    disable_notifications = models.BooleanField(default=False)


class General(models.Model):
    """A model defining the permissions of TaxSystem.

    Permissions are checked with Django and the full string, e.g.
    `@permission_required("taxsystem.basic_access")` or
    `user.has_perm("taxsystem.basic_access")`.
    """

    objects = GeneralManager()

    class Meta:
        managed = False
        verbose_name = "AA-TaxSystem"
        verbose_name_plural = "AA-TaxSystem"
        default_permissions = ()
        permissions = (
            ("basic_access", _("Can access the Tax System")),
            ("create_access", _("Can add Corporation/Alliance")),
            ("manage_own_corp", _("Can manage own Corporation")),
            ("manage_corps", _("Can manage all Corporations")),
            ("manage_own_alliance", _("Can manage own Alliance")),
            ("manage_alliances", _("Can manage all Alliances")),
            ("admin_access", _("Has access to the whole Administration.")),
        )


class EveEntity(models.Model):
    """Model representing an EVE Online entity, such as a character, corporation, or alliance."""

    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()

    objects: EveEntityManager = EveEntityManager()

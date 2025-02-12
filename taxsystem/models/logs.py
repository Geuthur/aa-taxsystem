"""Logs Model"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import User

from taxsystem.managers.logs_manager import LogsManager


class Logs(models.Model):
    """Logs Model for app"""

    class Actions(models.TextChoices):
        """Actions for Logs"""

        APPROVED = "approved", _("Approved")
        CANCELED = "canceled", _("Canceled")
        CREATED = "created", _("Created")
        CONFIRMED = "confirmed", _("Confirmed")
        DECLINED = "declined", _("Declined")
        DELETED = "deleted", _("Deleted")
        VIEWED = "viewed", _("Viewed")
        UPDATED = "updated", _("Updated")
        UNDO = "undo", _("Undo")

    class Levels(models.TextChoices):
        """Levels for Logs"""

        CRITICAL = "critical", _("Critical")
        IMPORTANT = "important", _("Important")
        INFO = "info", _("Info")
        UNNECESSARY = "unnecessary", _("Unnecessary")

    class Meta:
        default_permissions = ()

    objects = LogsManager()

    corporation = models.ForeignKey(
        "OwnerAudit",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Corporation"),
        help_text=_("Corporation that the action was performed on"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("User"),
        help_text=_("User that performed the action"),
    )

    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date"),
        help_text=_("Date of the action"),
    )

    action = models.CharField(
        max_length=16,
        choices=Actions.choices,
        verbose_name=_("Action"),
        help_text=_("Action performed"),
    )

    log = models.TextField(
        verbose_name=_("Log"),
        help_text=_("Log of the action"),
    )

    level = models.CharField(
        max_length=16,
        verbose_name=_("Level"),
        help_text=_("Level of the log"),
    )

    def __str__(self):
        return f"{self.date}: {self.user} - {self.action} - {self.log}"

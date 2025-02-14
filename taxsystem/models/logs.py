"""Logs Model"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import User

from taxsystem.managers.logs_manager import LogsManager
from taxsystem.models.tax import Payments


class Logs(models.Model):
    """Logs Model for app"""

    class Actions(models.TextChoices):
        """Actions for Logs"""

        DEFAULT = "", ""
        STATUS_CHANGE = "Status Changed", _("Status Changed")
        PAYMENT_ADDED = "Payment Added", _("Payment Added")
        REVISER_COMMENT = "Reviser Comment", _("Reviser Comment")

    class Meta:
        default_permissions = ()

    objects = LogsManager()

    payment = models.ForeignKey(
        Payments,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Payment"),
        help_text=_("Payment that the action was performed on"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("User"),
        help_text=_("User that performed the action"),
    )

    date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Date"),
        help_text=_("Date of the action"),
    )

    action = models.CharField(
        max_length=20,
        choices=Actions.choices,
        default=Actions.DEFAULT,
        verbose_name=_("Action"),
        help_text=_("Action performed"),
    )

    comment = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Comment"),
    )

    new_status = models.CharField(
        max_length=16,
        choices=Payments.RequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )

    def __str__(self):
        return f"{self.date}: {self.user} - {self.action} - {self.log}"

"""Logs Model"""

# Django
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import User

# AA TaxSystem
from taxsystem.managers.logs_manager import LogsManager
from taxsystem.models.tax import OwnerAudit, Payments


class PaymentHistory(models.Model):
    """PaymentHistory Model for app"""

    class SystemText(models.TextChoices):
        DEFAULT = "", ""
        ADDED = "Payment added to system", _("Payment added to system")
        AUTOMATIC = "Automated approved Payment", _("Automated approved Payment")
        REVISER = "Payment must be approved by an reviser", _(
            "Payment must be approved by an reviser"
        )

    class Actions(models.TextChoices):
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

    comment = models.CharField(
        max_length=255,
        choices=SystemText.choices,
        default=SystemText.DEFAULT,
        verbose_name=_("Comment"),
        help_text=_("Comment of the action"),
    )

    new_status = models.CharField(
        max_length=16,
        choices=Payments.RequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )

    def __str__(self):
        return f"{self.date}: {self.user} - {self.action} - {self.comment}"


class AdminLogs(models.Model):
    """Logs Model for app"""

    class Actions(models.TextChoices):
        DEFAULT = "", ""
        ADD = "Added", _("Added")
        CHANGE = "Changed", _("Changed")
        DELETE = "Deleted", _("Deleted")

    class Meta:
        default_permissions = ()

    objects = LogsManager()

    owner = models.ForeignKey(
        OwnerAudit,
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

    def __str__(self):
        return f"{self.date}: {self.user} - {self.action} - {self.comment}"

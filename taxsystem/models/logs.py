"""Models for Tax System."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.alliance import AllianceOwner, AlliancePayments
from taxsystem.models.base import (
    PaymentHistoryBaseModel,
)
from taxsystem.models.corporation import CorporationOwner, CorporationPayments
from taxsystem.models.helpers.textchoices import (
    PaymentRequestStatus,
)


class AdminActions(models.TextChoices):
    DEFAULT = "", ""
    ADD = "Added", _("Added")
    CHANGE = "Changed", _("Changed")
    DELETE = "Deleted", _("Deleted")


class AlliancePaymentHistory(PaymentHistoryBaseModel):
    """Model representing the history of actions taken on alliance payments in the tax system."""

    class Meta:
        default_permissions = ()

    # pylint: disable=duplicate-code
    payment = models.ForeignKey(
        AlliancePayments,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Payment"),
        help_text=_("Payment that the action was performed on"),
    )
    # pylint: enable=duplicate-code
    new_status = models.CharField(
        max_length=20,
        choices=PaymentRequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )


class AllianceAdminHistory(PaymentHistoryBaseModel):
    """
    Model representing the history of administrative actions taken on owners in the tax system.
    """

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        AllianceOwner,
        verbose_name=_("Owner"),
        help_text=_("Owner that the action was performed on"),
        on_delete=models.CASCADE,
        related_name="ts_admin_history",
    )

    action = models.CharField(
        max_length=20,
        choices=AdminActions.choices,
        default=AdminActions.DEFAULT,
        verbose_name=_("Action"),
        help_text=_("Action performed"),
    )


class CorporationPaymentHistory(PaymentHistoryBaseModel):
    """Model representing the history of actions taken on corporation payments in the tax system."""

    class Meta:
        default_permissions = ()

    payment = models.ForeignKey(
        CorporationPayments,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Payment"),
        help_text=_("Payment that the action was performed on"),
    )

    new_status = models.CharField(
        max_length=20,
        choices=PaymentRequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )


class CorporationAdminHistory(PaymentHistoryBaseModel):
    """
    Model representing the history of administrative actions taken on owners in the tax system.
    """

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        CorporationOwner,
        verbose_name=_("Owner"),
        help_text=_("Owner that the action was performed on"),
        on_delete=models.CASCADE,
        related_name="ts_admin_history",
    )

    action = models.CharField(
        max_length=20,
        choices=AdminActions.choices,
        default=AdminActions.DEFAULT,
        verbose_name=_("Action"),
        help_text=_("Action performed"),
    )

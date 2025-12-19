"""Models for Tax System."""

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import OwnershipRecord, User
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, app_settings
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    PaymentActions,
    PaymentRequestStatus,
    PaymentStatus,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.wallet import CorporationWalletJournalEntry


class PaymentsBaseModel(models.Model):
    """Basemodel for Payments in Tax System"""

    class Meta:
        abstract = True
        default_permissions = ()

    name = models.CharField(max_length=100)

    entry_id = models.BigIntegerField(null=True, blank=True)

    journal = models.OneToOneField(
        "CorporationWalletJournalEntry",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    date = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(null=True, blank=True)

    request_status = models.CharField(
        max_length=16,
        choices=PaymentRequestStatus.choices,
        default=PaymentRequestStatus.PENDING,
        verbose_name=_("Request Status"),
    )

    reviser = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=_("Reviser that approved or rejected the payment"),
    )

    @property
    def is_automatic(self) -> bool:
        return self.reviser == "System"

    @property
    def is_pending(self) -> bool:
        return self.request_status == PaymentRequestStatus.PENDING

    @property
    def is_needs_approval(self) -> bool:
        return self.request_status == PaymentRequestStatus.NEEDS_APPROVAL

    @property
    def is_approved(self) -> bool:
        return self.request_status == PaymentRequestStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.request_status == PaymentRequestStatus.REJECTED

    @property
    def character_id(self) -> int:
        """
        Return the character ID or first OwnershipRecord from user who made the payment.

        Returns:
            int: Character ID
        """
        try:
            character_id = self.account.user.profile.main_character.character_id
        except AttributeError:
            character = OwnershipRecord.objects.filter(user=self.account.user).first()
            character_id = character.character.character_id
        return character_id

    @property
    def division_name(self) -> "CorporationWalletJournalEntry":
        """
        Returns:
            str: The name of the division or "N/A".
        """
        if not self.journal:
            return "N/A"
        return self.journal.division.name

    def get_request_status(self) -> str:
        return self.get_request_status_display()

    @property
    def formatted_payment_date(self) -> str:
        if self.date:
            return timezone.localtime(self.date).strftime("%Y-%m-%d %H:%M:%S")
        return _("No date")


class PaymentAccountBaseModel(models.Model):
    """Basemodel for Payment User Accounts in Tax System"""

    class Meta:
        abstract = True
        default_permissions = ()

    name = models.CharField(
        max_length=100,
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="+")

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(
        max_length=16,
        choices=AccountStatus.choices,
        blank=True,
        default=AccountStatus.ACTIVE,
    )

    deposit = models.DecimalField(
        max_digits=16,
        decimal_places=0,
        default=0,
        help_text=_("Deposit Pool in ISK. Max 16 Digits"),
        validators=[
            MaxValueValidator(9999999999999999),
            MinValueValidator(-9999999999999999),
        ],
    )

    last_paid = models.DateTimeField(null=True, blank=True)

    notice = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.date} - {self.status}"

    def get_payment_status(self) -> str:
        return self.get_status_display()

    def get_alt_ids(self) -> list[int]:
        return list(
            self.user.character_ownerships.all().values_list(
                "character__character_id", flat=True
            )
        )

    @property
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE

    @property
    def is_inactive(self) -> bool:
        return self.status == AccountStatus.INACTIVE

    @property
    def is_deactivated(self) -> bool:
        return self.status == AccountStatus.DEACTIVATED

    @property
    def is_missing(self) -> bool:
        return self.status == AccountStatus.MISSING

    @property
    def has_paid(self) -> bool:
        """
        Return True if user has paid for alliance.

        Returns:
            bool: True if paid, False otherwise.
        """
        subclass = getattr(self, "owner", None)
        if not subclass:
            raise NotImplementedError(
                "has_paid property must be implemented in subclass"
            )

        if self.deposit >= self.owner.tax_amount:
            return True
        if self.last_paid and self.deposit >= 0:
            return (timezone.now() - self.last_paid) < timezone.timedelta(
                days=self.owner.tax_period
            )
        return False

    @property
    def next_due(self):
        """
        Return the next due date for alliance payment.

        Returns:
            datetime or None: Next due date or None if inactive/deactivated or never paid.
        """
        subclass = getattr(self, "owner", None)
        if not subclass:
            raise NotImplementedError(
                "has_paid property must be implemented in subclass"
            )

        if self.status in [AccountStatus.INACTIVE, AccountStatus.DEACTIVATED]:
            return None
        if self.last_paid:
            return self.last_paid + timezone.timedelta(days=self.owner.tax_period)
        return None

    def has_paid_icon(self, badge=False, text=False) -> str:
        """
        Return the HTML icon for has_paid.

        Returns:
            str: HTML icon string.
        """
        color = "success" if self.has_paid else "danger"

        if self.has_paid:
            html = f"<i class='fas fa-check' title='{PaymentStatus('paid').label}' data-bs-tooltip='aa-taxsystem'></i>"
        else:
            html = f"<i class='fas fa-times' title='{PaymentStatus('unpaid').label}' data-bs-tooltip='aa-taxsystem'></i>"

        if text:
            html += f" {PaymentStatus('paid').label if self.has_paid else PaymentStatus('unpaid').label}"

        if badge:
            html = mark_safe(f"<span class='badge bg-{color}'>{html}</span>")
        return html


class UpdateStatusBaseModel(models.Model):
    """Base Model for owner update status."""

    class Meta:
        abstract = True
        default_permissions = ()

    is_success = models.BooleanField(default=None, null=True, db_index=True)
    error_message = models.TextField()
    has_token_error = models.BooleanField(default=False)

    last_run_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last run has been started at this time",
    )
    last_run_finished_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last run has been successful finished at this time",
    )
    last_update_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been started at this time",
    )
    last_update_finished_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been successful finished at this time",
    )

    def need_update(self) -> bool:
        """Check if the update is needed."""
        if not self.is_success or not self.last_update_finished_at:
            needs_update = True
        else:
            section_time_stale = app_settings.TAXSYSTEM_STALE_TYPES.get(
                self.section, 60
            )
            stale = timezone.now() - timezone.timedelta(minutes=section_time_stale)
            needs_update = self.last_run_finished_at <= stale

        if needs_update and self.has_token_error:
            logger.info(
                "%s: Ignoring update because of token error, section: %s",
                self.owner,
                self.section,
            )
            needs_update = False

        return needs_update

    def reset(self) -> None:
        """Reset this update status."""
        self.is_success = None
        self.error_message = ""
        self.has_token_error = False
        self.last_run_at = timezone.now()
        self.last_run_finished_at = None
        self.save()


class FilterBaseModel(models.Model):
    class Meta:
        abstract = True
        default_permissions = ()

    class FilterType(models.TextChoices):
        REASON = "reason", _("Reason")
        AMOUNT = "amount", _("Amount")

    filter_type = models.CharField(max_length=20, choices=FilterType.choices)
    value = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.filter_type}: {self.value}"

    def apply_filter(
        self, qs: models.QuerySet  # pylint: disable=unused-argument
    ) -> models.QuerySet:
        raise NotImplementedError("Create apply_filter method")

    def apply_contains(
        self, qs: models.QuerySet  # pylint: disable=unused-argument
    ) -> models.QuerySet:
        raise NotImplementedError("Create apply_contains method")


class FilterSetBaseModel(models.Model):
    class Meta:
        abstract = True
        default_permissions = ()

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def is_active(self) -> bool:
        return self.enabled

    @property
    def is_active_html(self) -> mark_safe:
        if self.enabled:
            return mark_safe('<i class="fa-solid fa-check"></i>')
        return mark_safe('<i class="fa-solid fa-times"></i>')

    def filter(
        self, payments: models.QuerySet  # pylint: disable=unused-argument
    ) -> models.QuerySet:
        raise NotImplementedError("Create filter method")

    def filter_contains(
        self, payments: models.QuerySet  # pylint: disable=unused-argument
    ) -> models.QuerySet:  # not implemented yet
        raise NotImplementedError("Create filter_contains method")


class HistoryBaseModel(models.Model):
    """Basemodel for Payments History"""

    class Meta:
        abstract = True
        default_permissions = ()

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
        choices=PaymentActions.choices,
        default=PaymentActions.DEFAULT,
        verbose_name=_("Action"),
        help_text=_("Action performed"),
    )

    comment = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Comment"),
        help_text=_("Comment of the action"),
    )

    def __str__(self):
        return f"{self.date}: {self.user} - {self.action} - {self.comment}"

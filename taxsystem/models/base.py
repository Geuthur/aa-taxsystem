"""Models for Tax System."""

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import OwnershipRecord, User
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, app_settings
from taxsystem.models.general import UpdateSection, UpdateSectionResult

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.wallet import CorporationWalletJournalEntry


class OwnerBase(models.Model):
    """Basemodel for Owner Audit in Tax System"""

    class Meta:
        abstract = True
        default_permissions = ()

    class UpdateStatus(models.TextChoices):
        DISABLED = "disabled", _("disabled")
        TOKEN_ERROR = "token_error", _("token error")
        ERROR = "error", _("error")
        OK = "ok", _("ok")
        INCOMPLETE = "incomplete", _("incomplete")
        IN_PROGRESS = "in_progress", _("in progress")

        def bootstrap_icon(self) -> str:
            """Return bootstrap corresponding icon class."""
            update_map = {
                status: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='taxsystem-tooltip' title='{self.description()}'>⬤</span>"
                )
                for status in [
                    self.DISABLED,
                    self.TOKEN_ERROR,
                    self.ERROR,
                    self.INCOMPLETE,
                    self.IN_PROGRESS,
                    self.OK,
                ]
            }
            return update_map.get(self, "")

        def bootstrap_text_style_class(self) -> str:
            """Return bootstrap corresponding bootstrap text style class."""
            update_map = {
                self.DISABLED: "text-muted",
                self.TOKEN_ERROR: "text-warning",
                self.INCOMPLETE: "text-warning",
                self.IN_PROGRESS: "text-info",
                self.ERROR: "text-danger",
                self.OK: "text-success",
            }
            return update_map.get(self, "")

        def description(self) -> str:
            """Return description for an enum object."""
            update_map = {
                self.DISABLED: _("Update is disabled"),
                self.TOKEN_ERROR: _("One section has a token error during update"),
                self.INCOMPLETE: _("One or more sections have not been updated"),
                self.IN_PROGRESS: _("Update is in progress"),
                self.ERROR: _("An error occurred during update"),
                self.OK: _("Updates completed successfully"),
            }
            return update_map.get(self, "")

    name = models.CharField(
        max_length=255,
    )

    active = models.BooleanField(default=True)

    tax_amount = models.DecimalField(
        max_digits=16,
        decimal_places=0,
        help_text=_("Tax Amount in ISK that is set for the corporation. Max 16 Digits"),
        default=0,
        validators=[MaxValueValidator(9999999999999999)],
    )

    tax_period = models.PositiveIntegerField(
        help_text=_(
            "Tax Period in days for the corporation. Max 365 days. Default: 30 days"
        ),
        default=30,
        validators=[MaxValueValidator(365)],
    )

    # Abstract properties that must be implemented by subclasses
    @property
    def update_status_manager(self) -> models.QuerySet["UpdateStatusBase"]:
        """Return the related manager for update status objects.

        Must be implemented by subclasses to return the appropriate
        related manager (e.g., self.ts_corporation_update_status or
        self.ts_alliance_update_status).
        """
        raise NotImplementedError(
            "Subclasses must implement 'update_status_manager' property"
        )

    @property
    def update_section_enum(self) -> "UpdateSection":
        """Return the update section enum class.

        Must be implemented by subclasses to return the appropriate
        section enum (e.g., CorporationUpdateSection or AllianceUpdateSection).
        """
        raise NotImplementedError(
            "Subclasses must implement 'update_section_enum' property"
        )

    # Shared methods
    def calc_update_needed(self):
        """Calculate if an update is needed."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.general import _NeedsUpdate

        sections_needs_update = {
            section: True for section in self.update_section_enum.get_sections()
        }
        existing_sections = self.update_status_manager.all()
        needs_update = {
            obj.section: obj.need_update()
            for obj in existing_sections
            if obj.section in sections_needs_update
        }
        sections_needs_update.update(needs_update)
        return _NeedsUpdate(section_map=sections_needs_update)

    def reset_update_status(self, section):
        """Reset the status of a given update section and return it."""
        update_status_obj = self.update_status_manager.get_or_create(
            section=section,
        )[0]
        update_status_obj.reset()
        return update_status_obj

    def reset_has_token_error(self) -> None:
        """Reset the has_token_error flag."""
        self.update_status_manager.filter(
            has_token_error=True,
        ).update(
            has_token_error=False,
        )

    def update_section_if_changed(
        self, section, fetch_func, force_refresh: bool = False
    ):
        """Update the status of a specific section if it has changed."""
        section = self.update_section_enum(section)
        try:
            data = fetch_func(owner=self, force_refresh=force_refresh)
            logger.debug("%s: Update has changed, section: %s", self, section.label)
        except HTTPServerError as exc:
            logger.debug("%s: Update has an HTTP internal server error: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPNotModified:
            logger.debug("%s: Update has not changed, section: %s", self, section.label)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPClientError as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error(
                "%s: %s: Update has Client Error: %s %s",
                self,
                section.label,
                error_message,
                exc.status_code,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=True,
                error_message=error_message,
            )
        return UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            data=data,
        )

    def update_section_log(
        self, section: models.TextChoices, result: UpdateSectionResult
    ) -> None:
        """Update the status of a specific section."""
        error_message = result.error_message if result.error_message else ""
        is_success = not result.has_token_error
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": result.has_token_error,
            "last_run_finished_at": timezone.now(),
        }
        obj = self.update_status_manager.update_or_create(
            section=section,
            defaults=defaults,
        )[0]
        if result.is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self, section.label, status)

    def perform_update_status(
        self, section: models.TextChoices, method, *args, **kwargs
    ):
        """Perform update status."""
        try:
            result = method(*args, **kwargs)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error(
                "%s: %s: Error during update status: %s",
                self,
                section.label,
                error_message,
            )
            self.update_status_manager.update_or_create(
                section=section,
                defaults={
                    "is_success": False,
                    "error_message": error_message,
                    "has_token_error": True,
                    "last_update_at": timezone.now(),
                },
            )
            raise exc
        return result

    @property
    def get_update_status(self) -> dict[str, str]:
        """Return a dictionary of update sections and their statuses."""
        update_status = {}
        for section in self.update_section_enum.get_sections():
            try:
                status = self.update_status_manager.get(section=section)
                update_status[section] = {
                    "is_success": status.is_success,
                    "last_update_finished_at": status.last_update_finished_at,
                    "last_run_finished_at": status.last_run_finished_at,
                }
            except self.update_status_manager.model.DoesNotExist:
                continue
        return update_status


class PaymentAccountBase(models.Model):
    """Basemodel for Payment User Accounts in Tax System"""

    class Meta:
        abstract = True
        default_permissions = ()

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        DEACTIVATED = "deactivated", _("Deactivated")
        MISSING = "missing", _("Missing")

        def html(self, text=False) -> mark_safe:
            """Return the HTML for the status."""
            if text:
                return format_html(
                    f"<span class='badge bg-{self.color()}' data-tooltip-toggle='taxsystem-tooltip' title='{self.label}'>{self.label}</span>"
                )
            return format_html(
                f"<span class='btn btn-sm btn-square bg-{self.color()}' data-tooltip-toggle='taxsystem-tooltip' title='{self.label}'>{self.icon()}</span>"
            )

        def color(self) -> str:
            """Return bootstrap corresponding icon class."""
            status_map = {
                self.ACTIVE: "success",
                self.INACTIVE: "warning",
                self.DEACTIVATED: "danger",
                self.MISSING: "info",
            }
            return status_map.get(self, "secondary")

        def icon(self) -> str:
            """Return description for an enum object."""
            status_map = {
                self.ACTIVE: "<i class='fas fa-check'></i>",
                self.INACTIVE: "<i class='fas fa-user-slash'></i>",
                self.DEACTIVATED: "<i class='fas fa-user-clock'></i>",
                self.MISSING: "<i class='fas fa-question'></i> ",
            }
            return status_map.get(self, "")

    class Paid(models.TextChoices):
        PAID = "paid", _("Paid")
        UNPAID = "unpaid", _("Unpaid")

        def color(self) -> str:
            """Return bootstrap corresponding icon class."""
            paid_map = {
                self.PAID: "success",
                self.UNPAID: "danger",
            }
            return paid_map.get(self, "secondary")

    name = models.CharField(
        max_length=100,
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="+")

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        blank=True,
        default=Status.ACTIVE,
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
        return self.status == self.Status.ACTIVE

    @property
    def is_inactive(self) -> bool:
        return self.status == self.Status.INACTIVE

    @property
    def is_deactivated(self) -> bool:
        return self.status == self.Status.DEACTIVATED

    @property
    def is_missing(self) -> bool:
        return self.status == self.Status.MISSING

    @property
    def has_paid(self) -> bool:
        """Return True if user has paid."""
        if self.deposit >= self.owner.tax_amount:
            return True
        if self.last_paid and self.deposit >= 0:
            return timezone.now() - self.last_paid < timezone.timedelta(
                days=self.owner.tax_period
            )
        return False

    @property
    def deposit_html(self) -> str:
        if self.deposit < 0:
            # Make text red for negative deposits
            return f"<span class='text-danger'>{intcomma(self.deposit, use_l10n=True)}</span> ISK"
        if self.deposit > 0:
            return f"<span class='text-success'>{intcomma(self.deposit, use_l10n=True)}</span> ISK"
        return (
            f"{intcomma(self.deposit, use_l10n=True)} ISK" if self.deposit else "0 ISK"
        )

    def has_paid_icon(self, badge=False, text=False) -> str:
        """Return the HTML icon for has_paid."""
        color = "success" if self.has_paid else "danger"

        if self.has_paid:
            html = f"<i class='fas fa-check' title='{self.Paid('paid').label}' data-tooltip-toggle='taxsystem-tooltip'></i>"
        else:
            html = f"<i class='fas fa-times' title='{self.Paid('unpaid').label}' data-tooltip-toggle='taxsystem-tooltip'></i>"

        if text:
            html += f" {self.Paid('paid').label if self.has_paid else self.Paid('unpaid').label}"

        if badge:
            html = mark_safe(f"<span class='badge bg-{color}'>{html}</span>")
        return html


class PaymentsBase(models.Model):
    """Tax Payments model for app"""

    class Meta:
        abstract = True
        default_permissions = ()

    class RequestStatus(models.TextChoices):
        APPROVED = "approved", _("Approved")
        PENDING = "pending", _("Pending")
        REJECTED = "rejected", _("Rejected")
        NEEDS_APPROVAL = "needs_approval", _("Requires Auditor")

        def color(self) -> str:
            """Return bootstrap corresponding icon class."""
            status_map = {
                self.APPROVED: "success",
                self.PENDING: "warning",
                self.REJECTED: "danger",
                self.NEEDS_APPROVAL: "info",
            }
            return status_map.get(self, "secondary")

    name = models.CharField(max_length=100)

    entry_id = models.BigIntegerField()

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    date = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(null=True, blank=True)

    request_status = models.CharField(
        max_length=16,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
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
        return self.request_status == self.RequestStatus.PENDING

    @property
    def is_needs_approval(self) -> bool:
        return self.request_status == self.RequestStatus.NEEDS_APPROVAL

    @property
    def is_approved(self) -> bool:
        return self.request_status == self.RequestStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.request_status == self.RequestStatus.REJECTED

    @property
    def character_id(self) -> int:
        """Return the character ID of the user who made the payment or first OwnershipRecord."""
        try:
            character_id = self.account.user.profile.main_character.character_id
        except AttributeError:
            character = OwnershipRecord.objects.filter(user=self.account.user).first()
            character_id = character.character.character_id
        return character_id

    @property
    def division_name(self) -> "CorporationWalletJournalEntry":
        """Return the division name of the payment."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        journal = CorporationWalletJournalEntry.objects.filter(
            entry_id=self.entry_id
        ).first()
        if not journal:
            return "N/A"
        return journal.division.name

    def __str__(self):
        return (
            f"{self.account.name} - {self.date} - {self.amount} - {self.request_status}"
        )

    def get_request_status(self) -> str:
        return self.get_request_status_display()

    @property
    def formatted_payment_date(self) -> str:
        if self.date:
            return timezone.localtime(self.date).strftime("%Y-%m-%d %H:%M:%S")
        return _("No date")


class UpdateStatusBase(models.Model):
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


class FilterBase(models.Model):
    class Meta:
        abstract = True
        default_permissions = ()

    class FilterType(models.TextChoices):
        REASON = "reason", _("Reason")
        AMOUNT = "amount", _("Amount")

    filter_type = models.CharField(max_length=20, choices=FilterType.choices)
    value = models.CharField(max_length=255)

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


class FilterSetBase(models.Model):
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


class PaymentHistoryBase(models.Model):
    """Basemodel for Payments History"""

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

    def __str__(self):
        return f"{self.date}: {self.user} - {self.action} - {self.comment}"


class AdminHistoryBase(models.Model):
    """Logs Model for app"""

    class Actions(models.TextChoices):
        DEFAULT = "", ""
        ADD = "Added", _("Added")
        CHANGE = "Changed", _("Changed")
        DELETE = "Deleted", _("Deleted")

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

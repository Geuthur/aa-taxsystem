"""Models for Tax System."""

# Standard Library
from collections.abc import Callable
from typing import TYPE_CHECKING

# Third Party
from bravado.exception import HTTPInternalServerError

# Django
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import OwnershipRecord, User
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.models import Token

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, app_settings
from taxsystem.errors import HTTPGatewayTimeoutError, NotModifiedError
from taxsystem.managers.payment_manager import PaymentsManager, PaymentSystemManager
from taxsystem.managers.tax_manager import MembersManager, OwnerAuditManager
from taxsystem.models.general import UpdateSectionResult, _NeedsUpdate
from taxsystem.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.wallet import CorporationWalletJournalEntry


class OwnerAudit(models.Model):
    """Tax System Audit model for app"""

    class UpdateSection(models.TextChoices):
        WALLET = "wallet", _("Wallet Journal")
        DIVISION_NAMES = "division_names", _("Wallet Division Names")
        DIVISION = "division", _("Wallet Division")
        MEMBERS = "members", _("Members")
        PAYMENTS = "payments", _("Payments")
        PAYMENT_SYSTEM = "payment_system", _("Payment System")
        PAYDAY = "payday", _("Payday")

        @classmethod
        def get_sections(cls) -> list[str]:
            """Return list of section values."""
            return [choice.value for choice in cls]

        @property
        def method_name(self) -> str:
            """Return method name for this section."""
            return f"update_{self.value}"

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

    objects = OwnerAuditManager()

    name = models.CharField(
        max_length=255,
    )

    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="+"
    )

    alliance = models.ForeignKey(
        EveAllianceInfo,
        on_delete=models.CASCADE,
        related_name="alliance",
        blank=True,
        null=True,
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

    def __str__(self):
        return f"{self.corporation.corporation_name} - Status: {self.get_status}"

    def update_division_names(self, force_refresh: bool) -> None:
        """Update the divisions for this corporation."""
        return self.ts_corporation_division.update_or_create_esi_names(
            self, force_refresh=force_refresh
        )

    def update_division(self, force_refresh: bool) -> None:
        """Update the divisions for this corporation."""
        return self.ts_corporation_division.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_wallet(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the wallet journal for this corporation."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        return CorporationWalletJournalEntry.objects.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_members(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the members for this corporation."""
        return self.ts_members.update_or_create_esi(self, force_refresh=force_refresh)

    def update_payments(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the Payments for this corporation."""
        return Payments.objects.update_or_create_payments(
            self, force_refresh=force_refresh
        )

    def update_payment_system(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the Payment System for this corporation."""
        return self.ts_payment_system.update_or_create_payment_system(
            self, force_refresh=force_refresh
        )

    def update_payday(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the Payment System for this corporation."""
        return self.ts_payment_system.check_pay_day(self, force_refresh=force_refresh)

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            # General
            "esi-corporations.read_corporation_membership.v1",
            "esi-corporations.track_members.v1",
            "esi-characters.read_corporation_roles.v1",
            # wallets
            "esi-wallet.read_corporation_wallets.v1",
            "esi-corporations.read_divisions.v1",
        ]

    def get_token(self, scopes, req_roles) -> Token:
        """Get the token for this corporation."""
        if "esi-characters.read_corporation_roles.v1" not in scopes:
            scopes.append("esi-characters.read_corporation_roles.v1")

        char_ids = EveCharacter.objects.filter(
            corporation_id=self.corporation.corporation_id
        ).values("character_id")

        tokens = Token.objects.filter(character_id__in=char_ids).require_scopes(scopes)

        for token in tokens:
            try:
                roles = esi.client.Character.get_characters_character_id_roles(
                    character_id=token.character_id, token=token.valid_access_token()
                ).result()

                has_roles = False
                for role in roles.get("roles", []):
                    if role in req_roles:
                        has_roles = True

                if has_roles:
                    return token
            except TokenError as e:
                logger.error(
                    "Token ID: %s (%s)",
                    token.pk,
                    e,
                )
        return False

    @property
    def get_status(self) -> UpdateStatus:
        """Get the status of this character."""
        if self.active is False:
            return self.UpdateStatus.DISABLED

        qs = OwnerAudit.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return self.UpdateStatus(total_update_status)

    # pylint: disable=duplicate-code
    def calc_update_needed(self) -> _NeedsUpdate:
        """Calculate if an update is needed."""
        sections: models.QuerySet[OwnerUpdateStatus] = self.ts_update_status.all()
        needs_update = {}
        for section in sections:
            needs_update[section.section] = section.need_update()
        return _NeedsUpdate(section_map=needs_update)

    # pylint: disable=duplicate-code
    def reset_update_status(self, section: UpdateSection) -> "OwnerUpdateStatus":
        """Reset the status of a given update section and return it."""
        update_status_obj: OwnerUpdateStatus = self.ts_update_status.get_or_create(
            section=section,
        )[0]
        update_status_obj.reset()
        return update_status_obj

    # pylint: disable=duplicate-code
    def reset_has_token_error(self) -> None:
        """Reset the has_token_error flag for this corporation."""
        self.ts_update_status.filter(
            has_token_error=True,
        ).update(
            has_token_error=False,
        )

    # pylint: disable=duplicate-code
    def update_section_if_changed(
        self,
        section: UpdateSection,
        fetch_func: Callable,
        force_refresh: bool = False,
    ):
        """Update the status of a specific section if it has changed."""
        section = self.UpdateSection(section)
        try:
            data = fetch_func(owner=self, force_refresh=force_refresh)
            logger.debug("%s: Update has changed, section: %s", self, section.label)
        except HTTPInternalServerError as exc:
            logger.debug("%s: Update has an HTTP internal server error: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except NotModifiedError:
            logger.debug("%s: Update has not changed, section: %s", self, section.label)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPGatewayTimeoutError:
            logger.debug(
                "%s: Update has a gateway timeout error, section: %s",
                self,
                section.label,
            )
            return UpdateSectionResult(is_changed=False, is_updated=False)
        return UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            data=data,
        )

    # pylint: disable=duplicate-code
    def update_section_log(
        self,
        section: UpdateSection,
        is_success: bool,
        is_updated: bool = False,
        error_message: str = None,
    ) -> None:
        """Update the status of a specific section."""
        error_message = error_message if error_message else ""
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": False,
            "last_run_finished_at": timezone.now(),
        }
        obj: OwnerUpdateStatus = self.ts_update_status.update_or_create(
            section=section,
            defaults=defaults,
        )[0]
        if is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self, section.label, status)

    # pylint: disable=duplicate-code
    def perform_update_status(
        self, section: UpdateSection, method: Callable, *args, **kwargs
    ) -> UpdateSectionResult:
        """Perform update status."""
        try:
            result = method(*args, **kwargs)
        except Exception as exc:
            # TODO ADD DISCORD NOTIFICATION?
            error_message = f"{type(exc).__name__}: {str(exc)}"
            is_token_error = isinstance(exc, (TokenError))
            logger.error(
                "%s: %s: Error during update status: %s",
                self,
                section.label,
                error_message,
                exc_info=not is_token_error,  # do not log token errors
            )
            self.ts_update_status.update_or_create(
                section=section,
                defaults={
                    "is_success": False,
                    "error_message": error_message,
                    "has_token_error": is_token_error,
                    "last_update_at": timezone.now(),
                },
            )
            raise exc
        return result

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax System Audit")
        verbose_name_plural = _("Tax System Audits")


class Members(models.Model):
    """Tax System Member model for app"""

    class States(models.TextChoices):
        ACTIVE = "active", _("Active")
        MISSING = "missing", _("Missing")
        NOACCOUNT = "noaccount", _("Unregistered")
        IS_ALT = "is_alt", _("Is Alt")

    character_name = models.CharField(max_length=100, db_index=True)

    character_id = models.PositiveIntegerField(primary_key=True)

    owner = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="ts_members"
    )

    status = models.CharField(
        _("Status"), max_length=10, choices=States.choices, blank=True, default="active"
    )

    logon = models.DateTimeField(null=True, blank=True)

    logged_off = models.DateTimeField(null=True, blank=True)

    joined = models.DateTimeField(null=True, blank=True)

    notice = models.TextField(null=True, blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Member System")
        verbose_name_plural = _("Tax Member Systems")

    def __str__(self):
        return f"{self.character_name} - {self.character_id}"

    objects = MembersManager()

    @property
    def is_active(self) -> bool:
        return self.status == self.States.ACTIVE

    @property
    def is_missing(self) -> bool:
        return self.status == self.States.MISSING

    @property
    def is_noaccount(self) -> bool:
        return self.status == self.States.NOACCOUNT

    @property
    def is_alt(self) -> bool:
        return self.status == self.States.IS_ALT

    @property
    def is_faulty(self) -> bool:
        return self.status in [self.States.MISSING, self.States.NOACCOUNT]


class PaymentSystem(models.Model):
    """Tax Payment System model for app"""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        DEACTIVATED = "deactivated", _("Deactivated")
        MISSING = "missing", _("Missing")

        def html(self, text=False) -> str:
            """Return the badge name for the status."""
            if text:
                return mark_safe(
                    f"<span class='badge bg-{self.color()}' data-tooltip-toggle='taxsystem-tooltip'>{self.label}</span>"
                )
            return mark_safe(
                f"<span class='badge bg-{self.color()}' data-tooltip-toggle='taxsystem-tooltip'>{self.icons()}</span>"
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

        def icons(self) -> str:
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

    name = models.CharField(
        max_length=100,
    )

    owner = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="ts_payment_system"
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

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Payment System")
        verbose_name_plural = _("Tax Payment Systems")

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
        return {
            "display": html,
            "sort": _("Yes") if self.has_paid else _("No"),
            "raw": self.has_paid,
        }

    objects = PaymentSystemManager()


class Payments(models.Model):
    """Tax Payments model for app"""

    class RequestStatus(models.TextChoices):
        APPROVED = "approved", _("Approved")
        PENDING = "pending", _("Pending")
        REJECTED = "rejected", _("Rejected")
        NEEDS_APPROVAL = "needs_approval", _("Requires Auditor")

    name = models.CharField(max_length=100)

    entry_id = models.BigIntegerField()

    account = models.ForeignKey(
        PaymentSystem, on_delete=models.CASCADE, related_name="ts_payments"
    )

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

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Payments")
        verbose_name_plural = _("Tax Payments")

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
    def division(self) -> "CorporationWalletJournalEntry":
        """Return the division name of the payment."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        try:
            journal = CorporationWalletJournalEntry.objects.filter(
                division__corporation__corporation=self.account.owner.corporation
            ).first()
            return journal.division.name
        except CorporationWalletJournalEntry.DoesNotExist:
            return "N/A"

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

    objects = PaymentsManager()


class OwnerUpdateStatus(models.Model):
    """A Model to track the status of the last update."""

    owner = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="ts_update_status"
    )
    section = models.CharField(
        max_length=32, choices=OwnerAudit.UpdateSection.choices, db_index=True
    )
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

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.owner} - {self.section} - {self.is_success}"

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

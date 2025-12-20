"""Models for Tax System."""

# Django
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
)
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.managers.alliance_manager import (
    AlliancePaymentAccountManager,
    AlliancePaymentManager,
)
from taxsystem.managers.owner_manager import AllianceOwnerManager
from taxsystem.models.base import (
    FilterBaseModel,
    FilterSetBaseModel,
    HistoryBaseModel,
    PaymentAccountBaseModel,
    PaymentsBaseModel,
    UpdateStatusBaseModel,
)
from taxsystem.models.corporation import CorporationOwner
from taxsystem.models.general import UpdateSectionResult
from taxsystem.models.helpers.textchoices import (
    AdminActions,
    AllianceUpdateSection,
    PaymentRequestStatus,
    UpdateStatus,
)
from taxsystem.models.helpers.updater import UpdateManager
from taxsystem.models.wallet import CorporationWalletJournalEntry
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class AllianceUpdateStatus(UpdateStatusBaseModel):
    """Model representing the update status of an alliance owner in the tax system."""

    owner = models.ForeignKey(
        "AllianceOwner",
        on_delete=models.CASCADE,
        related_name="ts_alliance_update_status",
    )

    section = models.CharField(
        max_length=32, choices=AllianceUpdateSection.choices, db_index=True
    )

    class Meta:
        default_permissions = ()
        unique_together = [("owner", "section")]

    def __str__(self) -> str:
        return f"{self.owner.name} - {self.section}"


class AllianceOwner(models.Model):
    """Model representing an alliance owner in the tax system."""

    class Meta:
        default_permissions = ()

    objects: AllianceOwnerManager = AllianceOwnerManager()

    name = models.CharField(
        max_length=255,
    )

    eve_alliance = models.OneToOneField(
        EveAllianceInfo,
        on_delete=models.CASCADE,
        related_name="+",
    )

    corporation = models.ForeignKey(
        CorporationOwner,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=_("The corporation that owns this alliance tax system."),
    )

    active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this alliance owner is active."),
    )

    tax_amount = models.DecimalField(
        max_digits=16,
        decimal_places=0,
        help_text=_("Tax Amount in ISK that is set for the alliance. Max 16 Digits"),
        default=0,
        validators=[MaxValueValidator(9999999999999999)],
    )

    tax_period = models.PositiveIntegerField(
        help_text=_(
            "Tax Period in days for the alliance. Max 365 days. Default: 30 days"
        ),
        default=30,
        validators=[MaxValueValidator(365)],
    )

    def __str__(self) -> str:
        return f"{self.eve_alliance.alliance_name}"

    @property
    def eve_id(self) -> int:
        """Return the Eve Alliance ID."""
        return self.eve_alliance.alliance_id

    def update_payments(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the payments for this owner.
        Args:
            force_refresh: Force refresh
        Returns:
            UpdateSectionResult object for this section
        """
        return AlliancePayments.objects.update_or_create_payments(
            owner=self, force_refresh=force_refresh
        )

    def update_tax_accounts(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the tax accounts for this owner.
        Args:
            force_refresh: Force refresh
        Returns:
            UpdateSectionResult object for this section
        """
        return AlliancePaymentAccount.objects.update_or_create_tax_accounts(
            owner=self, force_refresh=force_refresh
        )

    def update_deadlines(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the tax deadlines for this owner.
        Args:
            force_refresh: Force refresh
        Returns:
            UpdateSectionResult object for this section
        """
        return AlliancePaymentAccount.objects.check_payment_deadlines(
            owner=self, force_refresh=force_refresh
        )

    @property
    def payment_model(self):
        """Return the Payment Model for this owner."""
        return AlliancePayments

    @property
    def payment_history_model(self):
        """Return the Payment History Model for this owner."""
        return AlliancePaymentHistory

    @property
    def admin_log_model(self):
        """Return the Admin History Model for this owner."""
        return AllianceAdminHistory

    @property
    def account_model(self):
        """Return the Tax Account Model for this owner."""
        return AlliancePaymentAccount

    @property
    def filterset_model(self):
        """Return the Filter Set Model for this owner."""
        return AllianceFilterSet

    @property
    def filter_model(self):
        """Return the Filter Model for this owner."""
        return AllianceFilter

    @property
    def update_manager(self):
        """Return the Update Manager helper for this owner."""
        return UpdateManager(
            owner=self,
            update_section=AllianceUpdateSection,
            update_status=AllianceUpdateStatus,
        )

    @property
    def get_status(self) -> UpdateStatus:
        """Get the update status of this owner.

        Returns:
            UpdateStatus enum value representing the current status
        """
        # pylint: disable=duplicate-code
        if self.active is False:
            return UpdateStatus.DISABLED

        # Use type(self) for dynamic QuerySet resolution
        qs = type(self).objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return UpdateStatus(total_update_status)

    @property
    def get_update_status(self) -> dict[str, str]:
        """Return a dictionary of update sections and their statuses."""
        update_status = {}
        for section in AllianceUpdateSection.get_sections():
            try:
                status = AllianceUpdateStatus.objects.get(owner=self, section=section)
                update_status[section] = {
                    "is_success": status.is_success,
                    "last_update_finished_at": status.last_update_finished_at,
                    "last_run_finished_at": status.last_run_finished_at,
                }
            except AllianceUpdateStatus.DoesNotExist:
                continue
        return update_status


class AlliancePaymentAccount(PaymentAccountBaseModel):
    """Model representing an alliance tax account in the tax system."""

    objects: AlliancePaymentAccountManager = AlliancePaymentAccountManager()

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        AllianceOwner,
        on_delete=models.CASCADE,
        related_name="ts_ally_tax_accounts",
    )


class AlliancePayments(PaymentsBaseModel):
    """Model representing payments made by alliance members in the tax system."""

    objects: AlliancePaymentManager = AlliancePaymentManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["account", "owner", "request_status", "-date"]),
            models.Index(fields=["request_status", "-date"]),
        ]

    account = models.ForeignKey(
        AlliancePaymentAccount,
        on_delete=models.CASCADE,
        related_name="+",
    )

    owner = models.ForeignKey(
        AllianceOwner,
        on_delete=models.CASCADE,
        related_name="ts_alliance_payments",
        help_text=_("Owner of this payment"),
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.account.name} - {self.amount} ISK"

    def transaction_log(
        self, user, comment, new_status, action=""
    ) -> "AlliancePaymentHistory":
        """Return a log entry for the transaction.

        Args:
            user: User performing the action
            comment: Additional message
            new_status: New status after the action
            action: Action performed (optional)
        Returns:
            AlliancePaymentHistory object
        """
        return AlliancePaymentHistory(
            user=user,
            payment=self,
            new_status=new_status,
            action=action,
            comment=comment,
        )


class AllianceFilterSet(FilterSetBaseModel):
    owner = models.ForeignKey(
        AllianceOwner,
        on_delete=models.CASCADE,
        related_name="ts_alliance_filter_set",
    )

    def filter(self, payments: AlliancePayments) -> models.QuerySet[AlliancePayments]:
        if self.is_active:
            for f in self.ts_alliance_filters.all():
                payments = f.apply_filter(payments)
            return payments
        return AlliancePayments.objects.none()

    def filter_contains(
        self, payments: AlliancePayments
    ) -> models.QuerySet[AlliancePayments]:  # not implemented yet
        if self.is_active:
            for f in self.ts_alliance_filters.all():
                payments = f.apply_contains(payments)
            return payments
        return AlliancePayments.objects.none()


class AllianceFilter(FilterBaseModel):
    filter_set = models.ForeignKey(
        AllianceFilterSet,
        on_delete=models.CASCADE,
        related_name="ts_alliance_filters",
    )

    def apply_filter(
        self, qs: models.QuerySet[CorporationWalletJournalEntry]
    ) -> models.QuerySet[CorporationWalletJournalEntry]:
        if self.filter_type == AllianceFilter.FilterType.REASON:
            return qs.filter(reason=self.value)
        if self.filter_type == AllianceFilter.FilterType.AMOUNT:
            return qs.filter(amount=self.value)
        # weitere Felder
        return qs

    def apply_contains(
        self, qs: models.QuerySet[CorporationWalletJournalEntry]
    ) -> models.QuerySet[CorporationWalletJournalEntry]:
        if self.filter_type == AllianceFilter.FilterType.REASON:
            return qs.filter(reason__icontains=self.value)
        if self.filter_type == AllianceFilter.FilterType.AMOUNT:
            return qs.filter(amount__gte=self.value)
        # weitere Felder
        return qs

    class Meta:
        default_permissions = ()


class AlliancePaymentHistory(HistoryBaseModel):
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


class AllianceAdminHistory(HistoryBaseModel):
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

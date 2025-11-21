"""Models for Tax System."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
)
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.managers.alliance_manager import (
    AllianceOwnerManager,
    AlliancePaymentAccountManager,
    AlliancePaymentManager,
)
from taxsystem.models.base import (
    AdminHistoryBase,
    FilterBase,
    FilterSetBase,
    OwnerBase,
    PaymentAccountBase,
    PaymentHistoryBase,
    PaymentsBase,
    UpdateStatusBase,
)
from taxsystem.models.corporation import CorporationOwner
from taxsystem.models.general import AllianceUpdateSection
from taxsystem.models.wallet import CorporationWalletJournalEntry

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class AllianceUpdateStatus(UpdateStatusBase):
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

    def __str__(self) -> str:
        return f"{self.owner.name} - {self.section}"


class AllianceOwner(OwnerBase):
    """Model representing an alliance owner in the tax system."""

    class Meta:
        default_permissions = ()

    objects: AllianceOwnerManager = AllianceOwnerManager()

    eve_alliance = models.OneToOneField(
        EveAllianceInfo,
        on_delete=models.CASCADE,
        related_name="+",
    )

    corporation = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="+",
        help_text=_("The corporation that owns this alliance tax system."),
    )

    def __str__(self) -> str:
        return f"{self.eve_alliance.alliance_name}"

    def update_payments(self, force_refresh: bool) -> AllianceUpdateStatus:
        """Update the Payments for this alliance."""
        return AlliancePayments.objects.update_or_create_payments(
            self, force_refresh=force_refresh
        )

    def update_payment_system(self, force_refresh: bool) -> AllianceUpdateStatus:
        """Update the Payment System for this alliance."""
        return self.ts_alliance_payment_accounts.update_or_create_payment_system(
            self, force_refresh=force_refresh
        )

    def update_payday(self, force_refresh: bool) -> AllianceUpdateStatus:
        """Update the Payment System for this alliance."""
        return self.ts_alliance_payment_accounts.check_pay_day(
            self, force_refresh=force_refresh
        )

    @property
    def eve_id(self) -> int:  # Is used for urls and templates
        """Return the Eve Corporation ID."""
        return self.eve_alliance.alliance_id

    @property
    def get_status(self) -> "OwnerBase.UpdateStatus":
        """Get the status of this character."""
        if self.active is False:
            return self.UpdateStatus.DISABLED

        qs = AllianceOwner.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return self.UpdateStatus(total_update_status)

    @property
    def update_status_manager(self) -> models.QuerySet[AllianceUpdateStatus]:
        """Return the related manager for alliance update status objects."""
        return AllianceUpdateStatus.objects.filter(owner=self)

    @property
    def update_section_enum(self):
        """Return the alliance update section enum class."""
        return AllianceUpdateSection

    @property
    def payments_class(self) -> type["AlliancePayments"]:
        """Return the payments class for this alliance owner."""
        return AlliancePayments

    @property
    def payments_account_class(self) -> type["AlliancePaymentAccount"]:
        """Return the payments account class for this alliance owner."""
        return AlliancePaymentAccount

    @property
    def payments_history_class(self) -> type["AlliancePaymentHistory"]:
        """Return the payments class for this alliance owner."""
        return AlliancePaymentHistory

    @property
    def admin_history_class(self) -> type["AllianceAdminHistory"]:
        """Return the admin history class for this alliance owner."""
        return AllianceAdminHistory

    @property
    def filterset_class(self) -> type["AllianceFilterSet"]:
        """Return the filter set class for this alliance owner."""
        return AllianceFilterSet

    @property
    def filter_class(self) -> type["AllianceFilter"]:
        """Return the filter class for this alliance owner."""
        return AllianceFilter


class AlliancePaymentAccount(PaymentAccountBase):
    """Model representing an alliance payment account in the tax system."""

    objects: AlliancePaymentAccountManager = AlliancePaymentAccountManager()

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        AllianceOwner,
        on_delete=models.CASCADE,
        related_name="ts_alliance_payment_accounts",
    )

    def __str__(self) -> str:
        return f"{self.name}"


class AlliancePayments(PaymentsBase):
    """Model representing payments made by alliance members in the tax system."""

    objects: AlliancePaymentManager = AlliancePaymentManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["account", "owner_id", "request_status", "-date"]),
            models.Index(fields=["request_status", "-date"]),
        ]

    account = models.ForeignKey(
        AlliancePaymentAccount,
        on_delete=models.CASCADE,
        related_name="ts_alliance_payments",
    )

    def __str__(self) -> str:
        return f"{self.account.name} - {self.amount} ISK"


class AllianceFilterSet(FilterSetBase):
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


class AllianceFilter(FilterBase):
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


class AlliancePaymentHistory(PaymentHistoryBase):
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
        max_length=16,
        choices=AlliancePayments.RequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )


class AllianceAdminHistory(AdminHistoryBase):
    """Model representing the history of administrative actions taken on alliance owners in the tax system."""

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        AllianceOwner,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Payment"),
        help_text=_("Payment that the action was performed on"),
    )

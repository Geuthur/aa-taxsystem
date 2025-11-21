"""Models for Tax System."""

# Standard Library
from typing import ClassVar

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.models import Token

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.managers.corporation_manager import (
    CorporationOwnerManager,
    MembersManager,
)
from taxsystem.managers.payment_manager import (
    CorporationAccountManager,
    PaymentsManager,
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
from taxsystem.models.general import CorporationUpdateSection
from taxsystem.models.wallet import CorporationWalletJournalEntry
from taxsystem.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationUpdateStatus(UpdateStatusBase):
    """Model representing the update status of a corporation owner in the tax system."""

    owner = models.ForeignKey(
        "CorporationOwner",
        on_delete=models.CASCADE,
        related_name="ts_corporation_update_status",
    )
    section = models.CharField(
        max_length=32, choices=CorporationUpdateSection.choices, db_index=True
    )

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.owner} - {self.section}"


class CorporationOwner(OwnerBase):
    """Model representing a corporation owner in the tax system."""

    class Meta:
        default_permissions = ()

    objects: ClassVar[CorporationOwnerManager] = CorporationOwnerManager()

    eve_corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="+"
    )

    def __str__(self):
        return f"{self.name}"

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
            corporation_id=self.eve_corporation.corporation_id
        ).values("character_id")

        tokens = Token.objects.filter(character_id__in=char_ids).require_scopes(scopes)

        for token in tokens:
            try:
                roles = esi.client.Character.GetCharactersCharacterIdRoles(
                    character_id=token.character_id, token=token
                ).result(force_refresh=True)

                has_roles = False
                for role in roles.roles:
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

    def update_wallet(self, force_refresh: bool) -> CorporationUpdateStatus:
        """Update the wallet journal for this corporation."""
        return CorporationWalletJournalEntry.objects.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_members(self, force_refresh: bool) -> CorporationUpdateStatus:
        """Update the members for this corporation."""
        return self.ts_members.update_or_create_esi(self, force_refresh=force_refresh)

    def update_payments(self, force_refresh: bool) -> CorporationUpdateStatus:
        """Update the Payments for this corporation."""
        return CorporationPayments.objects.update_or_create_payments(
            self, force_refresh=force_refresh
        )

    def update_payment_system(self, force_refresh: bool) -> CorporationUpdateStatus:
        """Update the Payment System for this corporation."""
        return self.ts_corporation_payment_accounts.update_or_create_payment_system(
            self, force_refresh=force_refresh
        )

    def update_payday(self, force_refresh: bool) -> CorporationUpdateStatus:
        """Update the Payment System for this corporation."""
        return self.ts_corporation_payment_accounts.check_pay_day(
            self, force_refresh=force_refresh
        )

    @property
    def eve_id(self) -> int:  # Is used for urls and templates
        """Return the Eve Corporation ID."""
        return self.eve_corporation.corporation_id

    @property
    def get_status(self) -> "OwnerBase.UpdateStatus":
        """Get the status of this character."""
        if self.active is False:
            return self.UpdateStatus.DISABLED

        qs = CorporationOwner.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return self.UpdateStatus(total_update_status)

    @property
    def update_status_manager(self) -> models.QuerySet[CorporationUpdateStatus]:
        """Return the related manager for corporation update status objects."""
        return CorporationUpdateStatus.objects.filter(owner=self)

    @property
    def update_section_enum(self):
        """Return the corporation update section enum class."""
        return CorporationUpdateSection

    @property
    def payments_class(self) -> type["CorporationPayments"]:
        """Return the payments class for this corporation owner."""
        return CorporationPayments

    @property
    def payments_account_class(self) -> type["CorporationPaymentAccount"]:
        """Return the payments account class for this corporation owner."""
        return CorporationPaymentAccount

    @property
    def payments_history_class(self) -> type["CorporationPaymentHistory"]:
        """Return the payments class for this corporation owner."""
        return CorporationPaymentHistory

    @property
    def filterset_class(self) -> type["CorporationFilterSet"]:
        """Return the filter set class for this corporation owner."""
        return CorporationFilterSet

    @property
    def filter_class(self) -> type["CorporationFilter"]:
        """Return the filter class for this corporation owner."""
        return CorporationFilter

    @property
    def admin_history_class(self) -> type["CorporationAdminHistory"]:
        """Return the admin history class for this corporation owner."""
        return CorporationAdminHistory


class Members(models.Model):
    """Tax System Member model for app"""

    class Meta:
        default_permissions = ()

    class States(models.TextChoices):
        ACTIVE = "active", _("Active")
        MISSING = "missing", _("Missing")
        NOACCOUNT = "noaccount", _("Unregistered")
        IS_ALT = "is_alt", _("Is Alt")

    character_name = models.CharField(max_length=100, db_index=True)

    character_id = models.PositiveIntegerField(primary_key=True)

    owner = models.ForeignKey(
        CorporationOwner, on_delete=models.CASCADE, related_name="ts_members"
    )

    status = models.CharField(
        _("Status"), max_length=10, choices=States.choices, blank=True, default="active"
    )

    logon = models.DateTimeField(null=True, blank=True)

    logged_off = models.DateTimeField(null=True, blank=True)

    joined = models.DateTimeField(null=True, blank=True)

    notice = models.TextField(null=True, blank=True)

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


class CorporationPaymentAccount(PaymentAccountBase):
    """Model representing a corporation payment account in the tax system."""

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="ts_corporation_payment_accounts",
    )

    objects = CorporationAccountManager()

    def __str__(self) -> str:
        return f"{self.name}"


class CorporationPayments(PaymentsBase):
    """Model representing payments made by corporation members in the tax system."""

    class Meta:
        default_permissions = ()

    account = models.ForeignKey(
        CorporationPaymentAccount,
        on_delete=models.CASCADE,
        related_name="ts_corporation_payments",
    )

    objects = PaymentsManager()

    def __str__(self) -> str:
        return f"{self.account.name} - {self.amount} ISK"


class CorporationFilterSet(FilterSetBase):
    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="ts_corporation_filter_set",
    )

    def filter(
        self, payments: CorporationPayments
    ) -> models.QuerySet[CorporationPayments]:
        if self.is_active:
            for f in self.ts_corporation_filters.all():
                payments = f.apply_filter(payments)
            return payments
        return CorporationPayments.objects.none()

    def filter_contains(
        self, payments: CorporationPayments
    ) -> models.QuerySet[CorporationPayments]:  # not implemented yet
        if self.is_active:
            for f in self.ts_corporation_filters.all():
                payments = f.apply_contains(payments)
            return payments
        return CorporationPayments.objects.none()


class CorporationFilter(FilterBase):
    class Meta:
        default_permissions = ()

    filter_set = models.ForeignKey(
        CorporationFilterSet,
        on_delete=models.CASCADE,
        related_name="ts_corporation_filters",
    )

    def apply_filter(
        self, qs: models.QuerySet[CorporationWalletJournalEntry]
    ) -> models.QuerySet[CorporationWalletJournalEntry]:
        if self.filter_type == CorporationFilter.FilterType.REASON:
            return qs.filter(reason=self.value)
        if self.filter_type == CorporationFilter.FilterType.AMOUNT:
            return qs.filter(amount=self.value)
        # weitere Felder
        return qs

    def apply_contains(
        self, qs: models.QuerySet[CorporationWalletJournalEntry]
    ) -> models.QuerySet[CorporationWalletJournalEntry]:
        if self.filter_type == CorporationFilter.FilterType.REASON:
            return qs.filter(reason__icontains=self.value)
        if self.filter_type == CorporationFilter.FilterType.AMOUNT:
            return qs.filter(amount__gte=self.value)
        # weitere Felder
        return qs


class CorporationPaymentHistory(PaymentHistoryBase):
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
        max_length=16,
        choices=CorporationPayments.RequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )


class CorporationAdminHistory(AdminHistoryBase):
    """Model representing the history of administrative actions taken on corporation owners in the tax system."""

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Payment"),
        help_text=_("Payment that the action was performed on"),
    )

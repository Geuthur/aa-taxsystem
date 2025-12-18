"""Models for Tax System."""

# Django
from django.core.validators import MaxValueValidator
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
    CorporationAccountManager,
    MembersManager,
    PaymentsManager,
)
from taxsystem.managers.owner_manager import (
    CorporationOwnerManager,
)
from taxsystem.models.base import (
    FilterBaseModel,
    FilterSetBaseModel,
    HistoryBaseModel,
    PaymentAccountBaseModel,
    PaymentsBaseModel,
    UpdateStatusBaseModel,
)
from taxsystem.models.general import (
    UpdateSectionResult,
)
from taxsystem.models.helpers.textchoices import (
    AdminActions,
    CorporationUpdateSection,
    PaymentRequestStatus,
    UpdateStatus,
)
from taxsystem.models.helpers.updater import UpdateManager
from taxsystem.models.wallet import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)
from taxsystem.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationUpdateStatus(UpdateStatusBaseModel):
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
        unique_together = [("owner", "section")]

    def __str__(self) -> str:
        return f"{self.owner} - {self.section}"


class CorporationOwner(models.Model):
    """Model representing a corporation owner in the tax system."""

    class Meta:
        default_permissions = ()

    objects: CorporationOwnerManager = CorporationOwnerManager()

    name = models.CharField(
        max_length=255,
    )

    eve_corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="+"
    )

    active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this corporation owner is active."),
    )

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
        return f"{self.name}"

    @property
    def payment_model(self):
        """Return the Payment Model for this owner."""
        return CorporationPayments

    @property
    def payment_history_model(self):
        """Return the Payment History Model for this owner."""
        return CorporationPaymentHistory

    @property
    def admin_log_model(self):
        """Return the Admin History Model for this owner."""
        return CorporationAdminHistory

    @property
    def account_model(self):
        """Return the Tax Account Model for this owner."""
        return CorporationPaymentAccount

    @property
    def filterset_model(self):
        """Return the Filter Set Model for this owner."""
        return CorporationFilterSet

    @property
    def filter_model(self):
        """Return the Filter Model for this owner."""
        return CorporationFilter

    @property
    def update_manager(self):
        """Return the Update Manager helper for this owner."""
        return UpdateManager(
            owner=self,
            update_section=CorporationUpdateSection,
            update_status=CorporationUpdateStatus,
        )

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

    def update_division_names(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the divisions for this corporation."""
        return CorporationWalletDivision.objects.update_or_create_esi_names(
            owner=self, force_refresh=force_refresh
        )

    def update_divisions(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the divisions for this corporation."""
        return CorporationWalletDivision.objects.update_or_create_esi(
            owner=self, force_refresh=force_refresh
        )

    def update_wallet(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the wallet journals for this corporation."""
        return CorporationWalletJournalEntry.objects.update_or_create_esi(
            owner=self, force_refresh=force_refresh
        )

    def update_members(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the members for this corporation.
        Args:
            force_refresh: Force refresh from ESI even if not modified
        Returns:
            UpdateSectionResult object for this section
        """
        return Members.objects.update_or_create_esi(self, force_refresh=force_refresh)

    def update_payments(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the payments for this owner.
        Args:
            force_refresh: Force refresh
        Returns:
            UpdateSectionResult object for this section
        """
        return CorporationPayments.objects.update_or_create_payments(
            owner=self, force_refresh=force_refresh
        )

    def update_tax_accounts(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the tax accounts for this owner.
        Args:
            force_refresh: Force refresh
        Returns:
            UpdateSectionResult object for this section
        """
        return CorporationPaymentAccount.objects.update_or_create_tax_accounts(
            owner=self, force_refresh=force_refresh
        )

    def update_deadlines(self, force_refresh: bool) -> UpdateSectionResult:
        """Update the tax deadlines for this owner.
        Args:
            force_refresh: Force refresh
        Returns:
            UpdateSectionResult object for this section
        """
        return CorporationPaymentAccount.objects.check_payment_deadlines(
            owner=self, force_refresh=force_refresh
        )

    # Abstract properties implementation
    @property
    def eve_id(self) -> int:
        """Return the Eve Corporation ID."""
        return self.eve_corporation.corporation_id

    @property
    def get_status(self) -> UpdateStatus:
        """Get the update status of this owner.

        Returns:
            UpdateStatus enum value representing the current status
        """
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
        for section in CorporationUpdateSection.get_sections():
            try:
                status = CorporationUpdateStatus.objects.get(
                    owner=self, section=section
                )
                update_status[section] = {
                    "is_success": status.is_success,
                    "last_update_finished_at": status.last_update_finished_at,
                    "last_run_finished_at": status.last_run_finished_at,
                }
            except CorporationUpdateStatus.DoesNotExist:
                continue
        return update_status


class Members(models.Model):
    """Tax System Member model for app"""

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["owner", "character_name"]),
            models.Index(fields=["status"]),
        ]

    objects: MembersManager = MembersManager()

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


class CorporationPaymentAccount(PaymentAccountBaseModel):
    """Model representing a corporation tax account in the tax system."""

    objects: CorporationAccountManager = CorporationAccountManager()

    class Meta:
        default_permissions = ()

    owner = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="ts_corp_tax_accounts",
    )


class CorporationPayments(PaymentsBaseModel):
    """Model representing payments made by corporation members in the tax system."""

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(
                fields=["account", "owner_id", "request_status", "-date"],
            ),
            models.Index(fields=["request_status", "-date"]),
        ]

    objects: PaymentsManager = PaymentsManager()

    account = models.ForeignKey(
        CorporationPaymentAccount,
        on_delete=models.CASCADE,
        related_name="ts_corporation_payments",
    )

    def __str__(self) -> str:
        return f"{self.account.name} - {self.amount} ISK"

    # pylint: disable=duplicate-code
    def transaction_log(
        self, user, comment, new_status, action=""
    ) -> "CorporationPaymentHistory":
        """Return a log entry for the transaction.

        Args:
            user: User performing the action
            comment: Additional message
            new_status: New status after the action
            action: Action performed (optional)
        Returns:
            CorporationPaymentHistory object
        """
        return CorporationPaymentHistory(
            user=user,
            payment=self,
            new_status=new_status,
            action=action,
            comment=comment,
        )


class CorporationFilterSet(FilterSetBaseModel):
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

    def __str__(self) -> str:
        return f"Filter Set: {self.name}"


class CorporationFilter(FilterBaseModel):
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

    def __str__(self) -> str:
        return f"Filter: {self.filter_type} = {self.value}"


class CorporationPaymentHistory(HistoryBaseModel):
    """Model representing the history of actions taken on corporation payments in the tax system."""

    class Meta:
        default_permissions = ()

    # pylint: disable=duplicate-code
    payment = models.ForeignKey(
        CorporationPayments,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Payment"),
        help_text=_("Payment that the action was performed on"),
    )

    # pylint: disable=duplicate-code
    new_status = models.CharField(
        max_length=20,
        choices=PaymentRequestStatus.choices,
        verbose_name=_("New Status"),
        help_text=_("New Status of the action"),
    )


class CorporationAdminHistory(HistoryBaseModel):
    """
    Model representing the history of administrative actions taken on owners in the tax system.
    """

    class Meta:
        default_permissions = ()

    # pylint: disable=duplicate-code
    owner = models.ForeignKey(
        CorporationOwner,
        verbose_name=_("Owner"),
        help_text=_("Owner that the action was performed on"),
        on_delete=models.CASCADE,
        related_name="ts_admin_history",
    )

    # pylint: disable=duplicate-code
    action = models.CharField(
        max_length=20,
        choices=AdminActions.choices,
        default=AdminActions.DEFAULT,
        verbose_name=_("Action"),
        help_text=_("Action performed"),
    )

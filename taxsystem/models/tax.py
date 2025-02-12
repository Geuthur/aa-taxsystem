"""Models for Tax System."""

# Django
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from taxsystem.managers.payment_manager import PaymentsManager, PaymentSystemManager
from taxsystem.managers.tax_manager import MembersManager, OwnerAuditManager


class OwnerAudit(models.Model):
    """Tax System Audit model for app"""

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

    active = models.BooleanField(default=False)

    last_update_wallet = models.DateTimeField(null=True, blank=True)

    last_update_members = models.DateTimeField(null=True, blank=True)

    last_update_payments = models.DateTimeField(null=True, blank=True)

    last_update_payment_system = models.DateTimeField(null=True, blank=True)

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
        return f"{self.corporation.corporation_name} - Audit Data"

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

    def logs(self) -> models.QuerySet:
        """Return all logs for this corporation."""
        # pylint: disable=import-outside-toplevel
        from taxsystem.models.logs import Logs

        return Logs.objects.filter(corporation=self)

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

    corporation = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="owner"
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

    class States(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        DEACTIVATED = "deactivated", _("Deactivated")

    name = models.CharField(
        max_length=100,
    )

    corporation = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="+"
    )

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="+")

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(
        _("Status"), max_length=16, choices=States.choices, blank=True, default=""
    )

    payment_pool = models.DecimalField(
        max_digits=16,
        decimal_places=0,
        default=0,
        help_text=_(
            "Payment Pool in ISK that is set for the corporation. Max 16 Digits"
        ),
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
            self.user.user.character_ownerships.all().values_list(
                "character__character_id", flat=True
            )
        )

    @property
    def is_active(self) -> bool:
        return self.status == self.States.ACTIVE

    @property
    def is_inactive(self) -> bool:
        return self.status == self.States.INACTIVE

    @property
    def is_deactivated(self) -> bool:
        return self.status == self.States.DEACTIVATED

    @property
    def has_paid(self) -> bool:
        """Return True if user has paid the set amount or if last_paid is within the tax period."""
        if self.payment_pool >= self.corporation.tax_amount:
            return True
        if self.last_paid and self.payment_pool == 0:
            return timezone.now() - self.last_paid < timezone.timedelta(
                days=self.corporation.tax_period
            )
        return False

    objects = PaymentSystemManager()


class Payments(models.Model):
    """Tax Payments model for app"""

    class States(models.TextChoices):
        PAID = "paid", _("Paid")
        PENDING = "pending", _("Pending")
        FAILED = "failed", _("Failed")
        NEEDS_APPROVAL = "needs_approval", _("Needs Approval")

    class Approval(models.TextChoices):
        APPROVED = "approved", _("Approved")
        PENDING = "pending", _("Pending")
        REJECTED = "rejected", _("Rejected")

    class Systems(models.TextChoices):
        AUTOMATIC = "automatic", _("System")

    name = models.CharField(max_length=100)

    entry_id = models.BigIntegerField()

    payment_user = models.ForeignKey(
        PaymentSystem, on_delete=models.CASCADE, related_name="payment_user"
    )

    date = models.DateTimeField(default=timezone.now, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    payment_status = models.CharField(
        _("Status"), max_length=16, choices=States.choices, blank=True, default=""
    )

    payment_date = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(null=True, blank=True)

    approved = models.CharField(
        _("Pending"), max_length=16, choices=Approval.choices, blank=True, default=""
    )

    system = models.CharField(
        _("System"),
        max_length=16,
        choices=Systems.choices,
        blank=True,
        default="",
        help_text=_("System that processed the payment"),
    )

    approver_text = models.TextField(
        null=True, blank=True, help_text=_("Reason for approval or rejection")
    )

    notified = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Payments")
        verbose_name_plural = _("Tax Payments")

    @property
    def is_human(self) -> bool:
        return self.system == self.Systems.MANUAL

    @property
    def is_automatic(self) -> bool:
        return self.system == self.Systems.AUTOMATIC

    @property
    def is_paid(self) -> bool:
        return self.payment_status == self.States.PAID

    @property
    def is_pending(self) -> bool:
        return self.payment_status == self.States.PENDING

    @property
    def is_failed(self) -> bool:
        return self.payment_status == self.States.FAILED

    @property
    def is_needs_approval(self) -> bool:
        return self.payment_status == self.States.NEEDS_APPROVAL

    @property
    def is_approved(self) -> bool:
        return self.approved == self.Approval.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.approved == self.Approval.REJECTED

    def __str__(self):
        return f"{self.payment_user.name} - {self.date} - {self.amount} - {self.payment_status}"

    def get_payment_status(self) -> str:
        return self.get_payment_status_display()

    def get_approval_status(self) -> str:
        return self.get_approved_display()

    def formatted_payment_date(self) -> str:
        if self.payment_date:
            return timezone.localtime(self.payment_date).strftime("%Y-%m-%d %H:%M:%S")
        return _("No payment date")

    objects = PaymentsManager()

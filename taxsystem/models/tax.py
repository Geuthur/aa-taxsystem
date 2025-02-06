"""Models for Tax System."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from taxsystem.managers.payment_manager import PaymentManager
from taxsystem.managers.tax_manager import OwnerAuditManager, TaxSystemManager


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

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax System Audit")
        verbose_name_plural = _("Tax System Audits")


class Members(models.Model):
    """Tax System Member model for app"""

    class States(models.TextChoices):
        ACTIVE = "active", _("Active")
        MISSING = "missing", _("Missing")

    character_name = models.CharField(max_length=100, db_index=True)

    character_id = models.PositiveIntegerField(primary_key=True)

    audit = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="owner"
    )

    status = models.CharField(
        _("Status"), max_length=10, choices=States.choices, blank=True, default="active"
    )

    notice = models.TextField(null=True, blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Member System")
        verbose_name_plural = _("Tax Member Systems")

    def __str__(self):
        return f"{self.member.character_name} - {self.member.character_id}"

    objects = TaxSystemManager()


class PaymentSystem(models.Model):
    """Tax Payment System model for app"""

    class States(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    name = models.CharField(
        max_length=100,
    )

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="+")

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(
        _("Status"), max_length=10, choices=States.choices, blank=True, default=""
    )

    notice = models.TextField(null=True, blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Payment System")
        verbose_name_plural = _("Tax Payment Systems")

    def __str__(self):
        return f"{self.name} - {self.date} - {self.status}"

    objects = PaymentManager()


class Payments(models.Model):
    """Tax Payments model for app"""

    class States(models.TextChoices):
        PAID = "paid", _("Paid")
        PENDING = "pending", _("Pending")
        FAILED = "failed", _("Failed")

    name = models.CharField(
        max_length=100,
    )

    context_id = models.AutoField(primary_key=True)

    payment_user = models.ForeignKey(
        PaymentSystem, on_delete=models.CASCADE, related_name="payment_user"
    )

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    payment_status = models.CharField(
        _("Status"), max_length=10, choices=States.choices, blank=True, default=""
    )

    payment_date = models.DateTimeField(null=True, blank=True)

    approved = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Payments")
        verbose_name_plural = _("Tax Payments")

    def __str__(self):
        return f"{self.payment_user.name} - {self.date} - {self.amount} - {self.payment_status}"

    objects = PaymentManager()

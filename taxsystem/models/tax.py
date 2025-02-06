"""Models for Tax System."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from taxsystem.managers.tax_manager import OwnerAuditManager, TaxSystemManager


class OwnerAudit(models.Model):
    """Tax System Audit model for app"""

    objects = OwnerAuditManager()

    name = models.CharField(
        max_length=100,
    )

    corporation = models.OneToOneField(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="corporation"
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

    name = models.CharField(
        max_length=100,
    )

    audit = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="audit"
    )

    member = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="member",
    )

    status = models.CharField(max_length=50, null=True, blank=True)

    active = models.BooleanField(default=False)
    payment_notification = models.BooleanField(default=False)

    notice = models.TextField(null=True, blank=True)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Member System")
        verbose_name_plural = _("Tax Member Systems")

    def __str__(self):
        return f"{self.member.main_character.character_name} - {self.member.main_character.character_id}"

    objects = TaxSystemManager()


class Payments(models.Model):
    """Tax Payments model for app"""

    name = models.CharField(
        max_length=100,
    )

    payment_member = models.ForeignKey(
        Members, on_delete=models.CASCADE, related_name="member_payment"
    )

    context_id = models.AutoField(primary_key=True)

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    payment_status = models.CharField(max_length=50, null=True, blank=True)

    payment_date = models.DateTimeField(null=True, blank=True)

    approved = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        verbose_name = _("Tax Payments")
        verbose_name_plural = _("Tax Payments")

    def __str__(self):
        return f"{self.payment_member.member.main_character.character_name} - {self.date} - {self.amount}"

    objects = TaxSystemManager()

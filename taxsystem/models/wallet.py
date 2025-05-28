"""Corporation Wallet Model"""

# Django
from django.db import models

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem import __title__
from taxsystem.managers.wallet_manager import (
    CorporationDivisionManager,
    CorporationWalletManager,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class WalletJournalEntry(models.Model):
    amount = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )
    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )
    context_id = models.BigIntegerField(null=True, default=None)

    class ContextType(models.TextChoices):
        STRUCTURE_ID = "structure_id"
        STATION_ID = "station_id"
        MARKET_TRANSACTION_ID = "market_transaction_id"
        CHARACTER_ID = "character_id"
        CORPORATION_ID = "corporation_id"
        ALLIANCE_ID = "alliance_id"
        EVE_SYSTEM = "eve_system"
        INDUSTRY_JOB_ID = "industry_job_id"
        CONTRACT_ID = "contract_id"
        PLANET_ID = "planet_id"
        SYSTEM_ID = "system_id"
        TYPE_ID = "type_id"

    context_id_type = models.CharField(
        max_length=30, choices=ContextType.choices, null=True, default=None
    )
    date = models.DateTimeField()
    description = models.CharField(max_length=500)
    first_party = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="+",
    )
    entry_id = models.BigIntegerField()
    reason = models.CharField(max_length=500, null=True, default=None)
    ref_type = models.CharField(max_length=72)
    second_party = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="+",
    )
    tax = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=None)
    tax_receiver_id = models.IntegerField(null=True, default=None)

    class Meta:
        abstract = True
        indexes = (
            models.Index(fields=["date"]),
            models.Index(fields=["amount"]),
            models.Index(fields=["entry_id"]),
            models.Index(fields=["ref_type"]),
            models.Index(fields=["first_party"]),
            models.Index(fields=["second_party"]),
        )
        default_permissions = ()


class CorporationWalletDivision(models.Model):
    name = models.CharField(max_length=100, null=True, default=None)
    corporation = models.ForeignKey(
        "OwnerAudit",
        on_delete=models.CASCADE,
        related_name="ts_corporation_division",
    )
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    division_id = models.IntegerField()

    objects = CorporationDivisionManager()

    class Meta:
        default_permissions = ()


class CorporationWalletJournalEntry(WalletJournalEntry):
    division = models.ForeignKey(
        CorporationWalletDivision,
        on_delete=models.CASCADE,
        related_name="ts_corporation_wallet",
    )

    objects = CorporationWalletManager()

    def __str__(self):
        return f"Corporation Wallet Journal: {self.first_party.name} '{self.ref_type}' {self.second_party.name}: {self.amount} isk"

    @classmethod
    def get_visible(cls, user):
        """Get visible objects for the user"""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.tax import OwnerAudit

        corps_vis = OwnerAudit.objects.visible_to(user)
        return cls.objects.filter(division__corporation__in=corps_vis)

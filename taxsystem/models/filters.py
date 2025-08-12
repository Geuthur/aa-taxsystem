"""Models for Filters."""

# Django

# Django
from django.db import models
from django.db.models import QuerySet
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.models.tax import OwnerAudit, Payments
from taxsystem.models.wallet import CorporationWalletJournalEntry


class JournalFilterSet(models.Model):
    owner = models.ForeignKey(
        OwnerAudit, on_delete=models.CASCADE, related_name="ts_filter_set"
    )
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

    def filter(self, payments: Payments) -> models.QuerySet[Payments]:
        if self.is_active:
            for f in self.ts_filters.all():
                payments = f.apply_filter(payments)
            return payments
        return Payments.objects.none()

    def filter_contains(
        self, payments: Payments
    ) -> models.QuerySet[Payments]:  # not implemented yet
        if self.is_active:
            for f in self.ts_filters.all():
                payments = f.apply_contains(payments)
            return payments
        return Payments.objects.none()

    class Meta:
        verbose_name = _("Journal Filter Set")
        verbose_name_plural = _("Journal Filter Sets")
        default_permissions = ()


class JournalFilter(models.Model):
    class FilterType(models.TextChoices):
        REASON = "reason", _("Reason")
        AMOUNT = "amount", _("Amount")

    filter_set = models.ForeignKey(
        JournalFilterSet, on_delete=models.CASCADE, related_name="ts_filters"
    )
    filter_type = models.CharField(max_length=20, choices=FilterType.choices)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.filter_type}: {self.value}"

    def apply_filter(
        self, qs: QuerySet[CorporationWalletJournalEntry]
    ) -> QuerySet[CorporationWalletJournalEntry]:
        if self.filter_type == JournalFilter.FilterType.REASON:
            return qs.filter(reason=self.value)
        if self.filter_type == JournalFilter.FilterType.AMOUNT:
            return qs.filter(amount=self.value)
        # weitere Felder
        return qs

    def apply_contains(
        self, qs: QuerySet[CorporationWalletJournalEntry]
    ) -> QuerySet[CorporationWalletJournalEntry]:
        if self.filter_type == JournalFilter.FilterType.REASON:
            return qs.filter(reason__icontains=self.value)
        if self.filter_type == JournalFilter.FilterType.AMOUNT:
            return qs.filter(amount__gte=self.value)
        # weitere Felder
        return qs

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["filter_set", "value"], name="unique_filter_value_per_set"
            )
        ]
        default_permissions = ()

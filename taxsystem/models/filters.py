"""Models for Filters."""

# Django
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from taxsystem.models.tax import OwnerAudit, Payments


class SmartFilter(models.Model):
    """Model to hold a filter and its settings"""

    class Meta:
        verbose_name = _("Smart Filter Binding")
        verbose_name_plural = _("Smart Filters Catalog")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    filter_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        try:
            return f"{self.filter_object.name}: {self.filter_object.description}"
        # pylint: disable=broad-exception-caught
        except Exception:
            return f"Error: {self.content_type.app_label}:{self.content_type} {self.object_id} Not Found"


class FilterBase(models.Model):
    """Base Filter Model"""

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name}: {self.description}"

    def filter(self, payments: Payments):
        raise NotImplementedError("Please Create a filter!")


class FilterAmount(FilterBase):
    """Filter for Amount"""

    class Meta:
        verbose_name = _("Filter Amount")
        verbose_name_plural = _("Filter Amounts")

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    def filter(self, payments: Payments):
        return payments.filter(amount__gte=self.amount)


class FilterReason(FilterBase):
    """Filter for Reason"""

    class Meta:
        verbose_name = _("Filter Reason")
        verbose_name_plural = _("Filter Reasons")

    reason = models.CharField(max_length=255)

    def filter(self, payments: Payments):
        return payments.filter(reason__contains=self.reason)


class SmartGroup(models.Model):
    """Model to hold a group of filters"""

    corporation = models.OneToOneField(
        OwnerAudit, on_delete=models.CASCADE, related_name="filter_sets"
    )
    description = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    filters = models.ManyToManyField(SmartFilter)
    last_update = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(default=True)

    def apply_filters(self, payments: Payments):
        if self.enabled is True:
            for smart_filter in self.filters.all():
                payments = smart_filter.filter_object.filter(payments)
        return payments

    def display_filters(self):
        return ", ".join([str(f) for f in self.filters.all()])

    display_filters.short_description = "Filters"

    def __str__(self):
        return f"{self.name}: {self.description}"

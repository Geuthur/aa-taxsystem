"""Models for Filters."""

# Django

# Django
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.models.tax import OwnerAudit, Payments


class SmartFilter(models.Model):
    """Model to hold a filter and its settings"""

    class Meta:
        default_permissions = ()
        verbose_name = _("Smart Filter Binding")
        verbose_name_plural = _("Smart Filters Catalog")

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
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
        default_permissions = ()
        abstract = True

    def __str__(self):
        return f"{self.name}: {self.description}"

    def filter(self):
        raise NotImplementedError("Please Create a filter!")

    def filter_containts(self):
        raise NotImplementedError("Please Create a contains filter!")


class FilterAmount(FilterBase):
    """Filter for Amount"""

    class Meta:
        default_permissions = ()
        verbose_name = _("Filter Amount")
        verbose_name_plural = _("Filter Amounts")

    amount = models.DecimalField(max_digits=12, decimal_places=0)

    def filter(self):
        return {"amount": self.amount}

    def filter_containts(self):
        return {"amount__gte": self.amount}


class FilterReason(FilterBase):
    """Filter for Reason"""

    class Meta:
        default_permissions = ()
        verbose_name = _("Filter Reason")
        verbose_name_plural = _("Filter Reasons")

    reason = models.CharField(max_length=255)

    def filter(self):
        return {"reason": self.reason}

    def filter_containts(self):
        return {"reason__contains": self.reason}


class FilterDate(FilterBase):
    """Filter for Date"""

    class Meta:
        default_permissions = ()
        verbose_name = _("Filter Date")
        verbose_name_plural = _("Filter Dates")

    date = models.DateTimeField()

    def filter(self):
        return {"date": self.date}

    def filter_containts(self):
        return {"date__gte": self.date}


class SmartGroup(models.Model):
    """Model to hold a group of filters"""

    class Meta:
        default_permissions = ()

    owner = models.OneToOneField(
        OwnerAudit, on_delete=models.CASCADE, related_name="ts_filter_sets"
    )
    description = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    filters = models.ManyToManyField(SmartFilter)
    last_update = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(default=True)

    def filter(self, payments: Payments) -> models.QuerySet[Payments]:
        if self.enabled is True:
            q_objects = Q()
            for smart_filter in self.filters.all():
                q_objects &= Q(**smart_filter.filter_object.filter())
            payments = payments.filter(q_objects)
        return payments

    def filter_containts(self, payments: Payments) -> models.QuerySet[Payments]:
        if self.enabled is True:
            q_objects = Q()
            for smart_filter in self.filters.all():
                q_objects |= Q(**smart_filter.filter_object.filter_containts())
            payments = payments.filter(q_objects)
        return payments

    def display_filters(self):
        return ", ".join([str(f) for f in self.filters.all()])

    display_filters.short_description = "Filters"

    def __str__(self):
        return f"{self.name}: {self.description}"

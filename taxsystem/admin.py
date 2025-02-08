"""Admin models"""

from django.contrib import admin

from taxsystem.models.filters import FilterAmount, FilterReason, SmartFilter, SmartGroup


@admin.register(FilterAmount)
class FilterAmountAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "amount")


@admin.register(FilterReason)
class FilterReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "reason")


@admin.register(SmartFilter)
class SmartfilterAdmin(admin.ModelAdmin):
    def has_add_permission(self):
        return False

    list_display = ["__str__"]


@admin.register(SmartGroup)
class SmartGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ["filters"]
    list_display = [
        "__str__",
        "enabled",
        "display_filters",
        "last_update",
        "corporation",
    ]

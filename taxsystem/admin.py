"""Admin models"""

# Django
from django.contrib import admin
from django.utils.html import format_html

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# AA TaxSystem
from taxsystem.models.filters import FilterAmount, FilterReason, SmartFilter, SmartGroup
from taxsystem.models.tax import OwnerAudit


@admin.register(OwnerAudit)
class OwnerAuditAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_corporation__corporation_id",
        "_corporation__corporation_name",
    )

    list_display_links = (
        "_entity_pic",
        "_corporation__corporation_id",
        "_corporation__corporation_name",
    )

    list_select_related = ("corporation",)

    ordering = ["corporation__corporation_name"]

    search_fields = ["corporation__corporation_name", "corporation__corporation_id"]

    actions = [
        "delete_objects",
    ]

    @admin.display(description="")
    def _entity_pic(self, obj: OwnerAudit):
        eve_id = obj.corporation.corporation_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("corporation", eve_id, 32),
        )

    @admin.display(description="Corporation ID", ordering="corporation__corporation_id")
    def _corporation__corporation_id(self, obj: OwnerAudit):
        return obj.corporation.corporation_id

    @admin.display(
        description="Corporation Name", ordering="corporation__corporation_name"
    )
    def _corporation__corporation_name(self, obj: OwnerAudit):
        return obj.corporation.corporation_name

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FilterAmount)
class FilterAmountAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "amount")


@admin.register(FilterReason)
class FilterReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "reason")


@admin.register(SmartFilter)
class SmartfilterAdmin(admin.ModelAdmin):
    # pylint: disable=unused-argument
    def has_add_permission(self, request, obj=None):
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
        "owner",
    ]

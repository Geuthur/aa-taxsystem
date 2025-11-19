"""Admin models"""

# Django
from django.contrib import admin
from django.utils.html import format_html

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# AA TaxSystem
from taxsystem.models.corporation import CorporationOwner


@admin.register(CorporationOwner)
class CorporationOwnerAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_eve_corporation__corporation_id",
        "_eve_corporation__corporation_name",
    )

    list_display_links = (
        "_entity_pic",
        "_eve_corporation__corporation_id",
        "_eve_corporation__corporation_name",
    )

    list_select_related = ("corporation",)

    ordering = ["eve_corporation__corporation_name"]

    search_fields = [
        "eve_corporation__corporation_name",
        "eve_corporation__corporation_id",
    ]

    actions = [
        "delete_objects",
    ]

    @admin.display(description="")
    def _entity_pic(self, obj: CorporationOwner):
        eve_id = obj.eve_corporation.corporation_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("corporation", eve_id, 32),
        )

    @admin.display(
        description="Corporation ID", ordering="eve_corporation__corporation_id"
    )
    def _eve_corporation__corporation_id(self, obj: CorporationOwner):
        return obj.eve_corporation.corporation_id

    @admin.display(
        description="Corporation Name", ordering="eve_corporation__corporation_name"
    )
    def _eve_corporation__corporation_name(self, obj: CorporationOwner):
        return obj.eve_corporation.corporation_name

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False

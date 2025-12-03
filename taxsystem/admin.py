"""Admin models"""

# Django
from django.contrib import admin, messages
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Max, Q
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tasks import update_alliance, update_corporation


@admin.register(CorporationOwner)
class CorporationOwnerAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_eve_corporation__corporation_id",
        "_eve_corporation__corporation_name",
        "_last_update_at",
    )

    list_display_links = (
        "_entity_pic",
        "_eve_corporation__corporation_id",
        "_eve_corporation__corporation_name",
    )

    list_select_related = ("eve_corporation",)

    ordering = ["eve_corporation__corporation_name"]

    search_fields = [
        "eve_corporation__corporation_name",
        "eve_corporation__corporation_id",
    ]

    actions = [
        "delete_objects",
        "force_update",
    ]

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("ts_corporation_update_status").annotate(
            last_update_at=Max(
                "ts_corporation_update_status__last_run_finished_at",
                filter=~Q(ts_corporation_update_status__section="payments"),
            )
        )

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

    @admin.display(ordering="last_update_at", description=_("last update run"))
    def _last_update_at(self, obj: CorporationOwner):
        return naturaltime(obj.last_update_at) if obj.last_update_at else "-"

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description=_("Force update selected corporations"))
    def force_update(self, request, queryset):
        """Force update of selected corporations."""
        count = 0
        for corporation_audit in queryset:
            update_corporation.delay(owner_pk=corporation_audit.pk, force_refresh=True)
            count += 1

        messages.success(
            request,
            _(
                f"Started force update for {count} corporation(s). Updates will run in the background."
            ),
        )


@admin.register(AllianceOwner)
class AllianceOwnerAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_eve_alliance__alliance_id",
        "_eve_alliance__alliance_name",
        "corporation",
        "_last_update_at",
    )

    list_display_links = (
        "_entity_pic",
        "_eve_alliance__alliance_id",
        "_eve_alliance__alliance_name",
    )

    list_select_related = ("eve_alliance", "corporation__eve_corporation")

    ordering = ["eve_alliance__alliance_name"]

    search_fields = [
        "eve_alliance__alliance_name",
        "eve_alliance__alliance_id",
    ]

    actions = [
        "delete_objects",
        "force_update",
    ]

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("ts_alliance_update_status").annotate(
            last_update_at=Max(
                "ts_alliance_update_status__last_run_finished_at",
                filter=~Q(ts_alliance_update_status__section="payments"),
            )
        )

    @admin.display(description="")
    def _entity_pic(self, obj: AllianceOwner):
        eve_id = obj.eve_alliance.alliance_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("alliance", eve_id, 32),
        )

    @admin.display(description="Alliance ID", ordering="eve_alliance__alliance_id")
    def _eve_alliance__alliance_id(self, obj: AllianceOwner):
        return obj.eve_alliance.alliance_id

    @admin.display(description="Alliance Name", ordering="eve_alliance__alliance_name")
    def _eve_alliance__alliance_name(self, obj: AllianceOwner):
        return obj.eve_alliance.alliance_name

    @admin.display(ordering="last_update_at", description=_("last update run"))
    def _last_update_at(self, obj: AllianceOwner):
        return naturaltime(obj.last_update_at) if obj.last_update_at else "-"

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description=_("Force update selected alliances"))
    def force_update(self, request, queryset):
        """Force update of selected alliances."""
        count = 0
        for alliance_audit in queryset:
            update_alliance.delay(owner_pk=alliance_audit.pk, force_refresh=True)
            count += 1

        messages.success(
            request,
            _(
                f"Started force update for {count} alliance(s). Updates will run in the background."
            ),
        )

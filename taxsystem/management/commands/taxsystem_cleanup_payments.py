# Django
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Model

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.alliance import AlliancePayments
from taxsystem.models.corporation import CorporationPayments
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class Command(BaseCommand):
    help = (
        "Clean up duplicate from payments based on entry_id, keeping the oldest entry."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find duplicates based on relevant fields
        duplicates_corp = (
            CorporationPayments.objects.values("entry_id")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )
        duplicates_ally = (
            AlliancePayments.objects.values("entry_id")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        total_deleted = 0

        def _process_duplicates(model: Model, duplicates_qs, label: str):
            nonlocal total_deleted
            for duplicate in duplicates_qs:
                entry_id = duplicate["entry_id"]
                qs = model.objects.filter(entry_id=entry_id).order_by("date", "pk")

                keeper = qs.first()
                if not keeper:
                    # shouldn't happen, but guard against it
                    continue

                to_delete = qs.exclude(pk=keeper.pk)
                count = to_delete.count()

                owner_info = getattr(keeper.account, "owner", None)
                owner_display = str(owner_info) if owner_info is not None else "N/A"

                if count == 0:
                    continue

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Would delete {count} duplicate(s) for {label} entry_id={entry_id} "
                            f"keeping id={keeper.pk} (owner={owner_display})"
                        )
                    )
                else:
                    with transaction.atomic():
                        to_delete.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Deleted {count} duplicate(s) for {label} entry_id={entry_id} (kept id={keeper.pk})"
                        )
                    )

                total_deleted += count

        # Process corporation and alliance duplicates
        _process_duplicates(CorporationPayments, duplicates_corp, "corporation")
        _process_duplicates(AlliancePayments, duplicates_ally, "alliance")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run: Would delete {total_deleted} duplicate payment(s)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully deleted {total_deleted} duplicate payment(s)"
                )
            )

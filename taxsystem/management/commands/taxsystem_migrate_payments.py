# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.corporation import CorporationOwner, CorporationPayments
from taxsystem.models.wallet import CorporationWalletJournalEntry

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class Command(BaseCommand):
    help = "Migrate Corporations to new Payments Model"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        corporations = CorporationOwner.objects.all()
        payments_entry_ids = CorporationPayments.objects.all().values_list(
            "entry_id", flat=True
        )
        if not corporations:
            self.stdout.write(
                "No Corporations found in the database. Skipping migration."
            )
            return

        for corporation in corporations:
            try:
                with transaction.atomic():
                    journals = CorporationWalletJournalEntry.objects.filter(
                        division__corporation=corporation
                    ).select_related("division")

                    if not journals:
                        self.stdout.write(
                            f"No Wallet Divisions found for {corporation}. Skipping..."
                        )
                        continue

                    successful = 0
                    for journal in journals:
                        if journal.entry_id in payments_entry_ids:
                            try:
                                payment = CorporationPayments.objects.get(
                                    owner__isnull=True,
                                    entry_id=journal.entry_id,
                                )
                                payment.owner = corporation
                                payment.journal = journal
                                payment.save()
                                self.stdout.write(
                                    f"Updated Payment {payment.pk} and assigned to {corporation} for entry_id {journal.entry_id}."
                                )
                                successful += 1
                                continue
                            except CorporationPayments.DoesNotExist:
                                self.stdout.write(
                                    f"Payment with entry_id {journal.entry_id} not found, skipping."
                                )
                                continue
                            except CorporationPayments.MultipleObjectsReturned:
                                # Inform user to run cleanup command to resolve duplicates
                                self.stdout.write(
                                    f"Multiple payments found for entry_id {journal.entry_id}. "
                                    "Please run: `python manage.py taxsystem_cleanup_payments` "
                                    "to remove duplicate payments and keep the oldest entry."
                                )
                                continue
                    self.stdout.write(
                        f"Migration report for {corporation}: {successful} entries migrated."
                    )
            except IntegrityError as e:
                self.stdout.write(f"Failed to create Payment for {corporation}: {e}")
                continue

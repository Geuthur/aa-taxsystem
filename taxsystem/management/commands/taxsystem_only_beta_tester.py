# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.alliance import AllianceOwner, AlliancePayments
from taxsystem.models.wallet import CorporationWalletJournalEntry
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class Command(BaseCommand):
    help = "Migrate Corporations to new Payments Model"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        alliances = AllianceOwner.objects.all()
        payments_entry_ids = AlliancePayments.objects.all().values_list(
            "entry_id", flat=True
        )
        if not alliances:
            self.stdout.write("No Alliances found in the database. Skipping migration.")
            return

        for alliance in alliances:
            try:
                with transaction.atomic():
                    journals = CorporationWalletJournalEntry.objects.filter(
                        division__corporation=alliance.corporation
                    ).select_related("division")

                    if not journals:
                        self.stdout.write(
                            f"No Wallet Divisions found for {alliance}. Skipping..."
                        )
                        continue

                    successful = 0
                    for journal in journals:
                        if journal.entry_id in payments_entry_ids:
                            try:
                                payment = AlliancePayments.objects.get(
                                    owner__isnull=True,
                                    entry_id=journal.entry_id,
                                )
                                payment.owner = alliance
                                payment.journal = journal
                                payment.save()
                                self.stdout.write(
                                    f"Updated Payment {payment.pk} and assigned to {alliance} for entry_id {journal.entry_id}."
                                )
                                successful += 1
                                continue
                            except AlliancePayments.DoesNotExist:
                                self.stdout.write(
                                    f"Payment with entry_id {journal.entry_id} not found, skipping."
                                )
                                continue
                            except AlliancePayments.MultipleObjectsReturned:
                                # Inform user to run cleanup command to resolve duplicates
                                self.stdout.write(
                                    f"Multiple payments found for entry_id {journal.entry_id}. "
                                    "Please run: `python manage.py taxsystem_cleanup_payments` "
                                    "to remove duplicate payments and keep the oldest entry."
                                )
                                continue
                    self.stdout.write(
                        f"Migration report for {alliance}: {successful} entries migrated."
                    )
            except IntegrityError as e:
                self.stdout.write(f"Failed to create Payment for {alliance}: {e}")
                continue

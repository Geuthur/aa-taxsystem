# Django
from django.core.management.base import BaseCommand

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.general import EveEntity as EveEntityV2
from taxsystem.models.wallet import CorporationWalletJournalEntry
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
class Command(BaseCommand):
    help = "Migrate all EVE Entities to new EveEntityV2 Model and update all references in the database"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        self.stdout.write(
            "Migrating EVE Entities to new EveEntityV2 model and updating references..."
        )

        # Step 1: Collect all unique entity IDs from first_party and second_party
        self.stdout.write(
            "Step 1: Collecting unique entity IDs from CorporationWalletJournalEntry..."
        )

        unique_entity_ids = set()
        journals = CorporationWalletJournalEntry.objects.all().select_related(
            "first_party", "second_party"
        )

        total_journals = journals.count()
        self.stdout.write(f"Found {total_journals} journal entries to process.")

        for journal in journals.iterator():
            if journal.first_party_id:
                unique_entity_ids.add(journal.first_party_id)
            if journal.second_party_id:
                unique_entity_ids.add(journal.second_party_id)

        self.stdout.write(f"Found {len(unique_entity_ids)} unique entity IDs.")

        # Step 2: Migrate entities from old EveEntity to new EveEntityV2
        self.stdout.write("Step 2: Migrating entities to EveEntityV2...")

        migrated_count = 0
        skipped_count = 0
        dummy_count = 0

        for entity_id in unique_entity_ids:
            try:
                # Get old entity
                old_entity = EveEntity.objects.get(id=entity_id)

                # Create or update new entity with same data
                new_entity, created = EveEntityV2.objects.update_or_create(
                    id=old_entity.id,
                    defaults={
                        "name": old_entity.name,
                        "category": old_entity.category,
                    },
                )

                if created:
                    migrated_count += 1
                    self.stdout.write(
                        f"  Created EveEntityV2: {new_entity.id} - {new_entity.name}"
                    )
                else:
                    skipped_count += 1
            except EveEntity.DoesNotExist:
                # Create dummy entity with Unknown
                self.stdout.write(
                    self.style.WARNING(
                        f"  Old EveEntity with ID {entity_id} not found, creating dummy with 'Unknown'."
                    )
                )
                new_entity, created = EveEntityV2.objects.update_or_create(
                    id=entity_id,
                    defaults={
                        "name": "Unknown",
                        "category": "unknown",
                    },
                )
                if created:
                    dummy_count += 1
                continue
            except Exception as e:  # pylint: disable=broad-except
                self.stdout.write(
                    self.style.ERROR(f"  Error migrating entity {entity_id}: {e}")
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Migrated {migrated_count} new entities, {skipped_count} already existed, {dummy_count} dummy entities created."
            )
        )

        # Step 3: Update CorporationWalletJournalEntry references
        self.stdout.write(
            "Step 3: Updating CorporationWalletJournalEntry references..."
        )

        updated_count = 0
        error_count = 0

        journals = CorporationWalletJournalEntry.objects.all().select_related(
            "first_party", "second_party"
        )

        for journal in journals.iterator():
            try:
                updated = False

                # Update first_party_new if first_party exists
                if journal.first_party_id and not journal.first_party_new_id:
                    try:
                        new_entity = EveEntityV2.objects.get(id=journal.first_party_id)
                        journal.first_party_new = new_entity
                        updated = True
                    except EveEntityV2.DoesNotExist:
                        # Create dummy entity if not found
                        self.stdout.write(
                            self.style.WARNING(
                                f"  EveEntityV2 {journal.first_party_id} not found for journal {journal.entry_id}, creating dummy."
                            )
                        )
                        new_entity, _ = EveEntityV2.objects.get_or_create(
                            id=journal.first_party_id,
                            defaults={
                                "name": "Unknown",
                                "category": "unknown",
                            },
                        )
                        journal.first_party_new = new_entity
                        updated = True

                # Update second_party_new if second_party exists
                if journal.second_party_id and not journal.second_party_new_id:
                    try:
                        new_entity = EveEntityV2.objects.get(id=journal.second_party_id)
                        journal.second_party_new = new_entity
                        updated = True
                    except EveEntityV2.DoesNotExist:
                        # Create dummy entity if not found
                        self.stdout.write(
                            self.style.WARNING(
                                f"  EveEntityV2 {journal.second_party_id} not found for journal {journal.entry_id}, creating dummy."
                            )
                        )
                        new_entity, _ = EveEntityV2.objects.get_or_create(
                            id=journal.second_party_id,
                            defaults={
                                "name": "Unknown",
                                "category": "unknown",
                            },
                        )
                        journal.second_party_new = new_entity
                        updated = True

                if updated:
                    journal.save(update_fields=["first_party_new", "second_party_new"])
                    updated_count += 1

            except Exception as e:  # pylint: disable=broad-except
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error updating journal {journal.entry_id}: {e}")
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated_count} journal entries, {error_count} errors."
            )
        )

        self.stdout.write(self.style.SUCCESS("Migration completed successfully!"))

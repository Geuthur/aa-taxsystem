# Standard Library
from io import StringIO

# Django
from django.core.management import call_command
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus

# AA Tax System
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    CorporationPaymentsFactory,
    CorporationTaxAccountFactory,
    DivisionFactory,
)

COMMAND_PATH = "taxsystem.management.commands.taxsystem_migrate_payments"


class TestMigratePayments(TaxSystemTestCase):
    """Test Tax System Payment Migration Command."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.division = DivisionFactory(corporation=cls.audit)
        cls.journal_entry = CorporationJournalFactory(division=cls.division)
        cls.tax_account = CorporationTaxAccountFactory(
            name=cls.user_character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        cls.payments = CorporationPaymentsFactory(
            name=cls.user_character.character_name,
            owner=None,  # This is the key part of the test, we are creating a payment with no owner to simulate the migration scenario.
            entry_id=cls.journal_entry.entry_id,  # This is the key part of the test, we are creating a payment with the same entry_id as the journal entry to simulate the migration scenario.
            account=cls.tax_account,
            journal=cls.journal_entry,
            request_status=PaymentRequestStatus.PENDING,
        )

    def test_should_migrate(self):
        # Test Data
        out = StringIO()

        # Test Action
        call_command("taxsystem_migrate_payments", stdout=out)
        output = out.getvalue()
        # Expected Result
        self.assertIn(
            f"Migration report for {self.audit.eve_corporation.corporation_name}: 1 entries migrated.",
            output,
        )

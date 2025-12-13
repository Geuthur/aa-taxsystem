# Standard Library
from io import StringIO

# Django
from django.core.management import call_command
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.corporation import CorporationPayments
from taxsystem.models.helpers.textchoices import AccountStatus, PaymentRequestStatus

# AA Tax System
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment,
    create_payment_system,
)
from taxsystem.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)

COMMAND_PATH = "taxsystem.management.commands.taxsystem_migrate_payments"


class TestMigratePayments(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_corporation_owner_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

        cls.division = create_division(
            corporation=cls.audit,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

        cls.journal_entry = create_wallet_journal_entry(
            division=cls.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Test Journal Entry",
            ref_type="tax_payment",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
        )

        cls.payment_system = create_payment_system(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=AccountStatus.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        cls.payments = create_payment(
            name=cls.user_character.character.character_name,
            account=cls.payment_system,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

    def test_should_migrate(self):
        # when
        out = StringIO()
        call_command("taxsystem_migrate_payments", stdout=out)
        output = out.getvalue()

        # then
        self.assertIn(
            "Migration report for Hell RiderZ: 1 entries migrated.",
            output,
        )

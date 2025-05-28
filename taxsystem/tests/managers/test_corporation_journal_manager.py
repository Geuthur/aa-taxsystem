# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase, create_user_from_evecharacter
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.tests.testdata.esi_stub import esi_client_stub
from taxsystem.tests.testdata.generate_owneraudit import create_owneraudit_from_user
from taxsystem.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.managers.wallet_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
@patch(MODULE_PATH + ".EveEntity.objects.bulk_resolve_ids")
@patch(MODULE_PATH + ".EveEntity.objects.filter")
class TestWalletManager(NoSocketsTestCase):
    """Test Wallet Manager for Corporation Journal Entries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_owneraudit_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

    def test_update_wallet_journal(
        self, mock_filter, mock_entity_bulk, mock_etag, mock_esi
    ):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()
        filter_mock = mock_filter.return_value
        filter_mock.count.return_value = 0

        mock_entity_bulk.side_effect = [
            EveEntity.objects.create(
                id=9998,
                name="Test Character",
                category="character",
            )
        ]

        self.audit.update_wallet(force_refresh=False)

        self.assertSetEqual(
            set(self.division.ts_corporation_wallet.values_list("entry_id", flat=True)),
            {10, 13, 16},
        )
        obj = self.division.ts_corporation_wallet.get(entry_id=10)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.context_id, 1)
        self.assertEqual(obj.first_party.id, 2001)
        self.assertEqual(obj.second_party.id, 1001)

        obj = self.division.ts_corporation_wallet.get(entry_id=13)
        self.assertEqual(obj.amount, 5000)

        obj = self.division.ts_corporation_wallet.get(entry_id=16)
        self.assertEqual(obj.amount, 10000)

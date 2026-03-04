# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings

# AA TaxSystem
from taxsystem.models.general import EveEntity
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)
from taxsystem.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.managers.wallet_manager"

TAXSYSTEM_WALLET_JOURNAL_ENDPOINTS = [
    EsiEndpoint(
        category="Wallet",
        method="GetCorporationsCorporationIdWalletsDivisionJournal",
        param_names=("corporation_id", "division"),
    ),
    EsiEndpoint(
        category="Corporation",
        method="GetCorporationsCorporationIdDivisions",
        param_names="corporation_id",
    ),
    EsiEndpoint(
        category="Wallet",
        method="GetCorporationsCorporationIdWallets",
        param_names="corporation_id",
    ),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".EveEntity.objects.bulk_resolve_names")
@patch(MODULE_PATH + ".EveEntity.objects.filter")
class TestWalletManager(TaxSystemTestCase):
    """Test Wallet Managers for Corporation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(id=1002)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )
        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_wallet_journal(self, mock_filter, mock_entity_bulk, mock_esi):
        """
        Test updating wallet journal entries from ESI data.
        This test should verify that wallet journal entries are correctly fetched and stored.

        Results:
            1. Wallet Journal Entries (entry_id: 10, 13, 16) are created with correct data.
            2. First and Second party entities are resolved correctly.
            3. Amounts and context IDs are stored accurately.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=TAXSYSTEM_WALLET_JOURNAL_ENDPOINTS
        )
        filter_mock = mock_filter.return_value
        filter_mock.count.return_value = 0

        mock_entity_bulk.side_effect = [
            EveEntity.objects.create(
                id=9998,
                name="Test Character",
                category="character",
            ),
        ]

        # Test Action

        self.audit.update_wallet(force_refresh=False)

        # Expected Results
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

    def test_update_division_names(self, mock_filter, mock_entity_bulk, mock_esi):
        """
        Test updating division names from ESI data.
        This test should verify that division names are correctly fetched and updated.

        Results:
            1. Division names are updated correctly based on ESI data.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=TAXSYSTEM_WALLET_JOURNAL_ENDPOINTS
        )

        # Test Action
        self.audit.update_division_names(force_refresh=False)

        # Expected Results
        obj = self.audit.ts_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=2
        )
        self.assertEqual(obj.name, "Rechnungen")

        obj = self.audit.ts_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=4
        )
        self.assertEqual(obj.name, "Ship Replacment Abteilung")

        obj = self.audit.ts_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=6
        )
        self.assertEqual(obj.name, "Partner")

    def test_update_divisions(self, mock_filter, mock_entity_bulk, mock_esi):
        """
        Test updating division balances from ESI data.
        This test should verify that division balances are correctly fetched and updated.

        Results:
            1. Division balances are updated correctly based on ESI data.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=TAXSYSTEM_WALLET_JOURNAL_ENDPOINTS
        )

        # Test Action
        self.audit.update_divisions(force_refresh=False)

        # Expected Results
        obj = self.audit.ts_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=2
        )
        self.assertEqual(obj.balance, 0)

        obj = self.audit.ts_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=4
        )
        self.assertEqual(obj.balance, 500000)

        obj = self.audit.ts_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=6
        )
        self.assertEqual(obj.balance, 250000)

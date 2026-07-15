# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Third Party
import pook

# Django
from django.test import override_settings

# AA TaxSystem
from taxsystem.models.general import EveEntity
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.managers.wallet_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
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

    @pook.on
    def test_update_wallet_journal(self, mock_filter, mock_entity_bulk):
        """
        Test updating wallet journal entries from ESI data.
        This test should verify that wallet journal entries are correctly fetched and stored.

        Results:
            1. Wallet Journal Entries (entry_id: 10, 13, 16) are created with correct data.
            2. First and Second party entities are resolved correctly.
            3. Amounts and context IDs are stored accurately.
        """
        # Test Data
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/wallets/1/journal",
            reply=HTTPStatus.OK,
            response_headers={"X-Pages": "1"},
            response_json=[
                {
                    "amount": 1000,
                    "balance": 2000,
                    "context_id": 1,
                    "context_id_type": "character_id",
                    "date": "2016-10-29T14:00:00Z",
                    "description": "Test Journal",
                    "first_party_id": 2001,
                    "id": 10,
                    "reason": "Test Reason",
                    "ref_type": "player_donation",
                    "second_party_id": 1001,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
                {
                    "amount": 5000,
                    "balance": 10000,
                    "context_id": 2,
                    "context_id_type": "system_id",
                    "date": "2016-12-01T14:00:00Z",
                    "description": "Bounty Tax",
                    "first_party_id": 1001,
                    "id": 13,
                    "reason": "Bounty",
                    "ref_type": "bounty_prizes",
                    "second_party_id": 2001,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
                {
                    "amount": 10000,
                    "balance": 20000,
                    "context_id": 4,
                    "context_id_type": "system_id",
                    "date": "2016-12-01T14:00:00Z",
                    "description": "Unknown Second Party",
                    "first_party_id": 1001,
                    "id": 16,
                    "reason": "Bounty",
                    "ref_type": "bounty_prizes",
                    "second_party_id": 9998,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
            ],
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

    @pook.on
    def test_update_division_names(self, mock_filter, mock_entity_bulk):
        """
        Test updating division names from ESI data.
        This test should verify that division names are correctly fetched and updated.

        Results:
            1. Division names are updated correctly based on ESI data.
        """
        # Test Data
        # Mock ESI response for corporation divisions names
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/divisions",
            reply=HTTPStatus.OK,
            response_json={
                "hangar": [
                    {"division": 1, "name": "Test Hangar"},
                    {"division": 2, "name": "Officer Hangar"},
                    {"division": 3, "name": "Schiffe"},
                    {"division": 4, "name": "Lager"},
                    {"division": 5, "name": "Wertvoll"},
                    {"division": 6, "name": "Produktion"},
                    {"division": 7, "name": "Blueprints"},
                ],
                "wallet": [
                    {"division": 1, "name": None},
                    {"division": 2, "name": "Rechnungen"},
                    {"division": 3, "name": "Event's"},
                    {"division": 4, "name": "Ship Replacment Abteilung"},
                    {"division": 5, "name": "Roaming"},
                    {"division": 6, "name": "Partner"},
                    {"division": 7, "name": "Backup"},
                ],
            },
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

    @pook.on
    def test_update_divisions(self, mock_filter, mock_entity_bulk):
        """
        Test updating division balances from ESI data.
        This test should verify that division balances are correctly fetched and updated.

        Results:
            1. Division balances are updated correctly based on ESI data.
        """
        # Test Data
        # Mock ESI response for corporation divisions
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/wallets",
            reply=HTTPStatus.OK,
            response_headers={"X-Pages": "1"},
            response_json=[
                {"balance": 0, "division": 1},
                {"balance": 0, "division": 2},
                {"balance": 0, "division": 3},
                {"balance": 500000, "division": 4},
                {"balance": 0, "division": 5},
                {"balance": 250000, "division": 6},
                {"balance": 0, "division": 7},
            ],
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

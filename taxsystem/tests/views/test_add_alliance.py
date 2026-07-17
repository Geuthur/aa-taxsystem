# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.models import AllianceAdminHistory, AllianceOwner
from taxsystem.models.helpers.textchoices import AdminActions
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.views"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
class TestAddAllianceView(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_add_alliance(self, mock_tasks, mock_messages):
        """Test adding an alliance via the add_alliance view."""
        # Test Data
        corporation = EveCorporationInfoFactory(
            corporation_id=2001, corporation_name="Test Corporation"
        )
        character = EveCharacterFactory(character_id=1001, corporation_id=2001)
        user = UserMainFactory(main_character__character=character)
        CorporationOwnerFactory(user=user, eve_corporation=corporation)
        token = user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_alliance(user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("taxsystem:index"))
        self.assertTrue(mock_tasks.update_alliance.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            AllianceOwner.objects.filter(
                corporation__eve_corporation__corporation_id=2001
            ).exists()
        )
        self.assertTrue(
            AllianceAdminHistory.objects.filter(action=AdminActions.ADD).exists()
        )

    def test_add_alliance_existing(self, mock_tasks, mock_messages):
        """Test adding an alliance that already exists via the add_alliance view."""
        # Test Data
        corporation = EveCorporationInfoFactory(
            corporation_id=2001, corporation_name="Test Corporation"
        )
        character = EveCharacterFactory(character_id=1001, corporation=corporation)
        user = UserMainFactory(main_character__character=character)
        corp_audit = CorporationOwnerFactory(user=user, eve_corporation=corporation)
        audit = AllianceOwnerFactory(user=user, corporation=corp_audit)
        token = user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_alliance(user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("taxsystem:index"))
        self.assertTrue(mock_tasks.update_alliance.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            AllianceOwner.objects.filter(
                corporation__eve_corporation__corporation_id=2001
            ).exists()
        )
        self.assertFalse(
            AllianceAdminHistory.objects.filter(
                owner=audit, action=AdminActions.ADD
            ).exists()
        )

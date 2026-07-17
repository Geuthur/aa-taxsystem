# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.models import CorporationAdminHistory, CorporationOwner
from taxsystem.models.helpers.textchoices import AdminActions
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationOwnerFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.views"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
class TestAddCorpView(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_add_corp(self, mock_tasks, mock_messages):
        """Test adding a corporation via the add_corp view."""
        # Test Data
        character = EveCharacterFactory(character_id=1001, corporation_id=2001)
        user = UserMainFactory(main_character__character=character)
        token = user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_corporation(user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("taxsystem:index"))
        self.assertTrue(mock_tasks.update_corporation.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CorporationOwner.objects.filter(
                eve_corporation__corporation_id=2001
            ).exists()
        )
        self.assertTrue(
            CorporationAdminHistory.objects.filter(action=AdminActions.ADD).exists()
        )

    def test_add_corp_existing(self, mock_tasks, mock_messages):
        """Test adding a corporation that already exists via the add_corp view."""
        # Test Data
        corporation = EveCorporationInfoFactory(
            corporation_id=2001, corporation_name="Test Corporation"
        )
        character = EveCharacterFactory(character_id=1001, corporation=corporation)
        user = UserMainFactory(main_character__character=character)
        audit = CorporationOwnerFactory(user=user, eve_corporation=corporation)
        token = user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_corporation(user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("taxsystem:index"))
        self.assertTrue(mock_tasks.update_corporation.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CorporationOwner.objects.filter(
                eve_corporation__corporation_id=2001
            ).exists()
        )
        self.assertFalse(
            CorporationAdminHistory.objects.filter(
                owner=audit, action=AdminActions.ADD
            ).exists()
        )

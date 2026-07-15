# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Third Party
import pook

# Django
from django.test import override_settings

# AA TaxSystem
from taxsystem.models.general import EveEntity
from taxsystem.models.general import EveEntity as EveEntityV2
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_division,
    create_filterset,
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.managers.eveonline_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestEveEntityManager(TaxSystemTestCase):
    """Test Eve Entity Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(cls.user, tax_type="alliance")

        cls.filter_set = create_filterset(
            owner=cls.audit,
            name="Test Filter Set",
            description="Filter Set for Testing Alliance Manager",
        )

        cls.division = create_division(
            corporation=cls.audit.corporation,
            division_id=1,
            name="Main Division",
            balance=1000000,
        )

        cls.eve_character_first_party = EveEntity.objects.get(id=1002)
        cls.eve_character_second_party = EveEntity.objects.get(id=1001)

    @pook.on
    def test_bulk_resolve_names(self):
        """
        Test bulk_resolve_names method of EveEntityManager with mocked ESI response.
        """
        pook.post(
            url="https://esi.evetech.net/universe/names",
            reply=HTTPStatus.OK,
            response_json=[
                {"id": 9997, "name": "Bulk Character", "category": "character"},
                {"id": 9998, "name": "Bulk Character 2", "category": "character"},
            ],
        )

        manager = EveEntityV2.objects
        # Mock ESI response for universe names
        ids_to_resolve = [9997, 9998]  # Include an ID that doesn't exist
        resolver = manager.bulk_resolve_names(ids_to_resolve)

        # Assert that the resolver returns correct names for known IDs
        self.assertEqual(resolver.to_name(9997), "Bulk Character")
        # Assert that the resolver returns an empty string for unknown ID
        self.assertEqual(resolver.to_name(9998), "Bulk Character 2")

    @pook.on
    def test_bulk_resolve_names_with_existing_ids_only(self):
        """Should resolve names from existing DB entities when no new IDs are needed."""
        pook.post(
            url="https://esi.evetech.net/universe/names",
            reply=HTTPStatus.OK,
            response_json=[
                {"id": 9997, "name": "Bulk Character", "category": "character"},
            ],
        )

        manager = EveEntityV2.objects

        resolver = manager.bulk_resolve_names([1001, 1002])

        self.assertEqual(resolver.to_name(1001), self.eve_character_second_party.name)
        self.assertEqual(resolver.to_name(1002), self.eve_character_first_party.name)

    @pook.on
    def test_bulk_resolve_names_with_mixed_existing_and_new_ids(self):
        """Should resolve both existing and newly fetched entities in one resolver."""
        pook.post(
            url="https://esi.evetech.net/universe/names",
            reply=HTTPStatus.OK,
            response_json=[
                {"id": 9997, "name": "Bulk Character", "category": "character"},
            ],
        )
        manager = EveEntityV2.objects

        resolver = manager.bulk_resolve_names([1001, 9997])

        self.assertEqual(resolver.to_name(1001), self.eve_character_second_party.name)
        self.assertEqual(resolver.to_name(9997), "Bulk Character")

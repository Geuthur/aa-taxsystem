# Standard Library
from http import HTTPStatus

# Third Party
import pook

# AA TaxSystem
from taxsystem.models.general import EveEntity as EveEntityV2
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import AllianceOwnerFactory, EveEntityFactory

MODULE_PATH = "taxsystem.managers.eveonline_manager"


class TestEveEntityManager(TaxSystemTestCase):
    """Test Eve Entity Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = AllianceOwnerFactory(user=cls.user)

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

        entity_1001 = EveEntityFactory(id=1001, name="Existing Character 1")
        entity_1002 = EveEntityFactory(id=1002, name="Existing Character 2")

        resolver = manager.bulk_resolve_names([1001, 1002])

        self.assertEqual(resolver.to_name(1001), entity_1001.name)
        self.assertEqual(resolver.to_name(1002), entity_1002.name)

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

        entity_1001 = EveEntityFactory(id=1001, name="Existing Character 1")
        resolver = manager.bulk_resolve_names([1001, 9997])

        self.assertEqual(resolver.to_name(1001), entity_1001.name)
        self.assertEqual(resolver.to_name(9997), "Bulk Character")

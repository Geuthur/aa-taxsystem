# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings

# AA TaxSystem
from taxsystem.models.general import EveEntity
from taxsystem.models.general import EveEntity as EveEntityV2
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)
from taxsystem.tests.testdata.utils import (
    create_division,
    create_filterset,
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.managers.eveonline_manager"

TAXSYSTEM_UNIVERSE_ENDPOINTS = [
    EsiEndpoint("Universe", "PostUniverseNames", "ids"),
]


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

    @patch(MODULE_PATH + ".esi")
    def test_bulk_resolve_names(self, mock_esi):
        """
        Test bulk_resolve_names method of EveEntityManager with mocked ESI response.
        """
        mock_esi.client = create_esi_client_stub(endpoints=TAXSYSTEM_UNIVERSE_ENDPOINTS)
        manager = EveEntityV2.objects
        # Mock ESI response for universe names
        ids_to_resolve = [9997, 9998]  # Include an ID that doesn't exist
        resolver = manager.bulk_resolve_names(ids_to_resolve)

        # Assert that the resolver returns correct names for known IDs
        self.assertEqual(resolver.to_name(9997), "Bulk Character")
        # Assert that the resolver returns an empty string for unknown ID
        self.assertEqual(resolver.to_name(9998), "Bulk Character 2")

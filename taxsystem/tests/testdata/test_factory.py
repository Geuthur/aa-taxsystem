"""Test to ensure that the factories are working correctly."""

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
    EveCorporationInfoFactory,
    EveEntityFactory,
    UserMainFactory,
)


class TestFactory(TaxSystemTestCase):
    """Test the factories."""

    def test_can_create_user(self):
        """Test that a user can be created."""
        user = UserMainFactory()
        self.assertTrue(user.has_perm("taxsystem.basic_access"))

    def test_can_create_corporation_owner(self):
        """Test that a corporation owner can be created."""
        owner = CorporationOwnerFactory()
        self.assertTrue(owner.eve_corporation)

    def test_can_create_alliance_owner(self):
        """Test that an alliance owner can be created."""
        owner = AllianceOwnerFactory()
        self.assertTrue(owner.eve_alliance)

    def test_can_create_corporation_owner_from_user(self):
        """Test that a corporation owner can be created from a user."""
        user = UserMainFactory()
        owner = CorporationOwnerFactory(user=user)
        self.assertEqual(owner.eve_corporation, user.profile.main_character.corporation)

    def test_can_create_alliance_owner_from_user(self):
        """Test that an alliance owner can be created from a user."""
        user = UserMainFactory()
        owner = AllianceOwnerFactory(user=user)
        self.assertEqual(
            owner.eve_alliance, user.profile.main_character.corporation.alliance
        )

    def test_can_create_eveentity(self):
        """Test that an EveEntity can be created."""
        entity = EveEntityFactory()
        self.assertTrue(entity.name)
        self.assertTrue(entity.category in ["character", "corporation", "alliance"])

    def test_can_create_custom_eveentity(self):
        """Test that a custom EveEntity can be created."""
        entity = EveEntityFactory(name="Test Corp", category="corporation")
        self.assertEqual(entity.name, "Test Corp")
        self.assertEqual(entity.category, "corporation")

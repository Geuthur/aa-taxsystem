# Django
from django.test import TestCase

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.tests.testdata.generate_owneraudit import (
    create_alliance_owner_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.models.owneraudit"


class TestAllianceOwnerAuditModel(TestCase):
    """Test AllianceOwner QuerySet methods (visible_to, manage_to)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        # Create users with characters in alliance 3001 (Voices of War)
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["taxsystem.basic_access"]
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1004, permissions=["taxsystem.basic_access"]
        )

        # Create alliance audits for both users
        cls.audit = create_alliance_owner_from_user(cls.user)
        cls.audit2 = create_alliance_owner_from_user(cls.user2)

    def test_str(self):
        """Test string representation of AllianceOwner."""
        expected_str = AllianceOwner.objects.get(id=self.audit.pk)
        self.assertEqual(str(self.audit), str(expected_str))

    def test_access_no_perms(self):
        """Test should return only own alliance if basic_access is set."""
        alliances = AllianceOwner.objects.visible_to(self.user)
        self.assertIn(self.audit, alliances)
        # Note: Both users are in the same alliance, so both audits visible
        self.assertIn(self.audit2, alliances)

    def test_access_perms_own_alliance(self):
        """Test should return only own alliance if manage_own_alliance is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_alliance", self.user
        )
        self.user.refresh_from_db()
        alliances = AllianceOwner.objects.visible_to(self.user)
        self.assertIn(self.audit, alliances)
        self.assertIn(self.audit2, alliances)  # Same alliance

    def test_access_perms_manage_alliances(self):
        """Test should return all alliances if manage_alliances is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_alliances", self.user
        )
        self.user.refresh_from_db()
        alliances = AllianceOwner.objects.visible_to(self.user)
        self.assertIn(self.audit, alliances)
        self.assertIn(self.audit2, alliances)

    def test_manage_to_no_perms(self):
        """Test should return empty queryset if no management permissions are set."""
        alliances = AllianceOwner.objects.manage_to(self.user)
        self.assertNotIn(self.audit, alliances)
        self.assertNotIn(self.audit2, alliances)

    def test_manage_to_perms_own_alliance(self):
        """Test should return only own alliance if manage_own_alliance is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_alliance", self.user
        )
        self.user.refresh_from_db()
        alliances = AllianceOwner.objects.manage_to(self.user)
        self.assertIn(self.audit, alliances)
        self.assertIn(self.audit2, alliances)  # Same alliance

    def test_manage_to_perms_manage_alliances(self):
        """Test should return all alliances if manage_alliances is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_alliances", self.user
        )
        self.user.refresh_from_db()
        alliances = AllianceOwner.objects.manage_to(self.user)
        self.assertIn(self.audit, alliances)
        self.assertIn(self.audit2, alliances)

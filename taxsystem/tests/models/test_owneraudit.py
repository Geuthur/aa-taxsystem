# Django
from django.contrib.auth.models import Permission
from django.test import TestCase

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.tax import OwnerAudit
from taxsystem.tests.testdata.generate_owneraudit import (
    create_owneraudit_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth

MODULE_PATH = "taxsystem.models.owneraudit"


class TestOwnerAuditModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["taxsystem.basic_access"]
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002, permissions=["taxsystem.basic_access"]
        )
        cls.audit = create_owneraudit_from_user(cls.user)
        cls.audit2 = create_owneraudit_from_user(cls.user2)

    def test_str(self):
        expected_str = OwnerAudit.objects.get(id=self.audit.pk)
        self.assertEqual(self.audit, expected_str)

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.audit.get_esi_scopes(),
            [
                # General
                "esi-corporations.read_corporation_membership.v1",
                "esi-corporations.track_members.v1",
                "esi-characters.read_corporation_roles.v1",
                # wallets
                "esi-wallet.read_corporation_wallets.v1",
                "esi-corporations.read_divisions.v1",
            ],
        )

    def test_access_no_perms(self):
        """Test should return only own corporation if basic_access is set."""
        corporation = OwnerAudit.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_access_perms_own_corp(self):
        """Test should return only own corporation if manage_own_corp is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_corp", self.user
        )
        self.user.refresh_from_db()
        corporation = OwnerAudit.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_access_perms_manage_corps(self):
        """Test should return all corporations if manage_corps is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_corps", self.user
        )
        self.user.refresh_from_db()
        corporation = OwnerAudit.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertIn(self.audit2, corporation)

    def test_manage_to_no_perms(self):
        """Test should return None if no permissions are set."""
        corporation = OwnerAudit.objects.manage_to(self.user)
        self.assertNotIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_manage_to_perms_own_corp(self):
        """Test should return only own corporation if manage_own_corp is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_corp", self.user
        )
        self.user.refresh_from_db()
        corporation = OwnerAudit.objects.manage_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_manage_to_perms_manage_corps(self):
        """Test should return all corporations if manage_corps is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_corps", self.user
        )
        self.user.refresh_from_db()
        corporation = OwnerAudit.objects.manage_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertIn(self.audit2, corporation)

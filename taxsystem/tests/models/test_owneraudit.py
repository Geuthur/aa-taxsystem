# Django
from django.test import TestCase

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils

# AA TaxSystem
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.models.owneraudit"


class TestOwnerAuditModel(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(cls.user)
        cls.audit2 = create_owner_from_user(cls.superuser)

    def test_str(self):
        expected_str = CorporationOwner.objects.get(id=self.audit.pk)
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
        corporation = CorporationOwner.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_access_perms_own_corp(self):
        """Test should return only own corporation if manage_own_corp is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_corp", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationOwner.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_access_perms_manage_corps(self):
        """Test should return all corporations if manage_corps is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_corps", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationOwner.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertIn(self.audit2, corporation)

    def test_manage_to_no_perms(self):
        """Test should return None if no permissions are set."""
        corporation = CorporationOwner.objects.manage_to(self.user)
        self.assertNotIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_manage_to_perms_own_corp(self):
        """Test should return only own corporation if manage_own_corp is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_own_corp", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationOwner.objects.manage_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_manage_to_perms_manage_corps(self):
        """Test should return all corporations if manage_corps is set."""
        self.user = AuthUtils.add_permission_to_user_by_name(
            "taxsystem.manage_corps", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationOwner.objects.manage_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertIn(self.audit2, corporation)

# Django
# AA TaxSystem
from taxsystem.models.general import General
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
    UserMainFactory,
)


class TestGeneralPermission(AuthTestCase):
    def test_permissions_should_keep_existing_codenames(self):
        # Test Data
        expected = {
            "basic_access",
            "create_access",
            "manage_own_corp",
            "manage_corps",
            "manage_own_alliance",
            "manage_alliances",
            "admin_access",
        }

        # Test Action
        codenames = {value for value, __ in General._meta.permissions}

        # Expected Result
        self.assertEqual(codenames, expected)

    def test_has_management_access_should_depend_on_five_permissions(self):
        # Test Data
        granted = [
            "admin_access",
            "manage_corps",
            "manage_own_corp",
            "manage_alliances",
            "manage_own_alliance",
        ]
        users = {p: UserMainFactory(permissions__=[f"taxsystem.{p}"]) for p in granted}
        basic = UserMainFactory(permissions__=["taxsystem.basic_access"])

        # Test Action
        results = {
            p: General.objects.has_management_access(u) for p, u in users.items()
        }

        # Expected Result
        self.assertTrue(all(results.values()))
        self.assertFalse(General.objects.has_management_access(basic))
        self.assertTrue(General.objects.has_management_access(self.superuser))

    def test_has_all_access_should_depend_on_owner_type(self):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        alliances = UserMainFactory(permissions__=["taxsystem.manage_alliances"])
        own = UserMainFactory(
            permissions__=["taxsystem.manage_own_corp", "taxsystem.manage_own_alliance"]
        )

        # Test Action
        result = {
            name: (
                General.objects.has_all_access("corporation", user),
                General.objects.has_all_access("alliance", user),
            )
            for name, user in {
                "admin": admin,
                "corps": corps,
                "alliances": alliances,
                "own": own,
            }.items()
        }

        # Expected Result
        self.assertEqual(result["admin"], (True, True))
        self.assertEqual(result["corps"], (True, False))
        self.assertEqual(result["alliances"], (False, True))
        self.assertEqual(result["own"], (False, False))
        self.assertFalse(General.objects.has_all_access("unknown", admin))

    def test_get_administration_owners_should_return_all_or_own_owners(self):
        # Test Data
        own_user = UserMainFactory(
            permissions__=["taxsystem.manage_own_corp", "taxsystem.manage_own_alliance"]
        )
        own_corp = CorporationOwnerFactory(user=own_user)
        own_alliance = AllianceOwnerFactory(user=own_user)
        other_corp = CorporationOwnerFactory()
        other_alliance = AllianceOwnerFactory()
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        alliances = UserMainFactory(permissions__=["taxsystem.manage_alliances"])
        nobody = UserMainFactory(permissions__=["taxsystem.basic_access"])

        # Test Action
        own_corps = General.objects.get_administration_owners("corporation", own_user)
        own_alliances = General.objects.get_administration_owners("alliance", own_user)
        all_corps = General.objects.get_administration_owners("corporation", corps)
        all_alliances = General.objects.get_administration_owners("alliance", alliances)
        no_corps = General.objects.get_administration_owners("corporation", alliances)
        no_one = General.objects.get_administration_owners("corporation", nobody)

        # Expected Result
        self.assertEqual(list(own_corps), [own_corp])
        self.assertEqual(list(own_alliances), [own_alliance])
        self.assertIn(other_corp, all_corps)
        self.assertIn(other_alliance, all_alliances)
        self.assertFalse(no_corps.exists())
        self.assertFalse(no_one.exists())
        with self.assertRaises(ValueError):
            General.objects.get_administration_owners("unknown", corps)

    def test_has_administration_owner_access_should_decide_per_owner(self):
        # Test Data
        own_user = UserMainFactory(permissions__=["taxsystem.manage_own_corp"])
        own_corp = CorporationOwnerFactory(user=own_user)
        other_corp = CorporationOwnerFactory()
        other_alliance = AllianceOwnerFactory()
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])

        # Test Action
        own = General.objects.has_administration_owner_access(
            "corporation", own_user, own_corp
        )
        foreign = General.objects.has_administration_owner_access(
            "corporation", own_user, other_corp
        )
        admin_alliance = General.objects.has_administration_owner_access(
            "alliance", admin, other_alliance
        )
        corps_alliance = General.objects.has_administration_owner_access(
            "alliance", corps, other_alliance
        )
        invalid = General.objects.has_administration_owner_access(
            "unknown", admin, own_corp
        )

        # Expected Result
        self.assertTrue(own)
        self.assertFalse(foreign)
        self.assertTrue(admin_alliance)
        self.assertFalse(corps_alliance)
        self.assertFalse(invalid)

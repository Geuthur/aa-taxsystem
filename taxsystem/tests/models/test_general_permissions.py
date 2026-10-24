# Django
from django.contrib.auth.models import AnonymousUser

# AA TaxSystem
from taxsystem.models.general import General
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
    UserMainFactory,
)


class TestGeneralPermission(TaxSystemTestCase):
    def test_get_perm_should_return_full_permission_string_for_enum(self):
        # Test Data
        perm = General.Permission.MANAGE_CORPS

        # Test Action
        result = General.get_perm(perm)

        # Expected Result
        self.assertEqual(result, "taxsystem.manage_corps")

    def test_get_perm_should_return_full_permission_string_for_codename(self):
        # Test Data
        codename = "basic_access"

        # Test Action
        result = General.get_perm(codename)

        # Expected Result
        self.assertEqual(result, "taxsystem.basic_access")

    def test_permission_choices_should_keep_existing_codenames(self):
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

    def test_has_perm_should_return_false_for_none_and_anonymous(self):
        # Test Data
        perm = General.Permission.BASIC_ACCESS

        # Test Action
        none_result = General.has_perm(None, perm)
        anonymous_result = General.has_perm(AnonymousUser(), perm)

        # Expected Result
        self.assertFalse(none_result)
        self.assertFalse(anonymous_result)

    def test_has_perm_should_return_true_for_superuser(self):
        # Test Data
        perm = General.Permission.MANAGE_ALLIANCES

        # Test Action
        result = General.has_perm(self.superuser, perm)

        # Expected Result
        self.assertTrue(result)

    def test_has_perm_should_check_user_permission(self):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.manage_corps"])

        # Test Action
        with_perm = General.has_perm(user, General.Permission.MANAGE_CORPS)
        without_perm = General.has_perm(user, General.Permission.MANAGE_ALLIANCES)

        # Expected Result
        self.assertTrue(with_perm)
        self.assertFalse(without_perm)

    def test_has_any_perm_should_return_true_if_one_permission_matches(self):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.manage_own_corp"])

        # Test Action
        result = General.has_any_perm(
            user,
            General.Permission.MANAGE_CORPS,
            General.Permission.MANAGE_OWN_CORP,
        )

        # Expected Result
        self.assertTrue(result)

    def test_has_any_perm_should_return_false_without_matching_permission(self):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.basic_access"])

        # Test Action
        result = General.has_any_perm(
            user,
            General.Permission.MANAGE_CORPS,
            General.Permission.MANAGE_ALLIANCES,
        )

        # Expected Result
        self.assertFalse(result)

    def test_has_any_perm_should_return_false_for_none_and_anonymous(self):
        # Test Data
        perm = General.Permission.BASIC_ACCESS

        # Test Action
        none_result = General.has_any_perm(None, perm)
        anonymous_result = General.has_any_perm(AnonymousUser(), perm)

        # Expected Result
        self.assertFalse(none_result)
        self.assertFalse(anonymous_result)

    def test_has_administration_access_should_depend_on_five_permissions(self):
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
        results = {p: General.has_administration_access(u) for p, u in users.items()}

        # Expected Result
        self.assertTrue(all(results.values()))
        self.assertFalse(General.has_administration_access(basic))
        self.assertTrue(General.has_administration_access(self.superuser))
        self.assertFalse(General.has_administration_access(None))

    def test_has_administration_all_access_should_depend_on_owner_type(self):
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
                General.has_administration_all_access("corporation", user),
                General.has_administration_all_access("alliance", user),
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
        self.assertFalse(General.has_administration_all_access("unknown", admin))

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
        own_corps = General.get_administration_owners("corporation", own_user)
        own_alliances = General.get_administration_owners("alliance", own_user)
        all_corps = General.get_administration_owners("corporation", corps)
        all_alliances = General.get_administration_owners("alliance", alliances)
        no_corps = General.get_administration_owners("corporation", alliances)
        no_one = General.get_administration_owners("corporation", nobody)

        # Expected Result
        self.assertEqual(list(own_corps), [own_corp])
        self.assertEqual(list(own_alliances), [own_alliance])
        self.assertIn(other_corp, all_corps)
        self.assertIn(other_alliance, all_alliances)
        self.assertFalse(no_corps.exists())
        self.assertFalse(no_one.exists())
        with self.assertRaises(ValueError):
            General.get_administration_owners("unknown", corps)

    def test_has_administration_owner_access_should_decide_per_owner(self):
        # Test Data
        own_user = UserMainFactory(permissions__=["taxsystem.manage_own_corp"])
        own_corp = CorporationOwnerFactory(user=own_user)
        other_corp = CorporationOwnerFactory()
        other_alliance = AllianceOwnerFactory()
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])

        # Test Action
        own = General.has_administration_owner_access("corporation", own_user, own_corp)
        foreign = General.has_administration_owner_access(
            "corporation", own_user, other_corp
        )
        admin_alliance = General.has_administration_owner_access(
            "alliance", admin, other_alliance
        )
        corps_alliance = General.has_administration_owner_access(
            "alliance", corps, other_alliance
        )
        invalid = General.has_administration_owner_access("unknown", admin, own_corp)

        # Expected Result
        self.assertTrue(own)
        self.assertFalse(foreign)
        self.assertTrue(admin_alliance)
        self.assertFalse(corps_alliance)
        self.assertFalse(invalid)

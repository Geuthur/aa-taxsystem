# Django
from django.contrib.auth.models import AnonymousUser

# AA TaxSystem
from taxsystem.models.general import General
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import UserMainFactory


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

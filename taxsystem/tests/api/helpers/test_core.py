# Third Party
from evesde_factory.allianceauth import EveCharacterFactory
from evesde_factory.utils import add_character_to_user

# AA TaxSystem
from taxsystem.api.helpers import core, owner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
    UserMainFactory,
)


class TestCoreHelpers(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corporation = CorporationOwnerFactory(user=cls.user)
        cls.other_corporation = CorporationOwnerFactory()

    def _request(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_get_object_with_access_should_return_visible_object(self):
        # Test Action
        perms, obj = core.get_object_with_access(
            self._request(self.user), CorporationOwner.objects, pk=self.corporation.pk
        )

        # Expected Result
        self.assertTrue(perms)
        self.assertEqual(obj, self.corporation)

    def test_get_object_with_access_should_deny_manage_without_permission(self):
        # Test Action
        perms, obj = core.get_object_with_access(
            self._request(self.user),
            CorporationOwner.objects,
            manage=True,
            pk=self.corporation.pk,
        )

        # Expected Result
        self.assertFalse(perms)
        self.assertEqual(obj, self.corporation)

    def test_get_object_with_access_should_deny_foreign_object(self):
        # Test Action
        perms, obj = core.get_object_with_access(
            self._request(self.user),
            CorporationOwner.objects,
            pk=self.other_corporation.pk,
        )

        # Expected Result
        self.assertFalse(perms)
        self.assertEqual(obj, self.other_corporation)

    def test_get_object_with_access_should_return_none_for_missing_object(self):
        # Test Action
        perms, obj = core.get_object_with_access(
            self._request(self.user), CorporationOwner.objects, pk=999999
        )

        # Expected Result
        self.assertFalse(perms)
        self.assertIsNone(obj)

    def test_get_character_permissions_should_allow_own_character(self):
        # Test Data
        character = EveCharacterFactory()
        add_character_to_user(self.user, character)

        # Test Action / Expected Result
        self.assertTrue(
            core.get_character_permissions(
                self._request(self.user), character.character_id
            )
        )

    def test_get_character_permissions_should_deny_foreign_character(self):
        # Test Data
        character = EveCharacterFactory()

        # Test Action / Expected Result
        self.assertFalse(
            core.get_character_permissions(
                self._request(self.user), character.character_id
            )
        )


class TestOwnerHelpers(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corporation = CorporationOwnerFactory(user=cls.user)
        cls.alliance = AllianceOwnerFactory(user=cls.user)
        cls.manager = UserMainFactory(
            permissions__=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
                "taxsystem.manage_alliances",
            ]
        )

    def _request(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_get_owner_should_find_corporation(self):
        # Test Action
        perms, obj = owner.get_owner(self._request(self.user), self.corporation.eve_id)

        # Expected Result
        self.assertTrue(perms)
        self.assertEqual(obj, self.corporation)

    def test_get_owner_should_find_alliance(self):
        # Test Action
        perms, obj = owner.get_owner(self._request(self.user), self.alliance.eve_id)

        # Expected Result
        self.assertTrue(perms)
        self.assertEqual(obj, self.alliance)

    def test_get_owner_should_deny_manage_without_permission(self):
        # Test Action
        perms, obj = owner.get_owner(
            self._request(self.user), self.corporation.eve_id, manage=True
        )

        # Expected Result
        self.assertFalse(perms)
        self.assertEqual(obj, self.corporation)

    def test_get_owner_should_allow_manage_with_permission(self):
        # Test Action
        corp_perms, corp = owner.get_owner(
            self._request(self.manager), self.corporation.eve_id, manage=True
        )
        ally_perms, ally = owner.get_owner(
            self._request(self.manager), self.alliance.eve_id, manage=True
        )

        # Expected Result
        self.assertTrue(corp_perms)
        self.assertEqual(corp, self.corporation)
        self.assertTrue(ally_perms)
        self.assertEqual(ally, self.alliance)

    def test_get_owner_should_return_none_for_unknown_owner(self):
        # Test Action
        perms, obj = owner.get_owner(self._request(self.manager), 999999, manage=True)

        # Expected Result
        self.assertFalse(perms)
        self.assertIsNone(obj)

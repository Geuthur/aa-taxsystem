# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationOwnerFactory,
    EveCharacterFactory,
    MembersFactory,
)
from taxsystem.tests.testdata.utils import add_character_to_user

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestCorporationApiEndpoints(TaxSystemTestCase):
    """Test Corporation API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = CorporationOwnerFactory(user=cls.user)

    def test_get_members_should_403(self):
        """
        Test should return 403 Forbidden when user lacks permissions.
        """
        # Test Data
        corporation_id = self.user_character.corporation_id
        url = reverse(f"{API_URL}:get_members", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_members_should_404(self):
        """
        Test should return 404 Not Found when resource does not exist.
        """
        # Test Data
        url = reverse(f"{API_URL}:get_members", kwargs={"owner_id": 9999})
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_members_should_200(self):
        """
        Test should return 200 OK when user has permissions.

        Results:
        - Contains Test Character
        - Contains Missing Character
        """
        # Test Data
        corporation_id = self.user_character.corporation_id
        MembersFactory(
            owner=self.audit,
            character_name="Test Character",
            status="active",
        )
        MembersFactory(
            owner=self.audit,
            character_name="Missing Character",
            status="missing",
        )

        url = reverse(f"{API_URL}:get_members", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("Test Character", str(response.json()))
        self.assertIn("Missing Character", str(response.json()))

    def test_get_members_should_identify_alts_and_assign_to_main(self):
        """
        Test should correctly identify alt members and assign them to the main character.
        """
        # Test Data
        corporation_id = self.user_character.corporation_id
        main_member = MembersFactory(
            owner=self.audit,
            character_id=self.user_character.character_id,
            character_name=self.user_character.character_name,
            status="active",
        )
        alt_char = EveCharacterFactory(
            character_name="User Alt Character",
            corporation=self.corp,
        )
        add_character_to_user(
            user=self.user,
            character=alt_char,
            is_main=False,
        )
        alt_member = MembersFactory(
            owner=self.audit,
            character_id=alt_char.character_id,
            character_name=alt_char.character_name,
            status="is_alt",
        )

        url = reverse(f"{API_URL}:get_members", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        main_entry = next(
            (
                m
                for m in data
                if m["character"]["character_id"] == main_member.character_id
            ),
            None,
        )
        alt_entry = next(
            (
                m
                for m in data
                if m["character"]["character_id"] == alt_member.character_id
            ),
            None,
        )
        self.assertIsNotNone(main_entry)
        self.assertFalse(main_entry["is_alt"])
        self.assertTrue(len(main_entry["alts"]) > 0)
        self.assertEqual(main_entry["alts"][0]["character_id"], alt_char.character_id)

        self.assertIsNotNone(alt_entry)
        self.assertTrue(alt_entry["is_alt"])

    def test_delete_member_should_403(self):
        """
        Test should return 403 Forbidden when user lacks permissions.
        """
        # Test Data
        corporation_id = self.user_character.corporation_id
        member = MembersFactory(owner=self.audit)
        url = reverse(
            f"{API_URL}:delete_member",
            kwargs={"owner_id": corporation_id, "member_pk": member.pk},
        )
        data = {"comment": "Removing member for testing purposes."}
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(path=url, data=data)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_member_should_200(self):
        """
        Test should return 200 OK when user has permissions.

        Results:
        - Member is deleted
        """
        # Test Data
        corporation_id = self.user_character.corporation_id
        member = MembersFactory(
            owner=self.audit,
            status="missing",
        )
        url = reverse(
            f"{API_URL}:delete_member",
            kwargs={"owner_id": corporation_id, "member_pk": member.pk},
        )
        data = {"comment": "Removing member for testing purposes."}
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Member {member} deleted - {reason}".format(
            member=member.character_name, reason=data["comment"]
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(response.json().get("message"), result)

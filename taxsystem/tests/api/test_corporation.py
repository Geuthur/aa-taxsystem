# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import create_member, create_owner_from_user

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestCorporationApiEndpoints(TaxSystemTestCase):
    """Test Corporation API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(user=cls.user)

    def test_get_members_should_403(self):
        """
        Test should return 403 Forbidden when user lacks permissions.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id
        url = reverse(f"{API_URL}:get_members", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Excepted Result
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

        # Excepted Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_members_should_200(self):
        """
        Test should return 200 OK when user has permissions.

        Results:
        - Contains Test Character
        - Contains Missing Character
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id
        create_member(
            owner=self.audit,
            character_id=9999,
            character_name="Test Character",
            joined="2023-01-01",
            status="active",
        )
        create_member(
            owner=self.audit,
            character_id=10000,
            character_name="Missing Character",
            joined="2022-01-01",
            status="missing",
        )

        url = reverse(f"{API_URL}:get_members", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Excepted Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("Test Character", str(response.json()))
        self.assertIn("Missing Character", str(response.json()))

    def test_delete_member_should_403(self):
        """
        Test should return 403 Forbidden when user lacks permissions.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id
        member = create_member(
            owner=self.audit,
            character_id=9999,
            character_name="Test Character",
        )
        url = reverse(
            f"{API_URL}:delete_member",
            kwargs={"owner_id": corporation_id, "member_pk": member.pk},
        )
        data = {"comment": "Removing member for testing purposes."}
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(path=url, data=data)

        # Excepted Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_member_should_200(self):
        """
        Test should return 200 OK when user has permissions.

        Results:
        - Member is deleted
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id
        member = create_member(
            owner=self.audit,
            character_id=9999,
            character_name="Test Character",
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
            path=url, body=json.dumps(data), content_type="application/json"
        )
        print(json.loads(response.content))

        # Excepted Result
        result = "Member {member} deleted - {reason}".format(
            member=member.character_name, reason=data["comment"]
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(response.json().get("message"), result)

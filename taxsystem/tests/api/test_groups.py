# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationGroupFactory,
    CorporationOwnerFactory,
)

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestGroupApiEndpoints(TaxSystemTestCase):
    """Test Filter API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = CorporationOwnerFactory(user=cls.user)

    def test_get_filters(self):
        """
        Test 'api:get_filters' Endpoint.

        # Test Scenarios:
            1. Filters are returned successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        CorporationGroupFactory(
            owner=self.audit,
            name="Test Group",
        )

        url = reverse(
            f"{API_URL}:get_groups",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(data[0]["name"], "Test Group")

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:get_groups",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_group(self):
        """
        Test 'api:delete_group' Endpoint.

        # Test Scenarios:
            1. Group is deleted successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        group = CorporationGroupFactory(
            owner=self.audit,
            name="Test Group",
        )

        url = reverse(
            f"{API_URL}:delete_group",
            kwargs={"owner_id": self.audit.eve_id, "group_pk": group.pk},
        )
        self.client.force_login(self.superuser)
        data = {"comment": "Delete filter via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "{group} deleted - Reason: {reason}".format(
            group=group,
            reason=data["comment"],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:delete_group",
            kwargs={"owner_id": self.audit.eve_id, "group_pk": group.pk},
        )
        self.client.force_login(self.user)
        data = {"comment": "Delete filter via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

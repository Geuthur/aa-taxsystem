# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.models.corporation import CorporationFilter, CorporationFilterSet
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_filter,
    create_filterset,
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestFilterApiEndpoints(TaxSystemTestCase):
    """Test Filter API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(user=cls.user)

        cls.filterset = create_filterset(owner=cls.audit, name="Test FilterSet")

    def test_get_filters(self):
        """
        Test 'api:get_filters' Endpoint.

        # Test Scenarios:
            1. Filters are returned successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        create_filter(
            filter_set=self.filterset,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000,
        )

        url = reverse(
            f"{API_URL}:get_filters",
            kwargs={"owner_id": self.audit.eve_id, "filterset_pk": self.filterset.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(data[0]["value"]["raw"], "1000")
        self.assertEqual(data[0]["filter_type"], "Amount")

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:get_filters",
            kwargs={"owner_id": self.audit.eve_id, "filterset_pk": self.filterset.pk},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_filter(self):
        """
        Test 'api:delete_filter' Endpoint.

        # Test Scenarios:
            1. Filter is deleted successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        filter_instance = create_filter(
            filter_set=self.filterset,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=500,
        )

        url = reverse(
            f"{API_URL}:delete_filter",
            kwargs={"owner_id": self.audit.eve_id, "filter_pk": filter_instance.pk},
        )
        self.client.force_login(self.superuser)
        data = {"comment": "Delete filter via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = '{filter_obj} in "{filter_set}" deleted - Reason: {reason}'.format(
            filter_obj=filter_instance,
            filter_set=self.filterset.name,
            reason=data["comment"],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:delete_filter",
            kwargs={"owner_id": self.audit.eve_id, "filter_pk": filter_instance.pk},
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

    def test_get_filter_set(self):
        """
        Test 'api:get_filter_set' Endpoint.

        # Test Scenarios:
            1. Filter Sets are returned successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_filter_set", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(data[0]["name"], self.filterset.name)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:get_filter_set", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_filter_set(self):
        """
        Test 'api:delete_filter_set' Endpoint.

        # Test Scenarios:
            1. Filter Set is deleted successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:delete_filter_set",
            kwargs={"owner_id": self.audit.eve_id, "filterset_pk": self.filterset.pk},
        )
        self.client.force_login(self.superuser)
        data = {"comment": "Delete filter set via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "{filter_set} deleted - Reason: {reason}".format(
            filter_set=self.filterset, reason=data["comment"]
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:delete_filter_set",
            kwargs={"owner_id": self.audit.eve_id, "filterset_pk": self.filterset.pk},
        )
        self.client.force_login(self.user)
        data = {"comment": "Delete filter set via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_switch_filter_set(self):
        """
        Test 'api:switch_filter_set' Endpoint.

        # Test Scenarios:
            1. Filter Set is switched successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:switch_filter_set",
            kwargs={"owner_id": self.audit.eve_id, "filterset_pk": self.filterset.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(path=url)

        # Expected Result
        filter_set = CorporationFilterSet.objects.get(pk=self.filterset.pk)
        result = "{filter_set} switched to {enabled}".format(
            filter_set=filter_set, enabled=filter_set.enabled
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:switch_filter_set",
            kwargs={"owner_id": self.audit.eve_id, "filterset_pk": self.filterset.pk},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(path=url)

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

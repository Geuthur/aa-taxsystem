"""Owner access of one endpoint per API module: allowed, denied, unknown owner."""

# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import CorporationOwnerFactory, UserMainFactory

API_URL = "taxsystem:api"
UNKNOWN_OWNER_ID = 999999

# Endpoints that need manage access to the owner (module: url name)
MANAGE_ENDPOINTS = {
    "admin": "get_dashboard",
    "corporation": "get_members",
    "filters": "get_filter_set",
    "groups": "get_groups",
    "logs": "get_admin_history",
}


class TestOwnerAccess(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corporation = CorporationOwnerFactory(user=cls.user)
        cls.stranger = UserMainFactory()

    def _get(self, user, name: str, owner_id: int):
        self.client.force_login(user)
        return self.client.get(
            reverse(f"{API_URL}:{name}", kwargs={"owner_id": owner_id})
        )

    def test_manage_endpoints_should_200_for_manager(self):
        for module, name in MANAGE_ENDPOINTS.items():
            with self.subTest(module=module):
                response = self._get(self.superuser, name, self.corporation.eve_id)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_manage_endpoints_should_403_without_manage_access(self):
        for module, name in MANAGE_ENDPOINTS.items():
            with self.subTest(module=module):
                response = self._get(self.user, name, self.corporation.eve_id)
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                self.assertEqual(response.json(), {"error": "Permission Denied."})

    def test_manage_endpoints_should_404_for_unknown_owner(self):
        for module, name in MANAGE_ENDPOINTS.items():
            with self.subTest(module=module):
                response = self._get(self.superuser, name, UNKNOWN_OWNER_ID)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertEqual(response.json(), {"error": "Owner not Found."})

    def test_get_payments_should_200_for_member(self):
        # Test Action
        response = self._get(self.user, "get_payments", self.corporation.eve_id)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_payments_should_403_for_stranger(self):
        # Test Action
        response = self._get(self.stranger, "get_payments", self.corporation.eve_id)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json(), {"error": "Permission Denied."})

    def test_get_payments_should_404_for_unknown_owner(self):
        # Test Action
        response = self._get(self.user, "get_payments", UNKNOWN_OWNER_ID)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response.json(), {"error": "Owner not Found."})

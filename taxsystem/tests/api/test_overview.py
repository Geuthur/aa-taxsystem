# Standard Library
from http import HTTPStatus

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationOwnerFactory,
    UserMainFactory,
)


class TestOverviewApi(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = "/taxsystem/api"
        cls.audit = CorporationOwnerFactory(user=cls.user)

    def test_get_overview_should_return_visible_owners(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("owners", data)
        self.assertGreaterEqual(data["total_count"], 1)
        owner_ids = [o["id"] for o in data["owners"]]
        self.assertIn(self.audit.eve_corporation.corporation_id, owner_ids)

    def test_get_overview_should_return_403_without_basic_access(self):
        # Test Data
        no_access_user = UserMainFactory()
        no_access_user.user_permissions.clear()
        self.client.force_login(no_access_user)

        # Test Action
        response = self.client.get(f"{self.api}/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

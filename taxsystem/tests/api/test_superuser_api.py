# Standard Library
import json
from http import HTTPStatus
from unittest.mock import patch

# AA TaxSystem
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
)

TASKS_PATH = "taxsystem.tasks"


class TestSuperuserApi(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = "/taxsystem/api"

    def setUp(self):
        super().setUp()
        self.corp_owner = CorporationOwnerFactory(user=self.superuser)
        self.alliance_owner = AllianceOwnerFactory(user=self.superuser)

    def test_list_superuser_owners_should_return_all_owners_for_superuser(self):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner_ids = [item["owner_id"] for item in data]
        self.assertIn(self.corp_owner.eve_id, owner_ids)
        self.assertIn(self.alliance_owner.eve_id, owner_ids)

    def test_list_superuser_owners_should_return_403_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_superuser_owner_should_trigger_corp_update(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)
        url = (
            f"{self.api}/superuser/owners/corporation/{self.corp_owner.eve_id}/update/"
        )

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": True}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    @patch(f"{TASKS_PATH}.update_alliance.apply_async")
    def test_update_superuser_owner_should_trigger_alliance_update(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)
        url = (
            f"{self.api}/superuser/owners/alliance/{self.alliance_owner.eve_id}/update/"
        )

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    def test_update_superuser_owner_should_return_404_if_not_found(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/superuser/owners/corporation/99999999/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_update_superuser_owner_should_return_400_for_invalid_type(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/superuser/owners/unknown/123/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_delete_superuser_owner_should_delete_corporation(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/superuser/owners/corporation/{self.corp_owner.eve_id}/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            CorporationOwner.objects.filter(
                eve_corporation__corporation_id=self.corp_owner.eve_id
            ).exists()
        )

    def test_delete_superuser_owner_should_delete_alliance(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/superuser/owners/alliance/{self.alliance_owner.eve_id}/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            AllianceOwner.objects.filter(
                eve_alliance__alliance_id=self.alliance_owner.eve_id
            ).exists()
        )

    def test_delete_superuser_owner_should_return_404_if_not_found(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/superuser/owners/corporation/99999999/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_inspect_superuser_owner_should_return_dashboard_for_corporation(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = (
            f"{self.api}/superuser/owners/corporation/{self.corp_owner.eve_id}/inspect/"
        )

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["owner"]["owner_name"], self.corp_owner.name)

    def test_inspect_superuser_owner_should_return_dashboard_for_alliance(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/superuser/owners/alliance/{self.alliance_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json()["owner"]["owner_name"], self.alliance_owner.name
        )

    def test_inspect_superuser_owner_should_return_403_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)
        url = (
            f"{self.api}/superuser/owners/corporation/{self.corp_owner.eve_id}/inspect/"
        )

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

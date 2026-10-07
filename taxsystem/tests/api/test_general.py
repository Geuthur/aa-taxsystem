# Standard Library
import json
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.models.general import UserSettings
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationOwnerFactory,
    CorporationTaxAccountFactory,
    UserMainFactory,
)

TASKS_PATH = "taxsystem.tasks"


class TestGeneralApi(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = "/taxsystem/api"

    def test_get_menu_should_return_menu_links_for_standard_user(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        left_links = [link["link"] for link in response.json()["left_links"]]
        self.assertEqual(left_links, ["/", "/account/", "/settings/"])
        right_links = [link["link"] for link in response.json()["right_links"]]
        self.assertEqual(right_links, [])

    def test_get_menu_should_include_admin_and_add_links_for_superuser(self):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        right_links = [link["link"] for link in data["right_links"]]
        self.assertIn(reverse("taxsystem:add_corp"), right_links)
        self.assertIn(reverse("taxsystem:add_alliance"), right_links)
        self.assertIn("/admin/", right_links)

    def test_get_menu_should_return_403_without_basic_access(self):
        # Test Data
        no_access_user = UserMainFactory()
        no_access_user.user_permissions.clear()
        self.client.force_login(no_access_user)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_user_should_return_user_data(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/user/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["user_id"], self.user.id)
        self.assertEqual(
            data["character_name"], self.user.profile.main_character.character_name
        )
        self.assertFalse(data["is_admin"])

    def test_get_user_accounts_should_return_accounts_for_user(self):
        # Test Data
        corp_owner = CorporationOwnerFactory()
        tax_account = CorporationTaxAccountFactory(
            owner=corp_owner,
            user=self.user,
            name=self.user.username,
            deposit=5000000,
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/user/accounts/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], tax_account.pk)
        self.assertEqual(data[0]["deposit"], 5000000.0)
        self.assertEqual(
            data[0]["owner_name"], corp_owner.eve_corporation.corporation_name
        )

    def test_get_settings_should_return_user_settings(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/settings/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("disable_notifications", data)

    def test_update_settings_should_save_user_settings(self):
        # Test Data
        self.client.force_login(self.user)
        payload = {"disable_notifications": True}

        # Test Action
        response = self.client.put(
            f"{self.api}/settings/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.json()["disable_notifications"])
        settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings.disable_notifications)

    @patch(f"{TASKS_PATH}.update_all_taxsytem.apply_async")
    def test_run_admin_tasks_should_queue_all_for_superuser(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)
        payload = {"target": "all", "force_refresh": True}

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/tasks/run/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    def test_run_admin_tasks_should_return_403_for_non_superuser(self):
        # Test Data
        self.client.force_login(self.user)
        payload = {"target": "all", "force_refresh": False}

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/tasks/run/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

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
    EveCorporationInfoFactory,
    UserMainFactory,
)

TASKS_PATH = "taxsystem.tasks"


class TestAdministrationApi(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = "/taxsystem/api"

    def setUp(self):
        super().setUp()
        self.corp_owner = CorporationOwnerFactory(user=self.superuser)
        self.alliance_owner = AllianceOwnerFactory(user=self.superuser)

    def test_list_administration_owners_should_return_all_owners_for_superuser(self):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(f"{self.api}/administration/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner_ids = [item["owner_id"] for item in data]
        self.assertIn(self.corp_owner.eve_id, owner_ids)
        self.assertIn(self.alliance_owner.eve_id, owner_ids)

    def test_list_administration_owners_should_return_403_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/administration/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_trigger_corp_update(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/update/"

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
    def test_update_administration_owner_should_trigger_alliance_update(
        self, mock_task
    ):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/alliance/{self.alliance_owner.eve_id}/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    def test_update_administration_owner_should_return_404_if_not_found(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/corporation/99999999/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_update_administration_owner_should_return_400_for_invalid_type(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/unknown/123/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_delete_administration_owner_should_delete_corporation(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            CorporationOwner.objects.filter(
                eve_corporation__corporation_id=self.corp_owner.eve_id
            ).exists()
        )

    def test_delete_administration_owner_should_delete_alliance(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/alliance/{self.alliance_owner.eve_id}/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            AllianceOwner.objects.filter(
                eve_alliance__alliance_id=self.alliance_owner.eve_id
            ).exists()
        )

    def test_delete_administration_owner_should_return_404_if_not_found(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/corporation/99999999/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_inspect_administration_owner_should_return_dashboard_for_corporation(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["owner"]["owner_name"], self.corp_owner.name)

    def test_inspect_administration_owner_should_return_dashboard_for_alliance(self):
        # Test Data
        self.client.force_login(self.superuser)
        url = f"{self.api}/administration/owners/alliance/{self.alliance_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json()["owner"]["owner_name"], self.alliance_owner.name
        )

    def test_inspect_administration_owner_should_return_403_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_list_administration_owners_should_return_all_owners_for_admin_access(
        self,
    ):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)

        # Test Action
        response = self.client.get(f"{self.api}/administration/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            {(item["owner_type"], item["owner_id"]) for item in data},
            {
                ("corporation", self.corp_owner.eve_id),
                ("alliance", self.alliance_owner.eve_id),
            },
        )

    def test_list_administration_owners_should_exclude_npc_corporations(self):
        # Test Data
        npc_owner = CorporationOwnerFactory(
            eve_corporation=EveCorporationInfoFactory(
                corporation_id=1_000_125, create_alliance=False
            )
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(f"{self.api}/administration/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        owner_ids = [item["owner_id"] for item in response.json()]
        self.assertIn(self.corp_owner.eve_id, owner_ids)
        self.assertNotIn(npc_owner.eve_id, owner_ids)

    def test_administration_owner_endpoints_should_return_404_for_npc_corporation(
        self,
    ):
        # Test Data
        npc_owner = CorporationOwnerFactory(
            eve_corporation=EveCorporationInfoFactory(
                corporation_id=1_000_125, create_alliance=False
            )
        )
        self.client.force_login(self.superuser)
        base = f"{self.api}/administration/owners/corporation/{npc_owner.eve_id}/"

        # Test Action
        inspect_response = self.client.get(f"{base}inspect/")
        update_response = self.client.post(
            f"{base}update/",
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )
        delete_response = self.client.delete(base)

        # Expected Result
        self.assertEqual(inspect_response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(update_response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(delete_response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(CorporationOwner.objects.filter(pk=npc_owner.pk).exists())

    def test_list_administration_owners_should_return_403_for_manage_permissions(
        self,
    ):
        # Test Data
        manager = UserMainFactory(
            permissions__=[
                "taxsystem.manage_corps",
                "taxsystem.manage_alliances",
                "taxsystem.manage_own_corp",
                "taxsystem.manage_own_alliance",
            ]
        )
        self.client.force_login(manager)

        # Test Action
        response = self.client.get(f"{self.api}/administration/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_allow_admin_access_without_force(
        self, mock_task
    ):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    @patch(f"{TASKS_PATH}.update_alliance.apply_async")
    def test_update_administration_owner_should_allow_admin_access_for_alliance(
        self, mock_task
    ):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)
        url = f"{self.api}/administration/owners/alliance/{self.alliance_owner.eve_id}/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_return_403_on_force_refresh_for_admin_access(
        self, mock_task
    ):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": True}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(mock_task.called)

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_return_403_for_manage_corps(
        self, mock_task
    ):
        # Test Data
        manager = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        self.client.force_login(manager)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/update/"

        # Test Action
        response = self.client.post(
            url,
            data=json.dumps({"force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(mock_task.called)

    def test_delete_administration_owner_should_allow_admin_access_for_alliance(self):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)
        url = f"{self.api}/administration/owners/alliance/{self.alliance_owner.eve_id}/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            AllianceOwner.objects.filter(
                eve_alliance__alliance_id=self.alliance_owner.eve_id
            ).exists()
        )

    def test_delete_administration_owner_should_return_403_for_manage_alliances(self):
        # Test Data
        manager = UserMainFactory(permissions__=["taxsystem.manage_alliances"])
        self.client.force_login(manager)
        url = f"{self.api}/administration/owners/alliance/{self.alliance_owner.eve_id}/"

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(
            AllianceOwner.objects.filter(
                eve_alliance__alliance_id=self.alliance_owner.eve_id
            ).exists()
        )

    def test_inspect_administration_owner_should_allow_admin_access(self):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_inspect_administration_owner_should_return_403_for_manage_corps(self):
        # Test Data
        manager = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        self.client.force_login(manager)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASKS_PATH}.update_all_taxsytem.apply_async")
    def test_run_update_tasks_should_return_403_for_admin_access(self, mock_task):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/tasks/run/",
            data=json.dumps({"target": "all", "force_refresh": False}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(mock_task.called)

    @patch(f"{TASKS_PATH}.update_all_taxsytem.apply_async")
    def test_run_update_tasks_should_queue_for_superuser(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/tasks/run/",
            data=json.dumps({"target": "all", "force_refresh": True}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_trigger_owner_update_should_return_403_on_force_refresh_for_manager(
        self, mock_task
    ):
        # Test Data
        manager = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        self.client.force_login(manager)

        # Test Action
        response = self.client.post(
            f"{self.api}/owner/{self.corp_owner.eve_id}/update/",
            data=json.dumps({"force_refresh": True}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(mock_task.called)

    def test_get_menu_should_show_administration_link_for_admin_access(self):
        # Test Data
        admin = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.admin_access"]
        )
        self.client.force_login(admin)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        links = [link["link"] for link in response.json()["right_links"]]
        self.assertIn("/administration/", links)

    def test_get_menu_should_hide_administration_link_for_manage_permissions(self):
        # Test Data
        manager = UserMainFactory(
            permissions__=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
                "taxsystem.manage_alliances",
            ]
        )
        self.client.force_login(manager)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        links = [link["link"] for link in response.json()["right_links"]]
        self.assertNotIn("/administration/", links)

    def test_get_menu_should_hide_administration_link_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        links = [link["link"] for link in response.json()["right_links"]]
        self.assertNotIn("/administration/", links)

    def test_get_user_should_flag_superuser_and_admin(self):
        # Test Data
        admin = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.admin_access"]
        )
        manager = UserMainFactory(
            permissions__=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
                "taxsystem.manage_alliances",
            ]
        )

        # Test Action
        self.client.force_login(admin)
        admin_data = self.client.get(f"{self.api}/user/").json()
        self.client.force_login(manager)
        manager_data = self.client.get(f"{self.api}/user/").json()
        self.client.force_login(self.superuser)
        superuser_data = self.client.get(f"{self.api}/user/").json()

        # Expected Result
        self.assertTrue(admin_data["is_admin"])
        self.assertFalse(admin_data["is_superuser"])
        self.assertFalse(manager_data["is_admin"])
        self.assertTrue(superuser_data["is_admin"])
        self.assertTrue(superuser_data["is_superuser"])

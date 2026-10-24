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

    def test_inspect_administration_owner_should_allow_admin_access(self):
        # Test Data
        admin = UserMainFactory(permissions__=["taxsystem.admin_access"])
        self.client.force_login(admin)
        url = f"{self.api}/administration/owners/corporation/{self.corp_owner.eve_id}/inspect/"

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

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

    def test_get_menu_should_hide_administration_link_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        links = [link["link"] for link in response.json()["right_links"]]
        self.assertNotIn("/administration/", links)

    def _owner_keys(self, user):
        self.client.force_login(user)
        response = self.client.get(f"{self.api}/administration/owners/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        return {(item["owner_type"], item["owner_id"]) for item in response.json()}

    def test_list_administration_owners_should_return_only_corporations_for_manage_corps(
        self,
    ):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.manage_corps"])

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertEqual(keys, {("corporation", self.corp_owner.eve_id)})

    def test_list_administration_owners_should_return_only_alliances_for_manage_alliances(
        self,
    ):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.manage_alliances"])

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertEqual(keys, {("alliance", self.alliance_owner.eve_id)})

    def test_list_administration_owners_should_return_both_for_both_manage_permissions(
        self,
    ):
        # Test Data
        user = UserMainFactory(
            permissions__=["taxsystem.manage_corps", "taxsystem.manage_alliances"]
        )

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertEqual(
            keys,
            {
                ("corporation", self.corp_owner.eve_id),
                ("alliance", self.alliance_owner.eve_id),
            },
        )

    def test_list_administration_owners_should_exclude_npc_corporations_for_manage_corps(
        self,
    ):
        # Test Data
        npc_owner = CorporationOwnerFactory(
            eve_corporation=EveCorporationInfoFactory(
                corporation_id=1_000_125, create_alliance=False
            )
        )
        user = UserMainFactory(permissions__=["taxsystem.manage_corps"])

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertNotIn(("corporation", npc_owner.eve_id), keys)
        self.assertIn(("corporation", self.corp_owner.eve_id), keys)

    def _call(self, user, method, owner_type, owner_id, suffix="", force=False):
        self.client.force_login(user)
        url = f"{self.api}/administration/owners/{owner_type}/{owner_id}/{suffix}"
        if method == "post":
            return self.client.post(
                url,
                data=json.dumps({"force_refresh": force}),
                content_type="application/json",
            )
        return getattr(self.client, method)(url)

    @patch(f"{TASKS_PATH}.update_alliance.apply_async")
    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_respect_owner_type_permission(
        self, mock_corp, mock_alliance
    ):
        # Test Data
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        alliances = UserMainFactory(permissions__=["taxsystem.manage_alliances"])
        corp_id = self.corp_owner.eve_id
        alliance_id = self.alliance_owner.eve_id

        # Test Action
        corps_on_corp = self._call(corps, "post", "corporation", corp_id, "update/")
        corps_on_alliance = self._call(
            corps, "post", "alliance", alliance_id, "update/"
        )
        alliances_on_corp = self._call(
            alliances, "post", "corporation", corp_id, "update/"
        )
        alliances_on_alliance = self._call(
            alliances, "post", "alliance", alliance_id, "update/"
        )

        # Expected Result
        self.assertEqual(corps_on_corp.status_code, HTTPStatus.OK)
        self.assertEqual(corps_on_alliance.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(alliances_on_corp.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(alliances_on_alliance.status_code, HTTPStatus.OK)
        self.assertEqual(mock_corp.call_count, 1)
        self.assertEqual(mock_alliance.call_count, 1)

    @patch(f"{TASKS_PATH}.update_alliance.apply_async")
    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_return_403_on_force_refresh_for_manage_permissions(
        self, mock_corp, mock_alliance
    ):
        # Test Data
        user = UserMainFactory(
            permissions__=["taxsystem.manage_corps", "taxsystem.manage_alliances"]
        )

        # Test Action
        corp = self._call(
            user, "post", "corporation", self.corp_owner.eve_id, "update/", force=True
        )
        alliance = self._call(
            user, "post", "alliance", self.alliance_owner.eve_id, "update/", force=True
        )

        # Expected Result
        self.assertEqual(corp.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(alliance.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(mock_corp.called)
        self.assertFalse(mock_alliance.called)

    def test_delete_administration_owner_should_respect_owner_type_permission(self):
        # Test Data
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        alliances = UserMainFactory(permissions__=["taxsystem.manage_alliances"])
        corp_id = self.corp_owner.eve_id
        alliance_id = self.alliance_owner.eve_id

        # Test Action
        corps_on_alliance = self._call(corps, "delete", "alliance", alliance_id)
        alliances_on_corp = self._call(alliances, "delete", "corporation", corp_id)
        alliances_on_alliance = self._call(alliances, "delete", "alliance", alliance_id)
        corps_on_corp = self._call(corps, "delete", "corporation", corp_id)

        # Expected Result
        self.assertEqual(corps_on_alliance.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(alliances_on_corp.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(corps_on_corp.status_code, HTTPStatus.OK)
        self.assertEqual(alliances_on_alliance.status_code, HTTPStatus.OK)
        self.assertFalse(
            AllianceOwner.objects.filter(pk=self.alliance_owner.pk).exists()
        )

    def test_inspect_administration_owner_should_respect_owner_type_permission(self):
        # Test Data
        corps = UserMainFactory(permissions__=["taxsystem.manage_corps"])
        alliances = UserMainFactory(permissions__=["taxsystem.manage_alliances"])
        corp_id = self.corp_owner.eve_id
        alliance_id = self.alliance_owner.eve_id

        # Test Action
        corps_on_corp = self._call(corps, "get", "corporation", corp_id, "inspect/")
        corps_on_alliance = self._call(
            corps, "get", "alliance", alliance_id, "inspect/"
        )
        alliances_on_corp = self._call(
            alliances, "get", "corporation", corp_id, "inspect/"
        )
        alliances_on_alliance = self._call(
            alliances, "get", "alliance", alliance_id, "inspect/"
        )

        # Expected Result
        self.assertEqual(corps_on_corp.status_code, HTTPStatus.OK)
        self.assertEqual(corps_on_alliance.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(alliances_on_corp.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(alliances_on_alliance.status_code, HTTPStatus.OK)

    def test_administration_owner_endpoints_should_return_404_for_npc_corporation_with_manage_corps(
        self,
    ):
        # Test Data
        npc_owner = CorporationOwnerFactory(
            eve_corporation=EveCorporationInfoFactory(
                corporation_id=1_000_125, create_alliance=False
            )
        )
        user = UserMainFactory(permissions__=["taxsystem.manage_corps"])

        # Test Action
        inspect = self._call(user, "get", "corporation", npc_owner.eve_id, "inspect/")
        delete = self._call(user, "delete", "corporation", npc_owner.eve_id)

        # Expected Result
        self.assertEqual(inspect.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(delete.status_code, HTTPStatus.NOT_FOUND)

    def _menu_links(self, user):
        self.client.force_login(user)
        response = self.client.get(f"{self.api}/menu/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        return [link["link"] for link in response.json()["right_links"]]

    def test_get_menu_should_show_administration_link_for_manage_corps_or_alliances(
        self,
    ):
        # Test Data
        corps = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.manage_corps"]
        )
        alliances = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.manage_alliances"]
        )

        # Test Action
        corps_links = self._menu_links(corps)
        alliances_links = self._menu_links(alliances)

        # Expected Result
        self.assertIn("/administration/", corps_links)
        self.assertIn("/administration/", alliances_links)

    def test_get_user_should_flag_is_admin_per_permission(self):
        # Test Data
        base = "taxsystem.basic_access"
        cases = {
            "taxsystem.admin_access": True,
            "taxsystem.manage_corps": True,
            "taxsystem.manage_alliances": True,
            "taxsystem.manage_own_corp": True,
            "taxsystem.manage_own_alliance": True,
        }

        # Test Action
        results = {}
        for perm in cases:
            self.client.force_login(UserMainFactory(permissions__=[base, perm]))
            data = self.client.get(f"{self.api}/user/").json()
            results[perm] = (data["is_admin"], data["is_superuser"])
        self.client.force_login(self.superuser)
        superuser_data = self.client.get(f"{self.api}/user/").json()

        # Expected Result
        for perm, expected in cases.items():
            self.assertEqual(results[perm], (expected, False), perm)
        self.assertTrue(superuser_data["is_admin"])
        self.assertTrue(superuser_data["is_superuser"])

    def _own_user(self, *permissions):
        user = UserMainFactory(permissions__=list(permissions))
        own_corp = CorporationOwnerFactory(user=user)
        own_alliance = AllianceOwnerFactory(user=user)
        return user, own_corp, own_alliance

    def test_list_administration_owners_should_return_only_own_corporation_for_manage_own_corp(
        self,
    ):
        # Test Data
        user, own_corp, _own_alliance = self._own_user("taxsystem.manage_own_corp")

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertEqual(keys, {("corporation", own_corp.eve_id)})

    def test_list_administration_owners_should_return_only_own_alliance_for_manage_own_alliance(
        self,
    ):
        # Test Data
        user, _own_corp, own_alliance = self._own_user("taxsystem.manage_own_alliance")

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertEqual(keys, {("alliance", own_alliance.eve_id)})

    def test_list_administration_owners_should_combine_own_and_all_permissions(self):
        # Test Data
        user, own_corp, _own_alliance = self._own_user(
            "taxsystem.manage_own_corp", "taxsystem.manage_alliances"
        )

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertIn(("corporation", own_corp.eve_id), keys)
        self.assertNotIn(("corporation", self.corp_owner.eve_id), keys)
        self.assertIn(("alliance", self.alliance_owner.eve_id), keys)

    def test_list_administration_owners_should_return_both_own_for_both_own_permissions(
        self,
    ):
        # Test Data
        user, own_corp, own_alliance = self._own_user(
            "taxsystem.manage_own_corp", "taxsystem.manage_own_alliance"
        )

        # Test Action
        keys = self._owner_keys(user)

        # Expected Result
        self.assertEqual(
            keys,
            {
                ("corporation", own_corp.eve_id),
                ("alliance", own_alliance.eve_id),
            },
        )

    @patch(f"{TASKS_PATH}.update_alliance.apply_async")
    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_administration_owner_endpoints_should_only_allow_own_owner_for_manage_own(
        self, mock_corp, mock_alliance
    ):
        # Test Data
        user, own_corp, own_alliance = self._own_user(
            "taxsystem.manage_own_corp", "taxsystem.manage_own_alliance"
        )
        foreign_corp = self.corp_owner.eve_id
        foreign_alliance = self.alliance_owner.eve_id

        # Test Action
        own_inspect = self._call(
            user, "get", "corporation", own_corp.eve_id, "inspect/"
        )
        own_update = self._call(user, "post", "corporation", own_corp.eve_id, "update/")
        own_ally_update = self._call(
            user, "post", "alliance", own_alliance.eve_id, "update/"
        )
        foreign_inspect = self._call(
            user, "get", "corporation", foreign_corp, "inspect/"
        )
        foreign_update = self._call(
            user, "post", "corporation", foreign_corp, "update/"
        )
        foreign_delete = self._call(user, "delete", "corporation", foreign_corp)
        foreign_ally_inspect = self._call(
            user, "get", "alliance", foreign_alliance, "inspect/"
        )
        foreign_ally_delete = self._call(user, "delete", "alliance", foreign_alliance)

        # Expected Result
        self.assertEqual(own_inspect.status_code, HTTPStatus.OK)
        self.assertEqual(own_update.status_code, HTTPStatus.OK)
        self.assertEqual(own_ally_update.status_code, HTTPStatus.OK)
        self.assertEqual(foreign_inspect.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(foreign_update.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(foreign_delete.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(foreign_ally_inspect.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(foreign_ally_delete.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(mock_corp.call_count, 1)
        self.assertEqual(mock_alliance.call_count, 1)
        self.assertTrue(CorporationOwner.objects.filter(pk=self.corp_owner.pk).exists())

    @patch(f"{TASKS_PATH}.update_corporation.apply_async")
    def test_update_administration_owner_should_return_403_on_force_refresh_for_manage_own_corp(
        self, mock_task
    ):
        # Test Data
        user, own_corp, _own_alliance = self._own_user("taxsystem.manage_own_corp")

        # Test Action
        response = self._call(
            user, "post", "corporation", own_corp.eve_id, "update/", force=True
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(mock_task.called)

    def test_get_menu_should_show_administration_link_for_manage_own_permissions(self):
        # Test Data
        corp_user = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.manage_own_corp"]
        )
        alliance_user = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.manage_own_alliance"]
        )

        # Test Action
        corp_links = self._menu_links(corp_user)
        alliance_links = self._menu_links(alliance_user)

        # Expected Result
        self.assertIn("/administration/", corp_links)
        self.assertIn("/administration/", alliance_links)

    def test_administration_should_return_403_and_hide_menu_without_manage_permissions(
        self,
    ):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.basic_access"])

        # Test Action
        links = self._menu_links(user)
        response = self.client.get(f"{self.api}/administration/owners/")

        # Expected Result
        self.assertNotIn("/administration/", links)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

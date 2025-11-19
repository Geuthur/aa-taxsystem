# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA TaxSystem
from taxsystem.api.admin import AdminApiEndpoints
from taxsystem.models.corporation import CorporationFilter
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    add_owneraudit_character_to_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestCoreHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.api = NinjaAPI()
        cls.admin_endpoint = AdminApiEndpoints(cls.api)

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
            ],
        )
        cls.audit = add_owneraudit_character_to_user(user=cls.user, character_id=1001)
        cls.no_evecharacter_user = UserMainFactory(permissions=[])

        cls.filter_set = create_filterset(
            owner=cls.audit,
            name="100m",
            description="Filter for payments over 100m",
        )

        cls.filter_amount = create_filter(
            filter_set=cls.filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=100_000_000,
        )

    def test_get_dashboard_access(self):
        """Test should be able to access dashboard API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_dashboard", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_dashboard_without_access(self):
        """Test should not be able to access dashboard API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_dashboard", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_members_access(self):
        """Test should be able to access members API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_members", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_members_without_access(self):
        """Test should not be able to access members API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_members", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_paymentsystem_access(self):
        """Test should be able to access paymentsystem API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_paymentsystem", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_paymentsystem_without_access(self):
        """Test should not be able to access paymentsystem API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_paymentsystem", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_corporation_admin_logs_access(self):
        """Test should be able to access corporation admin logs API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_corporation_admin_logs",
            kwargs={"corporation_id": corporation_id},
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_corporation_admin_logs_without_access(self):
        """Test should not be able to access corporation admin logs API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_corporation_admin_logs",
            kwargs={"corporation_id": corporation_id},
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_filter_set_filters_access(self):
        """Test should be able to access filters set filters API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        filter_set_id = self.filter_set.pk
        url = reverse(
            f"{API_URL}:get_filter_set_filters",
            kwargs={"corporation_id": corporation_id, "filter_set_id": filter_set_id},
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_filter_set_filters_without_access(self):
        """Test should not be able to access filters set filters API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        filter_set_id = self.filter_set.pk
        url = reverse(
            f"{API_URL}:get_filter_set_filters",
            kwargs={"corporation_id": corporation_id, "filter_set_id": filter_set_id},
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

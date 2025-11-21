# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA TaxSystem
from taxsystem.api.character import CharacterApiEndpoints
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationPaymentAccount,
    CorporationPayments,
)
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import (
    add_owneraudit_character_to_user,
    create_user_from_evecharacter_with_access,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment,
    create_payment_system,
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
        cls.character_endpoint = CharacterApiEndpoints(cls.api)
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
            ],
        )
        cls.audit = add_owneraudit_character_to_user(user=cls.user, character_id=1001)
        cls.user_no_payments, cls.character_ownership_no_payments = (
            create_user_from_evecharacter_with_access(1004)
        )
        cls.no_evecharacter_user = UserMainFactory(permissions=[])

        cls.payment_system = create_payment_system(
            name=cls.character_ownership.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        cls.payments = create_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            owner_id=cls.character_ownership.character.corporation_id,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=CorporationPayments.RequestStatus.PENDING,
            reviser="",
        )

        cls.payments2 = create_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            owner_id=cls.character_ownership.character.corporation_id,
            entry_id=2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Mining Stuff",
            request_status=CorporationPayments.RequestStatus.PENDING,
            reviser="",
        )

        cls.filter_set = create_filterset(
            owner=cls.audit,
            name="100m",
            description="Filter for payments over 100m",
        )

        cls.filter_amount = create_filter(
            filter_set=cls.filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000,
        )

    def test_get_payments_access(self):
        """Test should be able to access payments API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_payments", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = response.json()
        self.assertIn("owner", response_data)
        self.assertEqual(len(response_data["owner"]), 2)

    def test_get_payments_without_access(self):
        """Test should not be able to access payments API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_payments", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_own_payments_access(self):
        """Test should be able to access own payments API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_own_payments", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = response.json()
        self.assertIn("owner", response_data)
        self.assertEqual(len(response_data["owner"]), 2)

    def test_get_own_payments_no_payments(self):
        """Test should display not found when no own payments exist"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_own_payments", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.user_no_payments)
        # when
        response = self.client.get(url)
        response_data = response.json()
        print(response_data)
        # then
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertIn("Not Found", response_data.get("detail", ""))

    def test_get_own_payments_without_access(self):
        """Test should not be able to access own payments API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        url = reverse(
            f"{API_URL}:get_own_payments", kwargs={"corporation_id": corporation_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertIn("Corporation Not Found", response_data.get("error", ""))

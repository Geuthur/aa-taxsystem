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
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem.api.character import CharacterApiEndpoints
from taxsystem.models.alliance import (
    AllianceFilter,
    AlliancePaymentAccount,
    AlliancePayments,
)
from taxsystem.tests.testdata.generate_filter import (
    create_alliance_filter,
    create_alliance_filterset,
)
from taxsystem.tests.testdata.generate_owneraudit import (
    create_alliance_owner_from_user,
)
from taxsystem.tests.testdata.generate_payments import (
    create_alliance_payment,
    create_alliance_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestAllianceApiEndpoints(TestCase):
    """Test Alliance API endpoints for payments and filters."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.api = NinjaAPI()
        cls.character_endpoint = CharacterApiEndpoints(cls.api)
        cls.factory = RequestFactory()

        # Create user with alliance character
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "taxsystem.basic_access",
                "taxsystem.manage_alliances",
            ],
        )

        # Create AllianceOwner
        cls.alliance_owner = create_alliance_owner_from_user(cls.user)

        # User without payments
        cls.user_no_payments, cls.character_ownership_no_payments = (
            create_user_from_evecharacter(1002, permissions=["taxsystem.basic_access"])
        )

        # User without eve character
        cls.no_evecharacter_user = UserMainFactory(permissions=[])

        # Create payment system
        cls.payment_system = create_alliance_payment_system(
            name=cls.character_ownership.character.character_name,
            owner=cls.alliance_owner,
            user=cls.user,
            status=AlliancePaymentAccount.Status.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        # Create payments
        cls.payments = create_alliance_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            owner_id=cls.character_ownership.character.alliance_id,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Alliance Tax Payment",
            request_status=AlliancePayments.RequestStatus.PENDING,
            reviser="",
        )

        cls.payments2 = create_alliance_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            owner_id=cls.character_ownership.character.alliance_id,
            entry_id=2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Alliance Mining Operations",
            request_status=AlliancePayments.RequestStatus.PENDING,
            reviser="",
        )

        # Create filter set
        cls.filter_set = create_alliance_filterset(
            owner=cls.alliance_owner,
            name="100m Alliance Filter",
            description="Filter for alliance payments over 100m",
        )

        cls.filter_amount = create_alliance_filter(
            filter_set=cls.filter_set,
            filter_type=AllianceFilter.FilterType.AMOUNT,
            value=1000,
        )

    def test_get_alliance_payments_access(self):
        """Test should be able to access alliance payments API endpoint"""
        # given
        alliance_id = self.character_ownership.character.alliance_id
        url = reverse(
            f"{API_URL}:get_alliance_payments", kwargs={"alliance_id": alliance_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = response.json()
        self.assertIn("owner", response_data)
        self.assertEqual(len(response_data["owner"]), 2)

    def test_get_alliance_payments_without_access(self):
        """Test should not be able to access alliance payments API endpoint without permission"""
        # given
        alliance_id = self.character_ownership.character.alliance_id
        url = reverse(
            f"{API_URL}:get_alliance_payments", kwargs={"alliance_id": alliance_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_own_alliance_payments_access(self):
        """Test should be able to access own alliance payments API endpoint"""
        # given
        alliance_id = self.character_ownership.character.alliance_id
        url = reverse(
            f"{API_URL}:get_alliance_own_payments", kwargs={"alliance_id": alliance_id}
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = response.json()
        self.assertIn("owner", response_data)
        self.assertEqual(len(response_data["owner"]), 2)

    def test_get_own_alliance_payments_no_payments(self):
        """Test should display not found when no own alliance payments exist"""
        # given
        alliance_id = self.character_ownership.character.alliance_id
        url = reverse(
            f"{API_URL}:get_alliance_own_payments", kwargs={"alliance_id": alliance_id}
        )
        self.client.force_login(self.user_no_payments)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_own_alliance_payments_without_access(self):
        """Test should not be able to access own alliance payments API endpoint without permission"""
        # given
        alliance_id = self.character_ownership.character.alliance_id
        url = reverse(
            f"{API_URL}:get_alliance_own_payments", kwargs={"alliance_id": alliance_id}
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertIn("Alliance Not Found", response_data.get("error", ""))

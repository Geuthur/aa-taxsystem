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

    def test_get_payment_details(self):
        """Test should be able to access payment details API endpoint"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        character_id = self.character_ownership.character.character_id
        payment_id = self.payments.pk
        url = reverse(
            f"{API_URL}:get_payment_details",
            kwargs={
                "owner_id": corporation_id,
                "pk": payment_id,
                "character_id": character_id,
            },
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_payment_details_without_access(self):
        """Test should not be able to access payment details API endpoint without permission"""
        # given
        corporation_id = self.character_ownership.character.corporation_id
        character_id = self.character_ownership.character.character_id
        payment_id = self.payments.pk
        url = reverse(
            f"{API_URL}:get_payment_details",
            kwargs={
                "owner_id": corporation_id,
                "pk": payment_id,
                "character_id": character_id,
            },
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

    def test_get_member_payments(self):
        """Test should be able to access member payments API endpoint"""
        # given
        owner_id = self.character_ownership.character.corporation_id
        character_id = self.character_ownership.character.character_id
        url = reverse(
            f"{API_URL}:get_member_payments",
            kwargs={"owner_id": owner_id, "character_id": character_id},
        )
        self.client.force_login(self.user)
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("Gneuten", str(response.content))

    def test_get_member_payments_without_access(self):
        """Test should not be able to access member payments API endpoint without permission"""
        # given
        owner_id = self.character_ownership.character.corporation_id
        character_id = self.character_ownership.character.character_id
        url = reverse(
            f"{API_URL}:get_member_payments",
            kwargs={"owner_id": owner_id, "character_id": character_id},
        )
        self.client.force_login(self.no_evecharacter_user)
        # when
        response = self.client.get(url)
        response_data = response.json()
        # then
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn("Permission Denied", response_data.get("error", ""))

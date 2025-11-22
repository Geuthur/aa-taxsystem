# Django
from django.test import RequestFactory, TestCase
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA TaxSystem
from taxsystem.api.alliance import PaymentAllianceSchema
from taxsystem.api.helpers.common import (
    build_own_payments_response_list,
    build_payments_response_list,
)
from taxsystem.models.alliance import AllianceOwner, AlliancePayments
from taxsystem.tests.testdata.generate_owneraudit import (
    create_alliance_owner_from_user,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse


class TestBuildAlliancePaymentsResponseList(TestCase):
    """
    Test build_payments_response_list helper function with Alliance data.

    Prerequisites:
    - load_allianceauth() and load_eveuniverse() must be called first
    - Test user must be created with an alliance character
    - At least one AllianceOwner must exist
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load base test data (required for all tests)
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        # Create user with alliance character (character 1001 belongs to alliance)
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["taxsystem.basic_access"]
        )

        # Create AllianceOwner from user
        cls.alliance_owner = create_alliance_owner_from_user(cls.user)

    def test_builds_alliance_payment_list(self):
        """Test building alliance payment response list with AlliancePayments"""
        # TODO: Implement when AlliancePayments factory functions are available
        # This requires:
        # 1. create_alliance_payment_system() factory
        # 2. create_alliance_payment() factory
        # 3. AlliancePayments model and structure
        self.skipTest("AlliancePayments factory not yet implemented")

    def test_builds_empty_list_for_no_alliance_payments(self):
        """Test building empty list when no alliance payments exist"""
        # Arrange
        payments = AlliancePayments.objects.none()
        request = self.factory.get("/")
        request.user = self.user
        perms = True

        # Act
        result = build_payments_response_list(
            payments, request, perms, PaymentAllianceSchema
        )

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


class TestBuildOwnAlliancePaymentsResponseList(TestCase):
    """
    Test build_own_payments_response_list helper function with Alliance data.

    Prerequisites:
    - load_allianceauth() and load_eveuniverse() must be called first
    - Test user must be created with an alliance character
    - At least one AllianceOwner must exist
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load base test data (required for all tests)
        load_allianceauth()
        load_eveuniverse()

        # Create user with alliance character
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["taxsystem.basic_access"]
        )

        # Create AllianceOwner from user
        cls.alliance_owner = create_alliance_owner_from_user(cls.user)

    def test_builds_own_alliance_payment_list(self):
        """Test building own payment response list for alliance"""
        # TODO: Implement when AlliancePayments factory functions are available
        self.skipTest("AlliancePayments factory not yet implemented")

    def test_builds_empty_own_alliance_payment_list(self):
        """Test building empty own alliance payment list"""
        # Arrange
        payments = AlliancePayments.objects.none()

        # Act
        result = build_own_payments_response_list(payments, PaymentAllianceSchema)

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

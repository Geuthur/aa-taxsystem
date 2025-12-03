# Django
from django.test import RequestFactory, TestCase
from django.utils import timezone

# AA TaxSystem
from taxsystem.api.corporation import PaymentCorporationSchema
from taxsystem.api.helpers.common import (
    build_admin_logs_response_list,
    build_filters_response_list,
    build_members_response_list,
    build_own_payments_response_list,
    build_payment_accounts_response_list,
    build_payments_response_list,
    create_admin_log_response_data,
    create_filter_response_data,
    create_payment_account_response_data,
)
from taxsystem.api.schema import (
    AdminHistorySchema,
    FilterModelSchema,
    MembersSchema,
    PaymentSystemSchema,
)
from taxsystem.models.corporation import (
    CorporationAdminHistory,
    CorporationFilter,
    CorporationFilterSet,
    CorporationOwner,
    CorporationPaymentAccount,
    CorporationPayments,
    Members,
)
from taxsystem.tests.testdata.generate_owneraudit import (
    create_corporation_owner_from_user,
    create_user_from_evecharacter_with_access,
)
from taxsystem.tests.testdata.generate_payments import (
    create_payment,
    create_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse


class TestBuildPaymentsResponseList(TestCase):
    """
    Test build_payments_response_list helper function.

    Prerequisites:
    - load_allianceauth() and load_eveuniverse() must be called first
    - Test user must be created via generate_owneraudit functions
    - At least one owneraudit (CorporationOwner) must exist
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load base test data (required for all tests)
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        # Create user with main character using testdata factory
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

        # Create owneraudit (CorporationOwner) from user
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_builds_corporation_payment_list(self):
        """Test building corporation payment response list"""
        # Arrange
        account = create_payment_system(self.owner, user=self.user)
        payment1 = create_payment(
            account,
            name=self.user.profile.main_character.character_name,
            owner_id=self.owner.eve_corporation.corporation_id,
            entry_id=1,
            amount=1000000,
            date=timezone.now(),
            reason="Test Payment 1",
        )
        payment2 = create_payment(
            account,
            name=self.user.profile.main_character.character_name,
            owner_id=self.owner.eve_corporation.corporation_id,
            entry_id=2,
            amount=2000000,
            date=timezone.now(),
            reason="Test Payment 2",
        )

        payments = CorporationPayments.objects.filter(
            owner_id=self.owner.eve_corporation.corporation_id
        )

        request = self.factory.get("/")
        request.user = self.user
        perms = True

        # Act
        result = build_payments_response_list(
            payments, request, perms, PaymentCorporationSchema
        )

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], PaymentCorporationSchema)
        self.assertIsInstance(result[1], PaymentCorporationSchema)
        self.assertIn(payment1.id, [r.payment_id for r in result])
        self.assertIn(payment2.id, [r.payment_id for r in result])

    def test_builds_empty_list_for_no_payments(self):
        """Test building empty list when no payments exist"""
        # Arrange
        payments = CorporationPayments.objects.none()
        request = self.factory.get("/")
        request.user = self.user
        perms = True

        # Act
        result = build_payments_response_list(
            payments, request, perms, PaymentCorporationSchema
        )

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


class TestBuildOwnPaymentsResponseList(TestCase):
    """
    Test build_own_payments_response_list helper function.

    Prerequisites:
    - load_allianceauth() and load_eveuniverse() must be called first
    - Test user must be created via generate_owneraudit functions
    - At least one owneraudit (CorporationOwner) must exist
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load base test data (required for all tests)
        load_allianceauth()
        load_eveuniverse()

        # Create user with main character using testdata factory
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

        # Create owneraudit (CorporationOwner) from user
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_builds_own_corporation_payment_list(self):
        """Test building own payment response list for corporation"""
        # Arrange
        account = create_payment_system(self.owner, user=self.user)
        create_payment(
            account,
            name=self.user.profile.main_character.character_name,
            owner_id=self.owner.eve_corporation.corporation_id,
            entry_id=1,
            amount=500000,
            date=timezone.now(),
            reason="Test Payment 1",
        )
        create_payment(
            account,
            name=self.user.profile.main_character.character_name,
            owner_id=self.owner.eve_corporation.corporation_id,
            entry_id=2,
            amount=750000,
            date=timezone.now(),
            reason="Test Payment 2",
        )

        payments = CorporationPayments.objects.filter(
            owner_id=self.owner.eve_corporation.corporation_id,
            account__user=self.user,
        )

        # Act
        result = build_own_payments_response_list(payments, PaymentCorporationSchema)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], PaymentCorporationSchema)
        self.assertIsInstance(result[1], PaymentCorporationSchema)


class TestBuildMembersResponseList(TestCase):
    """
    Test build_members_response_list helper function.

    Prerequisites:
    - load_allianceauth() and load_eveuniverse() must be called first
    - Test user must be created via generate_owneraudit functions
    - At least one owneraudit (CorporationOwner) must exist
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load base test data (required for all tests)
        load_allianceauth()
        load_eveuniverse()

        # Create user with main character using testdata factory
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

        # Create owneraudit (CorporationOwner) from user
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_builds_members_list(self):
        """Test building members response list with actual member data"""
        # Arrange - Create test member
        Members.objects.create(
            owner=self.owner,
            character_id=self.user.profile.main_character.character_id,
            character_name=self.user.profile.main_character.character_name,
            joined=timezone.now(),
        )

        members = Members.objects.filter(
            owner__eve_corporation__corporation_id=self.owner.eve_corporation.corporation_id
        ).select_related("owner", "owner__eve_corporation")

        # Act
        result = build_members_response_list(members, MembersSchema)

        # Assert
        self.assertGreater(len(result), 0)
        for member_response in result:
            self.assertIsInstance(member_response, MembersSchema)
            self.assertIsNotNone(member_response.character)

    def test_builds_empty_members_list(self):
        """Test building empty members list"""
        # Arrange
        members = Members.objects.none()

        # Act
        result = build_members_response_list(members, MembersSchema)

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


class TestCreatePaymentAccountResponseData(TestCase):
    """Test create_payment_account_response_data helper function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_creates_payment_account_data(self):
        """Test creating payment account response data"""
        # Arrange
        account = create_payment_system(self.owner, user=self.user)

        # Act
        result = create_payment_account_response_data(account)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("payment_id", result)
        self.assertIn("account", result)
        self.assertIn("has_paid", result)
        self.assertIn("actions", result)
        self.assertEqual(result["payment_id"], account.pk)

    def test_payment_account_includes_character_info(self):
        """Test that payment account data includes character information"""
        # Arrange
        account = create_payment_system(self.owner, user=self.user)

        # Act
        result = create_payment_account_response_data(account)

        # Assert
        account_schema = result["account"]
        self.assertEqual(
            account_schema.character_id,
            self.user.profile.main_character.character_id,
        )
        self.assertEqual(
            account_schema.character_name,
            self.user.profile.main_character.character_name,
        )


class TestBuildPaymentAccountsResponseList(TestCase):
    """Test build_payment_accounts_response_list helper function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_builds_payment_accounts_list(self):
        """Test building payment accounts response list"""
        # Arrange
        create_payment_system(self.owner, user=self.user)

        # Create second user and account
        user2, _ = create_user_from_evecharacter_with_access(1002)
        create_payment_system(self.owner, user=user2)

        accounts = CorporationPaymentAccount.objects.filter(
            owner=self.owner
        ).select_related(
            "user",
            "user__profile",
            "user__profile__main_character",
        )

        # Act
        result = build_payment_accounts_response_list(accounts, PaymentSystemSchema)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], PaymentSystemSchema)
        self.assertIsInstance(result[1], PaymentSystemSchema)

    def test_builds_empty_payment_accounts_list(self):
        """Test building empty payment accounts list"""
        # Arrange
        accounts = CorporationPaymentAccount.objects.none()

        # Act
        result = build_payment_accounts_response_list(accounts, PaymentSystemSchema)

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


class TestCreateFilterResponseData(TestCase):
    """Test create_filter_response_data helper function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_creates_filter_data_with_amount_formatting(self):
        """Test creating filter response data with AMOUNT type formatting"""
        # Arrange
        filter_set = CorporationFilterSet.objects.create(
            owner=self.owner,
            name="Test Filter Set",
            description="Test Description",
            enabled=True,
        )
        filter_obj = CorporationFilter.objects.create(
            filter_set=filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000000,
        )

        # Act
        result = create_filter_response_data(filter_obj)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("filter_set", result)
        self.assertIn("filter_type", result)
        self.assertIn("value", result)
        self.assertIn("actions", result)
        self.assertIn("ISK", result["value"])  # Check ISK formatting

    def test_creates_filter_data_without_amount_formatting(self):
        """Test creating filter response data with non-AMOUNT type"""
        # Arrange
        filter_set = CorporationFilterSet.objects.create(
            owner=self.owner,
            name="Test Filter Set",
            description="Test Description",
            enabled=True,
        )
        filter_obj = CorporationFilter.objects.create(
            filter_set=filter_set,
            filter_type=CorporationFilter.FilterType.REASON,
            value="Test Reason",
        )

        # Act
        result = create_filter_response_data(filter_obj)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["value"], "Test Reason")
        self.assertNotIn("ISK", result["value"])


class TestBuildFiltersResponseList(TestCase):
    """Test build_filters_response_list helper function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_builds_filters_list(self):
        """Test building filters response list"""
        # Arrange
        filter_set = CorporationFilterSet.objects.create(
            owner=self.owner,
            name="Test Filter Set",
            description="Test Description",
            enabled=True,
        )
        CorporationFilter.objects.create(
            filter_set=filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000000,
        )
        CorporationFilter.objects.create(
            filter_set=filter_set,
            filter_type=CorporationFilter.FilterType.REASON,
            value="Test Reason",
        )

        filters = CorporationFilter.objects.filter(
            filter_set=filter_set
        ).select_related("filter_set", "filter_set__owner")

        # Act
        result = build_filters_response_list(filters, FilterModelSchema)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], FilterModelSchema)
        self.assertIsInstance(result[1], FilterModelSchema)

    def test_builds_empty_filters_list(self):
        """Test building empty filters list"""
        # Arrange
        filters = CorporationFilter.objects.none()

        # Act
        result = build_filters_response_list(filters, FilterModelSchema)

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


class TestCreateAdminLogResponseData(TestCase):
    """Test create_admin_log_response_data helper function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_creates_admin_log_data(self):
        """Test creating admin log response data"""
        # Arrange
        log = CorporationAdminHistory.objects.create(
            owner=self.owner,
            user=self.user,
            action=CorporationAdminHistory.Actions.ADD,
            comment="Test log entry",
        )

        # Act
        result = create_admin_log_response_data(log)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("log_id", result)
        self.assertIn("user_name", result)
        self.assertIn("date", result)
        self.assertIn("action", result)
        self.assertIn("comment", result)
        self.assertEqual(result["log_id"], log.pk)
        self.assertEqual(result["user_name"], self.user.username)
        self.assertEqual(result["action"], CorporationAdminHistory.Actions.ADD)
        self.assertEqual(result["comment"], "Test log entry")

    def test_admin_log_date_formatting(self):
        """Test that admin log date is properly formatted"""
        # Arrange
        log = CorporationAdminHistory.objects.create(
            owner=self.owner,
            user=self.user,
            action=CorporationAdminHistory.Actions.CHANGE,
            comment="Date format test",
        )

        # Act
        result = create_admin_log_response_data(log)

        # Assert
        self.assertIsInstance(result["date"], str)
        self.assertRegex(result["date"], r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


class TestBuildAdminLogsResponseList(TestCase):
    """Test build_admin_logs_response_list helper function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_builds_admin_logs_list(self):
        """Test building admin logs response list"""
        # Arrange
        CorporationAdminHistory.objects.create(
            owner=self.owner,
            user=self.user,
            action=CorporationAdminHistory.Actions.ADD,
            comment="First log entry",
        )
        CorporationAdminHistory.objects.create(
            owner=self.owner,
            user=self.user,
            action=CorporationAdminHistory.Actions.CHANGE,
            comment="Second log entry",
        )

        logs = CorporationAdminHistory.objects.filter(owner=self.owner).select_related(
            "user"
        )

        # Act
        result = build_admin_logs_response_list(logs, AdminHistorySchema)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], AdminHistorySchema)
        self.assertIsInstance(result[1], AdminHistorySchema)

    def test_builds_empty_admin_logs_list(self):
        """Test building empty admin logs list"""
        # Arrange
        logs = CorporationAdminHistory.objects.none()

        # Act
        result = build_admin_logs_response_list(logs, AdminHistorySchema)

        # Assert
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

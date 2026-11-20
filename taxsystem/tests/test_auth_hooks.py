"""Tests for the TaxSystem menu item hook."""

# Third Party
from evesde_factory.allianceauth import EveCharacterFactory
from evesde_factory.utils import add_character_to_user

# Django
from django.utils import timezone

# Alliance Auth
from allianceauth.groupmanagement.models import Group

# AA TaxSystem
from taxsystem.auth_hooks import TaxSystemMenuItem
from taxsystem.models.helpers.textchoices import PaymentRequestStatus
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import (
    AllianceGroupFactory,
    AllianceOwnerFactory,
    AlliancePaymentsFactory,
    AllianceTaxAccountFactory,
    CorporationGroupFactory,
    CorporationOwnerFactory,
    CorporationPaymentsFactory,
    CorporationTaxAccountFactory,
    UserMainFactory,
)


class TestTaxSystemMenuItem(AuthTestCase):
    """Test the unpaid badge of the TaxSystem menu item."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.superuser)
        cls.tax_free_group = Group.objects.create(name="Tax Free Menu Group")
        CorporationGroupFactory(owner=cls.audit, groups=[cls.tax_free_group])
        cls.alliance_audit = AllianceOwnerFactory(user=cls.superuser)
        AllianceGroupFactory(owner=cls.alliance_audit, groups=[cls.tax_free_group])

    def _render_count(self, user) -> int:
        request = self.factory.get("/")
        request.user = user
        menu_item = TaxSystemMenuItem()
        menu_item.render(request)
        return menu_item.count

    def test_should_count_unpaid_member(self):
        """
        Test that an unpaid member outside a tax-free group gets the badge.

        Results:
            - The badge count is 1.
        """
        # Test Data
        user = UserMainFactory()
        CorporationTaxAccountFactory(
            owner=self.audit, user=user, deposit=-1000, status="active"
        )

        # Test Action
        count = self._render_count(user)

        # Expected Result
        self.assertEqual(count, 1)

    def test_should_not_count_unpaid_tax_free_group_member(self):
        """
        Test that an unpaid member of a tax-free group gets no badge.

        Results:
            - The badge count is 0.
        """
        # Test Data
        user = UserMainFactory()
        self.tax_free_group.user_set.add(user)
        CorporationTaxAccountFactory(
            owner=self.audit, user=user, deposit=-1000, status="active"
        )

        # Test Action
        count = self._render_count(user)

        # Expected Result
        self.assertEqual(count, 0)

    def test_should_not_count_new_member_before_deadlines_run(self):
        """
        Test that a new member gets no badge before the first deadlines run.

        Results:
            - The badge count is 0.
        """
        # Test Data
        audit = CorporationOwnerFactory(user=UserMainFactory(), tax_amount=1000)
        user = UserMainFactory()
        char = EveCharacterFactory(corporation=audit.eve_corporation)
        add_character_to_user(user=user, character=char, is_main=True)
        audit.update_tax_accounts(force_refresh=False)

        # Test Action
        count = self._render_count(user)

        # Expected Result
        self.assertEqual(count, 0)

    def test_should_count_unpaid_alliance_member(self):
        """
        Test that an unpaid alliance member outside a tax-free group gets the badge.

        Results:
            - The badge count is 1.
        """
        # Test Data
        user = UserMainFactory()
        AllianceTaxAccountFactory(
            owner=self.alliance_audit, user=user, deposit=-1000, status="active"
        )

        # Test Action
        count = self._render_count(user)

        # Expected Result
        self.assertEqual(count, 1)

    def test_should_not_count_paid_alliance_member(self):
        """
        Test that a paid alliance member gets no badge.

        Results:
            - The badge count is 0.
        """
        # Test Data
        user = UserMainFactory()
        AllianceTaxAccountFactory(
            owner=self.alliance_audit,
            user=user,
            deposit=1000,
            status="active",
            last_paid=timezone.now(),
        )

        # Test Action
        count = self._render_count(user)

        # Expected Result
        self.assertEqual(count, 0)

    def test_should_not_count_unpaid_tax_free_alliance_member(self):
        """
        Test that an unpaid alliance member of a tax-free group gets no badge.

        Results:
            - The badge count is 0.
        """
        # Test Data
        user = UserMainFactory()
        self.tax_free_group.user_set.add(user)
        AllianceTaxAccountFactory(
            owner=self.alliance_audit, user=user, deposit=-1000, status="active"
        )

        # Test Action
        count = self._render_count(user)

        # Expected Result
        self.assertEqual(count, 0)

    def test_should_count_open_alliance_invoices_for_alliance_manager(self):
        """
        Test that an alliance manager sees the open alliance invoices.

        Results:
            - The badge count is the number of open alliance invoices.
        """
        # Test Data
        manager = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.manage_alliances"]
        )
        account = AllianceTaxAccountFactory(owner=self.alliance_audit)
        for status in (
            PaymentRequestStatus.PENDING,
            PaymentRequestStatus.NEEDS_APPROVAL,
            PaymentRequestStatus.APPROVED,
        ):
            AlliancePaymentsFactory(
                owner=self.alliance_audit, account=account, request_status=status
            )

        # Test Action
        count = self._render_count(manager)

        # Expected Result
        self.assertEqual(count, 2)

    def test_should_sum_open_invoices_for_corporation_and_alliance_manager(self):
        """
        Test that a manager of both sides sees the sum of open invoices.

        Results:
            - The badge count is the sum of open corporation and alliance invoices.
        """
        # Test Data
        manager = UserMainFactory(
            permissions__=[
                "taxsystem.basic_access",
                "taxsystem.manage_corps",
                "taxsystem.manage_alliances",
            ]
        )
        corp_account = CorporationTaxAccountFactory(owner=self.audit)
        CorporationPaymentsFactory(
            owner=self.audit,
            account=corp_account,
            request_status=PaymentRequestStatus.PENDING,
        )
        alliance_account = AllianceTaxAccountFactory(owner=self.alliance_audit)
        for _ in range(2):
            AlliancePaymentsFactory(
                owner=self.alliance_audit,
                account=alliance_account,
                request_status=PaymentRequestStatus.PENDING,
            )

        # Test Action
        count = self._render_count(manager)

        # Expected Result
        self.assertEqual(count, 3)

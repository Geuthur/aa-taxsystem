"""Tests for the TaxSystem menu item hook."""

# Alliance Auth
from allianceauth.groupmanagement.models import Group

# AA TaxSystem
from taxsystem.auth_hooks import TaxSystemMenuItem
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import (
    CorporationGroupFactory,
    CorporationOwnerFactory,
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

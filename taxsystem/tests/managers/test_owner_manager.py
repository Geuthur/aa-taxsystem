# Django
from django.test import override_settings

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_owner_from_user,
)

MODULE_PATH = "taxsystem.managers.owner_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestOwnerManager(TaxSystemTestCase):
    """Test Corporation Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(cls.user)
        cls.alliance_audit = create_owner_from_user(cls.user, tax_type="alliance")

    def test_visible_to(self):
        """
        Test OwnerManager.visible_to() method.
        This test verifies that the visibility of owners is correctly managed based on user permissions.

        Results:
            # Corporation visible_to tests
            1. The owner associated with user 1 is visible to user 1.
            2. The owner associated with user 2 is visible to user 2.
            3. Both owners are visible to a superuser.
            4. Both owners are visible to a user with 'taxsystem.manage_corps' permission.
            # Alliance visible_to tests
            1. The alliance owner associated with user 1 is visible to user 1.
            2. The alliance owner associated with user 2 is visible to user 2.
            3. Both alliance owners are visible to a superuser.
            4. Both alliance owners are visible to a user with 'taxsystem.manage_alliances' permission.
        """
        # Setup additional user and owner
        audit_2 = create_owner_from_user(self.user_2)
        alliance_audit_2 = create_owner_from_user(self.user_2, tax_type="alliance")

        # Test that audit is visible to its user
        visible_audits_user_1 = type(self.audit).objects.visible_to(self.user)
        self.assertIn(self.audit, visible_audits_user_1)
        self.assertNotIn(audit_2, visible_audits_user_1)

        # Test that audit_2 is visible to its user
        visible_audits_user_2 = type(audit_2).objects.visible_to(self.user_2)
        self.assertIn(audit_2, visible_audits_user_2)
        self.assertNotIn(self.audit, visible_audits_user_2)

        # Test that both audits are visible to a superuser
        self.assertIn(self.audit, type(self.audit).objects.visible_to(self.superuser))
        self.assertIn(audit_2, type(audit_2).objects.visible_to(self.superuser))

        # Test that both audits are visible to permission 'taxsystem.manage_corps'
        self.assertIn(self.audit, type(self.audit).objects.visible_to(self.manage_user))
        self.assertIn(audit_2, type(audit_2).objects.visible_to(self.manage_user))

        # Alliance visible_to tests
        # Test that alliance_audit is visible to its user
        visible_alliance_audits_user_1 = type(self.alliance_audit).objects.visible_to(
            self.user
        )
        self.assertIn(self.alliance_audit, visible_alliance_audits_user_1)
        self.assertNotIn(alliance_audit_2, visible_alliance_audits_user_1)

        # Test that alliance_audit_2 is visible to its user
        visible_alliance_audits_user_2 = type(alliance_audit_2).objects.visible_to(
            self.user_2
        )
        self.assertIn(alliance_audit_2, visible_alliance_audits_user_2)
        self.assertNotIn(self.alliance_audit, visible_alliance_audits_user_2)

        # Test that both alliance audits are visible to a superuser
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.visible_to(self.superuser),
        )
        self.assertIn(
            alliance_audit_2, type(alliance_audit_2).objects.visible_to(self.superuser)
        )

        # Test that both alliance audits are visible to permission 'taxsystem.manage_alliances'
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.visible_to(self.manage_user),
        )
        self.assertIn(
            alliance_audit_2,
            type(alliance_audit_2).objects.visible_to(self.manage_user),
        )

    def test_manage_to(self):
        """
        Test OwnerManager.manage_to() method.
        This test verifies that the management access of owners is correctly managed based on user permissions.

        Results:
            # Corporation manage_to tests
            1. The owner associated with user 1 can not be managed by user 1.
            2. The owner associated with user 1 can not be managed by other users.
            3. Both owners are manageable to a superuser.
            4. Own owner is manageable to a user with 'taxsystem.manage_own_corp' permission.
            5. Both owners are manageable to a user with 'taxsystem.manage_corps' permission.
            # Alliance manage_to tests
            1. The alliance owner associated with user 1 can not be managed by user 1.
            2. The alliance owner associated with user 1 can not be managed by other users.
            3. Both alliance owners are manageable to a superuser.
            4. Own alliance owner is manageable to a user with 'taxsystem.manage_own_alliance' permission.
            5. Both alliance owners are manageable to a user with 'taxsystem.manage_alliances' permission.
        """
        # Setup additional user and owner
        audit_2 = create_owner_from_user(self.user_2)
        alliance_audit_2 = create_owner_from_user(self.user_2, tax_type="alliance")

        # Test that user can not be managed by its user
        manageable_audits_user_1 = type(self.audit).objects.manage_to(self.user)
        self.assertNotIn(self.audit, manageable_audits_user_1)

        # Test that audit can not be managed by other user
        manageable_audits_user_2 = type(audit_2).objects.manage_to(self.user_2)
        self.assertNotIn(audit_2, manageable_audits_user_2)
        self.assertNotIn(self.audit, manageable_audits_user_2)

        # Test that both audits are manageable to a superuser
        self.assertIn(self.audit, type(self.audit).objects.manage_to(self.superuser))
        self.assertIn(audit_2, type(audit_2).objects.manage_to(self.superuser))

        # Test that own corporation audit are manageable to permission 'taxsystem.manage_own_corp'
        self.assertIn(
            self.audit, type(self.audit).objects.manage_to(self.manage_own_user)
        )
        self.assertNotIn(audit_2, type(audit_2).objects.manage_to(self.manage_own_user))

        # Test that all corporation audits are manageable to permission 'taxsystem.manage_corps'
        self.assertIn(audit_2, type(audit_2).objects.manage_to(self.manage_user))
        self.assertIn(self.audit, type(self.audit).objects.manage_to(self.manage_user))

        # Alliance manageable_to tests
        # Test that alliance audit can not be managed by its user
        manageable_audits_user_1 = type(self.alliance_audit).objects.manage_to(
            self.user
        )
        self.assertNotIn(self.alliance_audit, manageable_audits_user_1)

        # Test that alliance audit can not be managed by other user
        manageable_audits_user_2 = type(alliance_audit_2).objects.manage_to(self.user_2)
        self.assertNotIn(alliance_audit_2, manageable_audits_user_2)
        self.assertNotIn(self.alliance_audit, manageable_audits_user_2)

        # Test that both alliance audits are manageable to a superuser
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.manage_to(self.superuser),
        )
        self.assertIn(
            alliance_audit_2, type(alliance_audit_2).objects.manage_to(self.superuser)
        )

        # Test that own audit are manageable to permission 'taxsystem.manage_own_alliance'
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.manage_to(self.manage_own_user),
        )
        self.assertNotIn(
            alliance_audit_2,
            type(alliance_audit_2).objects.manage_to(self.manage_own_user),
        )

        # Test that all alliance audits are manageable to permission 'taxsystem.manage_alliances'
        self.assertIn(
            alliance_audit_2, type(alliance_audit_2).objects.manage_to(self.manage_user)
        )
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.manage_to(self.manage_user),
        )

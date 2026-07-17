# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

# AA TaxSystem
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
    EveCharacterFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.managers.owner_manager"


class TestOwnerManager(TaxSystemTestCase):
    """Test Corporation Managers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Corporation Owner
        corp = EveCorporationInfo.objects.get(
            corporation_id=cls.user_character.corporation_id
        )
        cls.audit = CorporationOwnerFactory(eve_corporation=corp)
        # Alliance Owner
        alliance = EveAllianceInfo.objects.get(
            alliance_id=cls.user_character.alliance_id
        )
        cls.alliance_audit = AllianceOwnerFactory(eve_alliance=alliance)

    def test_corporation_visible_to(self):
        """
        Test OwnerManager.visible_to() method.
        This test verifies that the visibility of owners is correctly managed based on user permissions.

        Results:
            # Corporation visible_to tests
            1. The owner associated with user 1 is visible to user 1.
            2. The owner associated with user 2 is visible to user 2.
            3. Both owners are visible to a superuser.
            4. Both owners are visible to a user with 'taxsystem.manage_corps' permission.
        """
        # Setup additional user and owner
        user_2 = UserMainFactory()
        audit_2 = CorporationOwnerFactory(user=user_2)
        corp = EveCorporationInfo.objects.get(
            corporation_id=self.user_character.corporation_id
        )
        manage_own_corporation = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corp),
            permissions=["taxsystem.manage_own_corp"],
        )
        manage_corporation = UserMainFactory(permissions=["taxsystem.manage_corps"])

        # Test that audit is visible to its user
        visible_audits_user_1 = type(self.audit).objects.visible_to(self.user)
        self.assertIn(self.audit, visible_audits_user_1)
        self.assertNotIn(audit_2, visible_audits_user_1)

        # Test that audit_2 is visible to its user
        visible_audits_user_2 = type(audit_2).objects.visible_to(user_2)
        self.assertIn(audit_2, visible_audits_user_2)
        self.assertNotIn(self.audit, visible_audits_user_2)

        # Test that both audits are visible to a superuser
        self.assertIn(self.audit, type(self.audit).objects.visible_to(self.superuser))
        self.assertIn(audit_2, type(audit_2).objects.visible_to(self.superuser))

        # Test that both audits are visible to permission 'taxsystem.manage_own_corp'
        self.assertIn(
            self.audit, type(self.audit).objects.visible_to(manage_own_corporation)
        )
        self.assertNotIn(
            audit_2, type(audit_2).objects.visible_to(manage_own_corporation)
        )

        # Test that both audits are visible to permission 'taxsystem.manage_corps'
        self.assertIn(
            self.audit, type(self.audit).objects.visible_to(manage_corporation)
        )
        self.assertIn(audit_2, type(audit_2).objects.visible_to(manage_corporation))

    def test_corporation_manage_to(self):
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
        """
        # Setup additional user and owner
        user_2 = UserMainFactory()
        audit_2 = CorporationOwnerFactory(user=user_2)
        corp = EveCorporationInfo.objects.get(
            corporation_id=self.user_character.corporation_id
        )
        manage_own_corporation = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corp),
            permissions=["taxsystem.manage_own_corp"],
        )
        manage_corporation = UserMainFactory(permissions=["taxsystem.manage_corps"])

        # Test that user can not be managed by its user
        manageable_audits_user_1 = type(self.audit).objects.manage_to(self.user)
        self.assertNotIn(self.audit, manageable_audits_user_1)

        # Test that audit can not be managed by other user
        manageable_audits_user_2 = type(audit_2).objects.manage_to(user_2)
        self.assertNotIn(audit_2, manageable_audits_user_2)
        self.assertNotIn(self.audit, manageable_audits_user_2)

        # Test that both audits are manageable to a superuser
        self.assertIn(self.audit, type(self.audit).objects.manage_to(self.superuser))
        self.assertIn(audit_2, type(audit_2).objects.manage_to(self.superuser))

        # Test that own corporation audit are manageable to permission 'taxsystem.manage_own_corp'
        self.assertIn(
            self.audit, type(self.audit).objects.manage_to(manage_own_corporation)
        )
        self.assertNotIn(
            audit_2, type(audit_2).objects.manage_to(manage_own_corporation)
        )

        # Test that all corporation audits are manageable to permission 'taxsystem.manage_corps'
        self.assertIn(audit_2, type(audit_2).objects.manage_to(manage_corporation))
        self.assertIn(
            self.audit, type(self.audit).objects.manage_to(manage_corporation)
        )

    def test_alliance_visible_to(self):
        """
        Test OwnerManager.visible_to() method.
        This test verifies that the visibility of owners is correctly managed based on user permissions.

        Results:
            # Alliance visible_to tests
            1. The alliance owner associated with user 1 is visible to user 1.
            2. The alliance owner associated with user 2 is visible to user 2.
            3. Both alliance owners are visible to a superuser.
            4. Both alliance owners are visible to a user with 'taxsystem.manage_alliances' permission.
        """
        # Test that alliance audit can not be managed by other user
        user_2 = UserMainFactory()
        audit2 = AllianceOwnerFactory(user=user_2)
        corp = EveCorporationInfo.objects.get(
            corporation_id=self.user_character.corporation_id
        )
        manage_own_alliance = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corp),
            permissions=["taxsystem.manage_own_alliance"],
        )
        manage_alliances = UserMainFactory(permissions=["taxsystem.manage_alliances"])

        # Test that alliance_audit is visible to its user
        visible_audits_user_1 = type(self.alliance_audit).objects.visible_to(self.user)
        self.assertIn(self.alliance_audit, visible_audits_user_1)
        self.assertNotIn(audit2, visible_audits_user_1)

        # Test that alliance_audit_2 is visible to its user
        visible_audits_user_2 = type(audit2).objects.visible_to(user_2)
        self.assertIn(audit2, visible_audits_user_2)
        self.assertNotIn(self.alliance_audit, visible_audits_user_2)

        # Test that both alliance audits are visible to a superuser
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.visible_to(self.superuser),
        )
        self.assertIn(audit2, type(audit2).objects.visible_to(self.superuser))

        # Test that both alliance audits are visible to permission 'taxsystem.manage_own_alliance'
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.visible_to(manage_own_alliance),
        )
        self.assertNotIn(
            audit2,
            type(audit2).objects.visible_to(manage_own_alliance),
        )

        # Test that both alliance audits are visible to permission 'taxsystem.manage_alliances'
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.visible_to(manage_alliances),
        )
        self.assertIn(
            audit2,
            type(audit2).objects.visible_to(manage_alliances),
        )

    def test_alliance_manage_to(self):
        """
        Test OwnerManager.manage_to() method.
        This test verifies that the management access of alliance owners is correctly managed based on user permissions.

        Results:
            # Alliance manage_to tests
            1. The alliance owner associated with user 1 can not be managed by user 1.
            2. The alliance owner associated with user 1 can not be managed by other users.
            3. Both alliance owners are manageable to a superuser.
            4. Own alliance owner is manageable to a user with 'taxsystem.manage_own_alliance' permission.
            5. Both alliance owners are manageable to a user with 'taxsystem.manage_alliances' permission.
        """
        # Test that alliance audit can not be managed by other user
        user_2 = UserMainFactory()
        audit_2 = AllianceOwnerFactory(user=user_2)
        corp = EveCorporationInfo.objects.get(
            corporation_id=self.user_character.corporation_id
        )
        manage_own_alliance = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corp),
            permissions=["taxsystem.manage_own_alliance"],
        )
        manage_alliances = UserMainFactory(permissions=["taxsystem.manage_alliances"])

        manageable_audits_user_2 = type(audit_2).objects.manage_to(user_2)
        self.assertNotIn(audit_2, manageable_audits_user_2)
        self.assertNotIn(self.alliance_audit, manageable_audits_user_2)

        # Test that both alliance audits are manageable to a superuser
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.manage_to(self.superuser),
        )
        self.assertIn(audit_2, type(audit_2).objects.manage_to(self.superuser))

        # Test that own audit are manageable to permission 'taxsystem.manage_own_alliance'
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.manage_to(manage_own_alliance),
        )
        self.assertNotIn(
            audit_2,
            type(audit_2).objects.manage_to(manage_own_alliance),
        )

        # Test that all alliance audits are manageable to permission 'taxsystem.manage_alliances'
        self.assertIn(audit_2, type(audit_2).objects.manage_to(manage_alliances))
        self.assertIn(
            self.alliance_audit,
            type(self.alliance_audit).objects.manage_to(manage_alliances),
        )

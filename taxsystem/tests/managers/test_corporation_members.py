# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase, create_user_from_evecharacter
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.tax import Members
from taxsystem.tests.testdata.esi_stub import esi_client_stub
from taxsystem.tests.testdata.generate_owneraudit import create_owneraudit_from_user
from taxsystem.tests.testdata.generate_payments import (
    create_member,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.managers.tax_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
@patch(MODULE_PATH + ".EveEntity.objects.bulk_resolve_names")
@patch(MODULE_PATH + ".logger")
class TestMembersManager(NoSocketsTestCase):
    """Test Members Manager for Corporation Members."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_owneraudit_from_user(cls.user)

        cls.member = create_member(
            owner=cls.audit,
            character_id=1001,
            character_name="Member 1",
            status=Members.States.ACTIVE,
        )

        cls.member_2 = create_member(
            owner=cls.audit,
            character_id=1004,
            character_name="Member 4",
            status=Members.States.ACTIVE,
        )

    def test_update_members(self, mock_logger, mock_bulk_resolve, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()

        mock_bulk_resolve.return_value.to_name.side_effect = (
            "Member 1",
            "Member 2",
            "Member 3",
        )

        self.audit.update_members(force_refresh=False)

        obj = self.audit.ts_members.get(character_id=1001)
        self.assertEqual(obj.character_name, "Member 1")

        obj = self.audit.ts_members.get(character_id=1002)
        self.assertEqual(obj.character_name, "Member 2")

        obj = self.audit.ts_members.get(character_id=1003)
        self.assertEqual(obj.character_name, "Member 3")

        mock_logger.info.assert_called_with(
            "Corp %s - Old Members: %s, New Members: %s, Missing: %s",
            self.audit.corporation.corporation_name,
            1,
            2,
            1,
        )

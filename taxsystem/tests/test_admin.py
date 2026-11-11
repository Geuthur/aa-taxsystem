"""Tests for admin.py"""

# Standard Library
from unittest.mock import Mock, patch

# Third Party
from celery import states
from celery.result import EagerResult

# Django
from django.contrib import messages
from django.contrib.admin.sites import AdminSite

# AA TaxSystem
from taxsystem.admin import AllianceOwnerAdmin, CorporationOwnerAdmin
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
)


class TestCorporationOwnerAdmin(AuthTestCase):
    """Test Backend AA Administration for Tax System"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user.is_staff = True
        cls.user.is_superuser = True
        cls.user.save()

        cls.corporation_owner = CorporationOwnerFactory()
        cls.site = AdminSite()
        cls.admin = CorporationOwnerAdmin(CorporationOwner, cls.site)

    def test_list_display(self):
        """Test list_display configuration"""
        # given/when/then
        self.assertIn("_entity_pic", self.admin.list_display)
        self.assertIn("_eve_corporation__corporation_id", self.admin.list_display)
        self.assertIn("_eve_corporation__corporation_name", self.admin.list_display)
        self.assertIn("_last_update_at", self.admin.list_display)

    def test_entity_pic_display(self):
        """Test _entity_pic method returns HTML"""
        # given/when
        result = self.admin._entity_pic(self.corporation_owner)
        # then
        self.assertIn("<img src=", result)
        self.assertIn('class="img-circle"', result)

    def test_corporation_id_display(self):
        """Test _eve_corporation__corporation_id method"""
        # given/when
        result = self.admin._eve_corporation__corporation_id(self.corporation_owner)
        # then
        self.assertEqual(result, self.corporation_owner.eve_corporation.corporation_id)

    def test_corporation_name_display(self):
        """Test _eve_corporation__corporation_name method"""
        # given/when
        result = self.admin._eve_corporation__corporation_name(self.corporation_owner)
        # then
        self.assertEqual(
            result, self.corporation_owner.eve_corporation.corporation_name
        )

    def test_last_update_at_display_with_data(self):
        """Test _last_update_at method with update status"""
        # given
        self.corporation_owner.last_update_at = "2025-11-22 10:00:00"
        # when
        result = self.admin._last_update_at(self.corporation_owner)
        # then
        self.assertIsNotNone(result)
        self.assertNotEqual(result, "-")

    def test_last_update_at_display_without_data(self):
        """Test _last_update_at method without update status"""
        # given
        self.corporation_owner.last_update_at = None
        # when
        result = self.admin._last_update_at(self.corporation_owner)
        # then
        self.assertEqual(result, "-")

    def test_has_add_permission_returns_false(self):
        """Test has_add_permission always returns False"""
        # given
        request = self.factory.get("/admin/taxsystem/corporationowner/")
        request.user = self.user
        # when
        result = self.admin.has_add_permission(request)
        # then
        self.assertFalse(result)

    def test_has_change_permission_returns_false(self):
        """Test has_change_permission always returns False"""
        # given
        request = self.factory.get("/admin/taxsystem/corporationowner/")
        request.user = self.user
        # when
        result = self.admin.has_change_permission(request)
        # then
        self.assertFalse(result)

    @patch("taxsystem.admin.update_corporation")
    def test_force_update_action(self, mock_update):
        """Test force_update action"""
        # given
        request = self.factory.post("/admin/taxsystem/corporationowner/")
        request.user = self.user
        request._messages = Mock()
        queryset = CorporationOwner.objects.filter(pk=self.corporation_owner.pk)
        # when
        self.admin.force_update(request, queryset)
        # then
        mock_update.delay.assert_called_once_with(
            owner_eve_id=self.corporation_owner.eve_id, force_refresh=True
        )

    @patch("taxsystem.admin.update_corporation")
    def test_force_update_action_should_warn_if_all_skipped(self, mock_update):
        """Test force_update action warns when no update was started"""
        # given
        mock_update.delay.return_value = EagerResult(None, None, states.REJECTED)
        request = self.factory.post("/admin/taxsystem/corporationowner/")
        request.user = self.user
        request._messages = Mock()
        queryset = CorporationOwner.objects.filter(pk=self.corporation_owner.pk)
        # when
        self.admin.force_update(request, queryset)
        # then
        level, message = request._messages.add.call_args.args[:2]
        self.assertEqual(level, messages.WARNING)
        self.assertEqual(
            message,
            "No force update started. 1 corporation(s) skipped, "
            "an update is already queued or running.",
        )

    @patch("taxsystem.admin.update_corporation")
    def test_force_update_action_should_report_skipped(self, mock_update):
        """Test force_update action reports success and skipped owners"""
        # given
        second_owner = CorporationOwnerFactory()
        mock_update.delay.side_effect = [
            EagerResult(None, None, states.REJECTED),
            Mock(),
        ]
        request = self.factory.post("/admin/taxsystem/corporationowner/")
        request.user = self.user
        request._messages = Mock()
        queryset = CorporationOwner.objects.filter(
            pk__in=[self.corporation_owner.pk, second_owner.pk]
        )
        # when
        self.admin.force_update(request, queryset)
        # then
        level, message = request._messages.add.call_args.args[:2]
        self.assertEqual(level, messages.SUCCESS)
        self.assertIn("Started force update for 1 corporation(s).", message)
        self.assertIn(
            "1 corporation(s) skipped, an update is already queued or running.",
            message,
        )


class TestAllianceOwnerAdmin(AuthTestCase):
    """Test force update action of the AllianceOwner admin"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alliance_owner = AllianceOwnerFactory(user=cls.user)
        cls.site = AdminSite()
        cls.admin = AllianceOwnerAdmin(AllianceOwner, cls.site)

    def _request(self):
        request = self.factory.post("/admin/taxsystem/allianceowner/")
        request.user = self.user
        request._messages = Mock()
        return request

    @patch("taxsystem.admin.update_alliance")
    def test_force_update_action(self, mock_update):
        """Test force_update action reports success"""
        # given
        request = self._request()
        queryset = AllianceOwner.objects.filter(pk=self.alliance_owner.pk)
        # when
        self.admin.force_update(request, queryset)
        # then
        mock_update.delay.assert_called_once_with(
            owner_eve_id=self.alliance_owner.eve_id, force_refresh=True
        )
        level, message = request._messages.add.call_args.args[:2]
        self.assertEqual(level, messages.SUCCESS)
        self.assertEqual(
            message,
            "Started force update for 1 alliance(s). "
            "Updates will run in the background.",
        )

    @patch("taxsystem.admin.update_alliance")
    def test_force_update_action_should_warn_if_all_skipped(self, mock_update):
        """Test force_update action warns when no update was started"""
        # given
        mock_update.delay.return_value = EagerResult(None, None, states.REJECTED)
        request = self._request()
        queryset = AllianceOwner.objects.filter(pk=self.alliance_owner.pk)
        # when
        self.admin.force_update(request, queryset)
        # then
        level, message = request._messages.add.call_args.args[:2]
        self.assertEqual(level, messages.WARNING)
        self.assertEqual(
            message,
            "No force update started. 1 alliance(s) skipped, "
            "an update is already queued or running.",
        )

    @patch("taxsystem.admin.update_alliance")
    def test_force_update_action_should_report_skipped(self, mock_update):
        """Test force_update action reports success and skipped owners"""
        # given
        second_owner = AllianceOwnerFactory(user=self.superuser)
        mock_update.delay.side_effect = [
            EagerResult(None, None, states.REJECTED),
            Mock(),
        ]
        request = self._request()
        queryset = AllianceOwner.objects.filter(
            pk__in=[self.alliance_owner.pk, second_owner.pk]
        )
        # when
        self.admin.force_update(request, queryset)
        # then
        level, message = request._messages.add.call_args.args[:2]
        self.assertEqual(level, messages.SUCCESS)
        self.assertIn("Started force update for 1 alliance(s).", message)
        self.assertIn(
            "1 alliance(s) skipped, an update is already queued or running.",
            message,
        )

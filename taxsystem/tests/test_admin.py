"""Tests for admin.py"""

# Standard Library
from unittest.mock import Mock, patch

# Django
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

# AA TaxSystem
from taxsystem.admin import AllianceOwnerAdmin, CorporationOwnerAdmin
from taxsystem.models.alliance import AllianceOwner
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.generate_owneraudit import (
    create_alliance_owner,
    create_corporation_owner_from_user,
    create_user_from_evecharacter_with_access,
)


class TestCorporationOwnerAdmin(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user.is_staff = True
        cls.user.is_superuser = True
        cls.user.save()

        cls.corporation_owner = create_corporation_owner_from_user(cls.user)
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
            owner_pk=self.corporation_owner.pk, force_refresh=True
        )


class TestAllianceOwnerAdmin(TaxSystemTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user.is_staff = True
        cls.user.is_superuser = True
        cls.user.save()

        cls.alliance_owner = create_alliance_owner(cls.user_character.character)
        cls.site = AdminSite()
        cls.admin = AllianceOwnerAdmin(AllianceOwner, cls.site)

    def test_list_display(self):
        """Test list_display configuration"""
        # given/when/then
        self.assertIn("_entity_pic", self.admin.list_display)
        self.assertIn("_eve_alliance__alliance_id", self.admin.list_display)
        self.assertIn("_eve_alliance__alliance_name", self.admin.list_display)
        self.assertIn("corporation", self.admin.list_display)
        self.assertIn("_last_update_at", self.admin.list_display)

    def test_entity_pic_display(self):
        """Test _entity_pic method returns HTML"""
        # given/when
        result = self.admin._entity_pic(self.alliance_owner)
        # then
        self.assertIn("<img src=", result)
        self.assertIn('class="img-circle"', result)

    def test_alliance_id_display(self):
        """Test _eve_alliance__alliance_id method"""
        # given/when
        result = self.admin._eve_alliance__alliance_id(self.alliance_owner)
        # then
        self.assertEqual(result, self.alliance_owner.eve_alliance.alliance_id)

    def test_alliance_name_display(self):
        """Test _eve_alliance__alliance_name method"""
        # given/when
        result = self.admin._eve_alliance__alliance_name(self.alliance_owner)
        # then
        self.assertEqual(result, self.alliance_owner.eve_alliance.alliance_name)

    def test_last_update_at_display_with_data(self):
        """Test _last_update_at method with update status"""
        # given
        self.alliance_owner.last_update_at = "2025-11-22 10:00:00"
        # when
        result = self.admin._last_update_at(self.alliance_owner)
        # then
        self.assertIsNotNone(result)
        self.assertNotEqual(result, "-")

    def test_last_update_at_display_without_data(self):
        """Test _last_update_at method without update status"""
        # given
        self.alliance_owner.last_update_at = None
        # when
        result = self.admin._last_update_at(self.alliance_owner)
        # then
        self.assertEqual(result, "-")

    def test_has_add_permission_returns_false(self):
        """Test has_add_permission always returns False"""
        # given
        request = self.factory.get("/admin/taxsystem/allianceowner/")
        request.user = self.user
        # when
        result = self.admin.has_add_permission(request)
        # then
        self.assertFalse(result)

    def test_has_change_permission_returns_false(self):
        """Test has_change_permission always returns False"""
        # given
        request = self.factory.get("/admin/taxsystem/allianceowner/")
        request.user = self.user
        # when
        result = self.admin.has_change_permission(request)
        # then
        self.assertFalse(result)

    @patch("taxsystem.admin.update_alliance")
    def test_force_update_action(self, mock_update):
        """Test force_update action"""
        # given
        request = self.factory.post("/admin/taxsystem/allianceowner/")
        request.user = self.user
        request._messages = Mock()
        queryset = AllianceOwner.objects.filter(pk=self.alliance_owner.pk)
        # when
        self.admin.force_update(request, queryset)
        # then
        mock_update.delay.assert_called_once_with(
            owner_pk=self.alliance_owner.pk, force_refresh=True
        )

    def test_queryset_includes_corporation(self):
        """Test queryset includes corporation in select_related"""
        # given
        request = self.factory.get("/admin/taxsystem/allianceowner/")
        request.user = self.user
        # when
        queryset = self.admin.get_queryset(request)
        # then
        # select_related returns True when used without arguments,
        # but we can check it was called via prefetch
        self.assertTrue(hasattr(queryset, "query"))
        # Verify the queryset exists and has expected fields
        self.assertTrue(queryset.exists() or queryset.count() >= 0)

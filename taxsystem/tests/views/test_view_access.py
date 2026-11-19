"""Tests that the views to add an owner require `basic_access` and `create_access`."""

# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA TaxSystem
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import UserMainFactory

LOGIN_URL = "/account/login/"
VIEWS = ["taxsystem:add_corp", "taxsystem:add_alliance"]


class TestAddOwnerViewAccess(AuthTestCase):
    """
    Basic access is only granted by `basic_access`.

    `create_access` does not include it. The permissions are checked before
    `token_required`, so a user without them is never sent to the EVE SSO.
    """

    def _get(self, user, url_name):
        self.client.force_login(user)
        return self.client.get(reverse(url_name))

    def test_should_redirect_to_login_with_create_access_only(self):
        # Test Data
        user = UserMainFactory(permissions__=["taxsystem.create_access"])

        for url_name in VIEWS:
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(user, url_name)

                # Expected Result
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertTrue(response["Location"].startswith(LOGIN_URL))

    def test_should_redirect_to_login_with_basic_access_only(self):
        for url_name in VIEWS:
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(self.user, url_name)

                # Expected Result
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertTrue(response["Location"].startswith(LOGIN_URL))

    def test_should_redirect_to_login_with_all_permissions_but_basic_access(self):
        # Test Data
        user = UserMainFactory(
            permissions__=[
                "taxsystem.create_access",
                "taxsystem.manage_own_corp",
                "taxsystem.manage_corps",
                "taxsystem.manage_own_alliance",
                "taxsystem.manage_alliances",
                "taxsystem.admin_access",
            ]
        )

        for url_name in VIEWS:
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(user, url_name)

                # Expected Result
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertTrue(response["Location"].startswith(LOGIN_URL))

    def test_should_reach_token_selection_with_basic_and_create_access(self):
        # Test Data
        user = UserMainFactory(
            permissions__=["taxsystem.basic_access", "taxsystem.create_access"]
        )

        for url_name in VIEWS:
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(user, url_name)

                # Expected Result: `token_required` answers, not the permission check
                self.assertNotEqual(response.status_code, HTTPStatus.FORBIDDEN)
                self.assertFalse(response.get("Location", "").startswith(LOGIN_URL))

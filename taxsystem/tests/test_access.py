"""TestViewAccess class."""

# Standard Library
from http import HTTPStatus

# Django
from django.urls import resolve, reverse

# AA TaxSystem
from taxsystem import views
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import UserFactory

MODULE_PATH = "taxsystem.views"


class TestViewAccess(TaxSystemTestCase):
    """Test View General Access Permissions for React SPA."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_react_base_view_should_return_200_when_has_basic_access(self):
        """Test that a user with 'basic_access' can access react_base view directly."""
        # Test Data
        request = self.factory.get(reverse("taxsystem:index"))
        request.user = self.user

        # Test Action
        response = views.react_base(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_spa_catch_all_route_resolution_should_resolve_to_react_base(self):
        """Test that arbitrary client-side paths resolve to react_base."""
        # Test Data
        url = "/taxsystem/arbitrary/frontend/route/"

        # Test Action
        match = resolve(url)

        # Expected Result
        self.assertEqual(match.url_name, "react_base")

    def test_client_access_index_and_spa_should_return_200(self):
        """Test client GET on index and SPA routes returns 200 OK for authorized user."""
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        resp_index = self.client.get(reverse("taxsystem:index"))
        resp_spa = self.client.get("/taxsystem/payments/")

        # Expected Result
        self.assertEqual(resp_index.status_code, HTTPStatus.OK)
        self.assertEqual(resp_spa.status_code, HTTPStatus.OK)

    def test_client_access_index_should_redirect_when_user_has_no_permission(self):
        """Test client GET redirects when user lacks basic_access permission."""
        # Test Data
        user_no_perms = UserFactory()
        self.client.force_login(user_no_perms)

        # Test Action
        response = self.client.get(reverse("taxsystem:index"))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_client_access_index_should_redirect_when_user_not_authenticated(self):
        """Test client GET redirects when user is not logged in."""
        # Test Data
        # Anonymous client request (no login)

        # Test Action
        response = self.client.get(reverse("taxsystem:index"))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

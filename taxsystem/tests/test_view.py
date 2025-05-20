"""Tax System for a TestView class."""

# Standard Library
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testdata_factories import UserMainFactory

# AA TaxSystem
from taxsystem.views import index


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.user = UserMainFactory(
            permissions=[
                "taxsystem.basic_access",
            ]
        )

    def test_view(self):
        request = self.factory.get(reverse("taxsystem:index"))
        request.user = self.user
        response = index(request)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

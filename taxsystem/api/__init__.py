# Standard Library
import logging

# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# AA TaxSystem
from taxsystem.api import (
    admin,
    corporation,
    filters,
    general,
    groups,
    logs,
    overview,
    payments,
)
from taxsystem.api.helpers.parser import SafeNinjaParser

api = NinjaAPI(
    title="TaxSystem API",
    version="0.5.0",
    urls_namespace="taxsystem:api",
    auth=django_auth,
    parser=SafeNinjaParser(),
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)


def setup(ninja_api):
    general.ApiEndpoints(ninja_api)
    overview.ApiEndpoints(ninja_api)
    corporation.CorporationApiEndpoints(ninja_api)
    admin.AdminApiEndpoints(ninja_api)
    payments.PaymentsApiEndpoints(ninja_api)
    logs.LogsApiEndpoints(ninja_api)
    filters.FilterApiEndpoints(ninja_api)
    groups.GroupsApiEndpoints(ninja_api)


# Initialize API endpoints
setup(api)

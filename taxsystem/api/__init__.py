# Standard Library
import logging

# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# AA TaxSystem
from taxsystem.api import admin, character, corporation

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="TaxSystem API",
    version="0.5.0",
    urls_namespace="taxsystem:api",
    auth=django_auth,
    csrf=True,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)


def setup(ninja_api):
    corporation.CorporationApiEndpoints(ninja_api)
    character.CharacterApiEndpoints(ninja_api)
    admin.AdminApiEndpoints(ninja_api)


# Initialize API endpoints
setup(api)

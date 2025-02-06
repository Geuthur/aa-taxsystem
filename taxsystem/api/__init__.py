from ninja import NinjaAPI
from ninja.security import django_auth

from django.conf import settings

from taxsystem.api import taxsystem
from taxsystem.hooks import get_extension_logger

logger = get_extension_logger(__name__)

api = NinjaAPI(
    title="Geuthur API",
    version="0.1.0",
    urls_namespace="taxsystem:new_api",
    auth=django_auth,
    csrf=True,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)

# Add the taxsystem endpoints
taxsystem.setup(api)

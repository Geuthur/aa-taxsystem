"""App URLs"""

# Django
from django.urls import path, re_path

# Alliance Auth
from allianceauth.authentication.decorators import decorate_url_patterns

# AA TaxSystem
from taxsystem import views
from taxsystem.api import api
from taxsystem.api.auth import basic_access_required

app_name: str = "taxsystem"  # pylint: disable=invalid-name

# Every URL of the API (endpoints, schema and docs) requires `basic_access`
api_patterns, api_app_name, api_namespace = api.urls
api_patterns = decorate_url_patterns(
    (api_patterns, api_app_name), basic_access_required
)[0]

urlpatterns = [
    # -- Registration via ESI SSO (server-side)
    path("corporation/add/", views.add_corp, name="add_corp"),
    path("alliance/add/", views.add_alliance, name="add_alliance"),
    # -- API System
    re_path(r"^api/", (api_patterns, api_app_name, api_namespace)),
    # -- React Frontend
    path("", views.react_base, name="index"),
    re_path(
        r"^(?!api/|corporation/add/|alliance/add/).*$",
        views.react_base,
        name="react_base",
    ),
]

"""App URLs"""

# Django
from django.urls import path, re_path

# AA TaxSystem
from taxsystem import views
from taxsystem.api import api

app_name: str = "taxsystem"  # pylint: disable=invalid-name

urlpatterns = [
    # -- Registration via ESI SSO (server-side)
    path("corporation/add/", views.add_corp, name="add_corp"),
    path("alliance/add/", views.add_alliance, name="add_alliance"),
    # -- API System
    re_path(r"^api/", api.urls),
    # -- React Frontend
    path("", views.react_base, name="index"),
    re_path(
        r"^(?!api/|corporation/add/|alliance/add/|owner/\d+/view/|owner/view/).*$",
        views.react_base,
        name="react_base",
    ),
]

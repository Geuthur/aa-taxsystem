"""App URLs"""

from django.urls import path, re_path

from taxsystem import views
from taxsystem.api import api

app_name: str = "taxsystem"

urlpatterns = [
    path("", views.index, name="index"),
    # -- API System
    re_path(r"^api/", api.urls),
    # -- Tax System
    path("corporation/overview/", views.overview, name="overview"),
    path(
        "corporation/<int:corporation_pk>/",
        views.corporation,
        name="corporation",
    ),
    # -- Tax Administration
    path("corporation/add/", views.add_corp, name="add_corp"),
]

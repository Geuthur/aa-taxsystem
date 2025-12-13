"""App URLs"""

# Django
from django.urls import path, re_path

# AA TaxSystem
from taxsystem import views
from taxsystem.api import api

app_name: str = "taxsystem"  # pylint: disable=invalid-name

urlpatterns = [
    # -- Tax System
    path("", views.index, name="index"),
    path("admin/", views.admin, name="admin"),
    # -- Add Corporation/Alliance
    path("corporation/add/", views.add_corp, name="add_corp"),
    path("alliance/add/", views.add_alliance, name="add_alliance"),
    # -- Owner Views
    path("owner/<int:owner_id>/view/faq/", views.faq, name="faq"),
    path("owner/<int:owner_id>/view/account/", views.account, name="account"),
    path(
        "owner/<int:owner_id>/view/account/<int:character_id>/",
        views.account,
        name="account",
    ),
    # -- Corporation Tax System
    path(
        "owner/<int:owner_id>/view/manage/",
        views.manage_owner,
        name="manage_owner",
    ),
    path(
        "owner/view/manage/",
        views.manage_owner,
        name="manage_owner",
    ),
    # -- Tax System Views
    path(
        "owner/<int:owner_id>/view/payments/",
        views.payments,
        name="payments",
    ),
    path(
        "owner/<int:owner_id>/view/my-payments/",
        views.my_payments,
        name="my_payments",
    ),
    # -- Tax Manage
    path(
        "owner/<int:owner_id>/manage/update_tax/",
        views.update_tax_amount,
        name="update_tax_amount",
    ),
    path(
        "owner/<int:owner_id>/manage/update_period/",
        views.update_tax_period,
        name="update_tax_period",
    ),
    path(
        "owner/<int:owner_id>/view/filters/",
        views.manage_filter,
        name="manage_filter",
    ),
    # -- API System
    re_path(r"^api/", api.urls),
]

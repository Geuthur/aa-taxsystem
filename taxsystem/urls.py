"""App URLs"""

# Django
from django.urls import path, re_path

# AA TaxSystem
from taxsystem import views
from taxsystem.api import api

app_name: str = "taxsystem"

urlpatterns = [
    # -- Tax System
    path("", views.index, name="index"),
    path("admin/", views.admin, name="admin"),
    path(
        "corporation/<int:corporation_id>/view/payments/",
        views.payments,
        name="payments",
    ),
    path(
        "corporation/<int:corporation_id>/view/own_payments/",
        views.own_payments,
        name="own_payments",
    ),
    path(
        "corporation/<int:corporation_id>/view/administration/",
        views.administration,
        name="administration",
    ),
    path(
        "corporation/<int:corporation_id>/view/filters/",
        views.manage_filter,
        name="manage_filter",
    ),
    path("corporation/<int:corporation_id>/view/faq/", views.faq, name="faq"),
    # --- Tax Administration
    # -- Tax Payments
    path("corporation/add/", views.add_corp, name="add_corp"),
    path(
        "corporation/<int:corporation_id>/payment/<int:payment_pk>/approve/",
        views.approve_payment,
        name="approve_payment",
    ),
    path(
        "corporation/<int:corporation_id>/payment/<int:payment_pk>/undo/",
        views.undo_payment,
        name="undo_payment",
    ),
    path(
        "corporation/<int:corporation_id>/payment/<int:payment_pk>/reject/",
        views.reject_payment,
        name="reject_payment",
    ),
    # -- Tax Manage
    path(
        "corporation/<int:corporation_id>/manage/update_tax/",
        views.update_tax_amount,
        name="update_tax_amount",
    ),
    path(
        "corporation/<int:corporation_id>/manage/update_period/",
        views.update_tax_period,
        name="update_tax_period",
    ),
    path(
        "corporation/<int:corporation_id>/manage/member/<int:member_pk>/delete/",
        views.delete_member,
        name="delete_member",
    ),
    # -- Tax Manage Filters
    path(
        "corporation/<int:corporation_id>/manage/filter_set/<int:filter_set_id>/deactivate/",
        views.switch_filterset,
        name="switch_filterset",
    ),
    path(
        "corporation/<int:corporation_id>/manage/filter_set/<int:filter_set_id>/edit/",
        views.edit_filterset,
        name="edit_filterset",
    ),
    path(
        "corporation/<int:corporation_id>/manage/filter_set/<int:filter_set_id>/delete/",
        views.delete_filterset,
        name="delete_filterset",
    ),
    path(
        "corporation/<int:corporation_id>/manage/filter/<int:filter_pk>/delete/",
        views.delete_filter,
        name="delete_filter",
    ),
    # -- Tax Payment System
    path("corporation/view/account/", views.account, name="account"),
    path("corporation/view/account/<int:character_id>/", views.account, name="account"),
    path(
        "corporation/<int:corporation_id>/manage/user/<int:payment_system_pk>/switch_user/",
        views.switch_user,
        name="switch_user",
    ),
    # -- API System
    re_path(r"^api/", api.urls),
]

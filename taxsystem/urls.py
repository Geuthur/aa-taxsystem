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
    path("view/faq/", views.faq, name="faq"),
    path("admin/", views.admin, name="admin"),
    path("corporation/add/", views.add_corp, name="add_corp"),
    path("alliance/add/", views.add_alliance, name="add_alliance"),
    # -- Corporation Tax System
    path(
        "corporation/<int:corporation_id>/view/payments/",
        views.payments,
        name="payments",
    ),
    path(
        "corporation/view/payments/",
        views.payments,
        name="payments",
    ),
    path(
        "corporation/<int:corporation_id>/view/own-payments/",
        views.own_payments,
        name="own_payments",
    ),
    path(
        "corporation/view/own-payments/",
        views.own_payments,
        name="own_payments",
    ),
    path(
        "corporation/<int:corporation_id>/view/administration/",
        views.manage_corporation,
        name="administration",
    ),
    path(
        "corporation/view/administration/",
        views.manage_corporation,
        name="administration",
    ),
    # -- Corporation Manage
    path(
        "corporation/<int:corporation_id>/manage/member/<int:member_pk>/delete/",
        views.delete_member,
        name="delete_member",
    ),
    # -- Alliance Tax System
    path(
        "alliance/<int:alliance_id>/view/management/",
        views.manage_alliance,
        name="manage_alliance",
    ),
    path(
        "alliance/view/management/",
        views.manage_alliance,
        name="manage_alliance",
    ),
    path(
        "alliance/<int:alliance_id>/view/payments/",
        views.alliance_payments,
        name="alliance_payments",
    ),
    path(
        "alliance/view/payments/",
        views.alliance_payments,
        name="alliance_payments",
    ),
    path(
        "alliance/<int:alliance_id>/view/own-payments/",
        views.alliance_own_payments,
        name="alliance_own_payments",
    ),
    path(
        "alliance/view/own-payments/",
        views.alliance_own_payments,
        name="alliance_own_payments",
    ),
    # -- Tax Payments
    path(
        "owner/<int:owner_id>/payment/<int:payment_system_pk>/add/",
        views.add_payment,
        name="add_payment",
    ),
    path(
        "owner/<int:owner_id>/payment/<int:payment_pk>/delete/",
        views.delete_payment,
        name="delete_payment",
    ),
    path(
        "owner/<int:owner_id>/payment/<int:payment_pk>/approve/",
        views.approve_payment,
        name="approve_payment",
    ),
    path(
        "owner/<int:owner_id>/payment/<int:payment_pk>/undo/",
        views.undo_payment,
        name="undo_payment",
    ),
    path(
        "owner/<int:owner_id>/payment/<int:payment_pk>/reject/",
        views.reject_payment,
        name="reject_payment",
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
        "owner/<int:owner_id>/manage/user/<int:payment_system_pk>/switch_user/",
        views.switch_user,
        name="switch_user",
    ),
    path(
        "owner/<int:owner_id>/view/filters/",
        views.manage_filter,
        name="manage_filter",
    ),
    path(
        "owner/view/filters/",
        views.manage_filter,
        name="manage_filter",
    ),
    path(
        "owner/<int:owner_id>/manage/filter_set/<int:filter_set_id>/deactivate/",
        views.switch_filterset,
        name="switch_filterset",
    ),
    path(
        "owner/<int:owner_id>/manage/filter_set/<int:filter_set_id>/edit/",
        views.edit_filterset,
        name="edit_filterset",
    ),
    path(
        "owner/<int:owner_id>/manage/filter_set/<int:filter_set_id>/delete/",
        views.delete_filterset,
        name="delete_filterset",
    ),
    path(
        "owner/<int:owner_id>/manage/filter/<int:filter_pk>/delete/",
        views.delete_filter,
        name="delete_filter",
    ),
    # -- Tax Payment Account
    path("view/account/", views.account, name="account"),
    path("view/account/<int:character_id>/", views.account, name="account"),
    # -- API System
    re_path(r"^api/", api.urls),
]

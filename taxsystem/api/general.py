# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem import __title__
from taxsystem.api import schema
from taxsystem.helpers import lazy
from taxsystem.models.alliance import AlliancePaymentAccount
from taxsystem.models.corporation import (
    CorporationPaymentAccount,
    Members,
)
from taxsystem.models.general import UserSettings


class ApiEndpoints:
    tags = ["General"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "menu/",
            response={
                HTTPStatus.OK: schema.MenuSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get the navigation menu of the current user",
        )
        def get_menu(request: WSGIRequest):
            user = request.user
            if not user.has_perm("taxsystem.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            left_links = [
                schema.MenuLink(name=_("Overview"), link="/"),
                schema.MenuLink(name=_("Account Overview"), link="/account/"),
                schema.MenuLink(name=_("Settings"), link="/settings/"),
            ]

            right_links = []
            if user.is_superuser or user.has_perm("taxsystem.create_access"):
                right_links += [
                    schema.MenuLink(
                        name=_("Add Corporation"),
                        link=reverse("taxsystem:add_corp"),
                        is_external=True,
                    ),
                    schema.MenuLink(
                        name=_("Add Alliance"),
                        link=reverse("taxsystem:add_alliance"),
                        is_external=True,
                    ),
                ]

            if user.is_superuser:
                right_links.append(
                    schema.MenuLink(name=_("Superadmin"), link="/admin/")
                )

            return schema.MenuSchema(left_links=left_links, right_links=right_links)

        @api.get(
            "user/",
            response={
                HTTPStatus.OK: schema.UserData,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get the current user and permissions",
        )
        def get_user(request: WSGIRequest):
            user = request.user
            if not user.has_perm("taxsystem.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            main_character = getattr(
                getattr(user, "profile", None), "main_character", None
            )

            can_manage = (
                user.is_superuser
                or user.has_perm("taxsystem.manage_corps")
                or user.has_perm("taxsystem.manage_own_corp")
                or user.has_perm("taxsystem.manage_alliances")
                or user.has_perm("taxsystem.manage_own_alliance")
            )
            can_create = user.is_superuser or user.has_perm("taxsystem.create_access")

            if not main_character:
                return schema.UserData(
                    user_id=user.id,
                    is_admin=user.is_superuser,
                    can_manage=can_manage,
                    can_create=can_create,
                )

            return schema.UserData(
                user_id=user.id,
                character_id=main_character.character_id,
                character_name=main_character.character_name,
                corporation_id=main_character.corporation_id,
                corporation_name=main_character.corporation_name,
                alliance_id=main_character.alliance_id,
                alliance_name=main_character.alliance_name,
                portrait=lazy.get_character_portrait_url(
                    character_id=main_character.character_id,
                    size=64,
                ),
                is_admin=user.is_superuser,
                can_manage=can_manage,
                can_create=can_create,
            )

        @api.get(
            "settings/",
            response={
                HTTPStatus.OK: schema.UserSettingsSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get the settings of the current user",
        )
        def get_user_settings(request: WSGIRequest):
            if not request.user.has_perm("taxsystem.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            settings, __ = UserSettings.objects.get_or_create(user=request.user)
            return schema.UserSettingsSchema(
                disable_notifications=settings.disable_notifications
            )

        @api.put(
            "settings/",
            response={
                HTTPStatus.OK: schema.UserSettingsSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Update the settings of the current user",
        )
        def update_user_settings(
            request: WSGIRequest, payload: schema.UserSettingsUpdateRequest
        ):
            if not request.user.has_perm("taxsystem.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            settings, __ = UserSettings.objects.get_or_create(user=request.user)
            settings.disable_notifications = payload.disable_notifications
            settings.save()
            return schema.UserSettingsSchema(
                disable_notifications=settings.disable_notifications
            )

        @api.get(
            "user/accounts/",
            response={
                HTTPStatus.OK: list[schema.UserAccountSchema],
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get all tax accounts for the current user",
        )
        def get_user_accounts(request: WSGIRequest):
            user = request.user
            if not user.has_perm("taxsystem.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            accounts: list[schema.UserAccountSchema] = []

            main_char = getattr(getattr(user, "profile", None), "main_character", None)
            char_id = main_char.character_id if main_char else None
            char_name = main_char.character_name if main_char else None
            portrait = (
                lazy.get_character_portrait_url(char_id, size=64) if char_id else None
            )

            # Fetch Corporation Accounts for this user
            for tax_account in CorporationPaymentAccount.objects.filter(
                user=user
            ).select_related("owner__eve_corporation"):
                owner = tax_account.owner
                member = None
                if char_id:
                    member = Members.objects.filter(
                        owner=owner, character_id=char_id
                    ).first()

                open_inv = owner.payment_model.objects.get_owner_open_invoices(
                    user=user, owner=owner
                )

                accounts.append(
                    schema.UserAccountSchema(
                        id=tax_account.pk,
                        name=tax_account.name,
                        owner_id=owner.eve_corporation.corporation_id,
                        owner_name=owner.eve_corporation.corporation_name,
                        owner_type="corporation",
                        owner_logo=lazy.get_corporation_logo_url(
                            owner.eve_corporation.corporation_id, size=64
                        ),
                        character_id=char_id,
                        character_name=char_name,
                        character_portrait=portrait,
                        status=tax_account.status,
                        status_display=tax_account.get_status_display(),
                        deposit=float(tax_account.deposit),
                        tax_amount=float(owner.tax_amount),
                        tax_period=owner.tax_period,
                        has_paid=tax_account.has_paid,
                        last_paid=(
                            tax_account.last_paid.strftime("%Y-%m-%d %H:%M:%S")
                            if tax_account.last_paid
                            else None
                        ),
                        next_due=(
                            tax_account.next_due.strftime("%Y-%m-%d %H:%M:%S")
                            if tax_account.next_due
                            else None
                        ),
                        joined=(
                            member.joined.strftime("%Y-%m-%d %H:%M:%S")
                            if member and member.joined
                            else None
                        ),
                        last_login=(
                            member.logon.strftime("%Y-%m-%d %H:%M:%S")
                            if member and member.logon
                            else None
                        ),
                        notice=tax_account.notice,
                        open_invoices=open_inv,
                        is_main=tax_account.is_main,
                    )
                )

            # Fetch Alliance Accounts for this user
            for tax_account in AlliancePaymentAccount.objects.filter(
                user=user
            ).select_related("owner__eve_alliance"):
                owner = tax_account.owner
                open_inv = owner.payment_model.objects.get_owner_open_invoices(
                    user=user, owner=owner
                )

                accounts.append(
                    schema.UserAccountSchema(
                        id=tax_account.pk,
                        name=tax_account.name,
                        owner_id=owner.eve_alliance.alliance_id,
                        owner_name=owner.eve_alliance.alliance_name,
                        owner_type="alliance",
                        owner_logo=lazy.get_alliance_logo_url(
                            owner.eve_alliance.alliance_id, size=64
                        ),
                        character_id=char_id,
                        character_name=char_name,
                        character_portrait=portrait,
                        status=tax_account.status,
                        status_display=tax_account.get_status_display(),
                        deposit=float(tax_account.deposit),
                        tax_amount=float(owner.tax_amount),
                        tax_period=owner.tax_period,
                        has_paid=tax_account.has_paid,
                        last_paid=(
                            tax_account.last_paid.strftime("%Y-%m-%d %H:%M:%S")
                            if tax_account.last_paid
                            else None
                        ),
                        next_due=(
                            tax_account.next_due.strftime("%Y-%m-%d %H:%M:%S")
                            if tax_account.next_due
                            else None
                        ),
                        joined=None,
                        last_login=None,
                        notice=tax_account.notice,
                        open_invoices=open_inv,
                        is_main=tax_account.is_main,
                    )
                )

            return HTTPStatus.OK, accounts

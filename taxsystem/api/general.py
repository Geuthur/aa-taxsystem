# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem import __title__, tasks
from taxsystem.api import schema
from taxsystem.helpers import lazy
from taxsystem.models.alliance import (
    AllianceOwner,
    AlliancePaymentAccount,
    AllianceUpdateStatus,
)
from taxsystem.models.corporation import (
    CorporationOwner,
    CorporationPaymentAccount,
    CorporationUpdateStatus,
    Members,
)
from taxsystem.models.general import General, UserSettings
from taxsystem.models.helpers.update_manager import (
    AllianceUpdateSection,
    CorporationUpdateSection,
    UpdateStatus,
)


# pylint: disable=too-many-locals
def _build_tax_owner_setting_schema(
    owner: CorporationOwner | AllianceOwner, user
) -> schema.TaxOwnerSettingSchema:
    if isinstance(owner, CorporationOwner):
        owner_id = owner.eve_corporation.corporation_id
        name = owner.eve_corporation.corporation_name
        ticker = getattr(owner.eve_corporation, "ticker", None)
        icon = lazy.get_corporation_logo_url(owner_id, size=64)
        owner_type = "corporation"
        sections_enum = CorporationUpdateSection
        status_model = CorporationUpdateStatus
    else:
        owner_id = owner.eve_alliance.alliance_id
        name = owner.eve_alliance.alliance_name
        ticker = getattr(owner.eve_alliance, "ticker", None)
        icon = lazy.get_alliance_logo_url(owner_id, size=64)
        owner_type = "alliance"
        sections_enum = AllianceUpdateSection
        status_model = AllianceUpdateStatus

    status_records = {s.section: s for s in status_model.objects.filter(owner=owner)}
    section_list: list[schema.OwnerSectionSchema] = []
    last_sync_dt = None
    latest_err = None

    for sec in sections_enum:
        sec_record = status_records.get(sec.value)
        if sec_record:
            if sec_record.last_run_finished_at and (
                last_sync_dt is None or sec_record.last_run_finished_at > last_sync_dt
            ):
                last_sync_dt = sec_record.last_run_finished_at
            if sec_record.error_message and not latest_err:
                latest_err = sec_record.error_message

            section_list.append(
                schema.OwnerSectionSchema(
                    section=sec.value,
                    section_name=str(sec.label),
                    is_success=sec_record.is_success,
                    has_token_error=sec_record.has_token_error,
                    error_message=sec_record.error_message or None,
                    last_update_finished_at=(
                        sec_record.last_update_finished_at.strftime("%Y-%m-%d %H:%M")
                        if sec_record.last_update_finished_at
                        else None
                    ),
                )
            )
        else:
            section_list.append(
                schema.OwnerSectionSchema(
                    section=sec.value,
                    section_name=str(sec.label),
                    is_success=None,
                    has_token_error=False,
                    error_message=None,
                    last_update_finished_at=None,
                )
            )

    open_inv = int(
        owner.payment_model.objects.get_owner_open_invoices(user=user, owner=owner) or 0
    )

    last_sync_str = last_sync_dt.strftime("%Y-%m-%d %H:%M") if last_sync_dt else None

    return schema.TaxOwnerSettingSchema(
        id=owner.id,
        owner_id=owner_id,
        owner_type=owner_type,
        name=name,
        icon=icon,
        ticker=ticker,
        status=str(owner.get_status),
        is_active=owner.active,
        tax_amount=float(owner.tax_amount),
        tax_period=owner.tax_period,
        open_invoices=open_inv,
        last_sync=last_sync_str,
        error_message=latest_err,
        sections=section_list,
    )


class ApiEndpoints:
    tags = ["General"]

    # pylint: disable=too-many-statements
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
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            has_owner_errors = False
            for corp in CorporationOwner.objects.manage_to(user):
                if corp.get_status in (UpdateStatus.ERROR, UpdateStatus.TOKEN_ERROR):
                    has_owner_errors = True
                    break
            if not has_owner_errors:
                for ally in AllianceOwner.objects.manage_to(user):
                    if ally.get_status in (
                        UpdateStatus.ERROR,
                        UpdateStatus.TOKEN_ERROR,
                    ):
                        has_owner_errors = True
                        break

            left_links = [
                schema.MenuLink(name=_("Overview"), link="/"),
                schema.MenuLink(name=_("Account Overview"), link="/account/"),
                schema.MenuLink(
                    name=_("Settings"),
                    link="/settings/",
                    has_errors=has_owner_errors,
                ),
            ]

            right_links = []
            if General.has_perm(user, General.Permission.CREATE_ACCESS):
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

            if General.has_administration_access(user):
                right_links.append(
                    schema.MenuLink(name=_("Administration"), link="/administration/")
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
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            main_character = getattr(
                getattr(user, "profile", None), "main_character", None
            )

            can_manage = General.has_any_perm(
                user,
                General.Permission.MANAGE_CORPS,
                General.Permission.MANAGE_OWN_CORP,
                General.Permission.MANAGE_ALLIANCES,
                General.Permission.MANAGE_OWN_ALLIANCE,
            )
            can_create = General.has_perm(user, General.Permission.CREATE_ACCESS)
            is_admin = General.has_administration_access(user)
            is_superuser = bool(user.is_superuser)

            if not main_character:
                return schema.UserData(
                    user_id=user.id,
                    is_admin=is_admin,
                    is_superuser=is_superuser,
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
                is_admin=is_admin,
                is_superuser=is_superuser,
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
            if not General.has_perm(request.user, General.Permission.BASIC_ACCESS):
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
            if not General.has_perm(request.user, General.Permission.BASIC_ACCESS):
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
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
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

        @api.get(
            "settings/owners/",
            response={
                HTTPStatus.OK: list[schema.TaxOwnerSettingSchema],
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get settings update status for all manageable owners",
        )
        def get_settings_owners(request: WSGIRequest):
            if not General.has_perm(request.user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            owners_list: list[schema.TaxOwnerSettingSchema] = []
            for corp in (
                CorporationOwner.objects.manage_to(request.user)
                .select_related("eve_corporation")
                .order_by("eve_corporation__corporation_name")
            ):
                owners_list.append(_build_tax_owner_setting_schema(corp, request.user))

            for ally in (
                AllianceOwner.objects.manage_to(request.user)
                .select_related("eve_alliance")
                .order_by("eve_alliance__alliance_name")
            ):
                owners_list.append(_build_tax_owner_setting_schema(ally, request.user))

            return HTTPStatus.OK, owners_list

        @api.post(
            "settings/owners/update-all/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Trigger update tasks for all manageable owners with force_refresh=false",
        )
        def trigger_update_all_owners(
            request: WSGIRequest,
            payload: schema.OwnerUpdateRequest | None = None,
        ):
            if not General.has_perm(request.user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            force_refresh = payload.force_refresh if payload else False
            count = 0
            for corp in CorporationOwner.objects.manage_to(request.user):
                tasks.update_corporation.apply_async(
                    args=[corp.eve_id],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
                count += 1

            for ally in AllianceOwner.objects.manage_to(request.user):
                tasks.update_alliance.apply_async(
                    args=[ally.eve_id],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
                count += 1

            return HTTPStatus.OK, {
                "message": _("Queued updates for %(count)d owner(s).")
                % {"count": count}
            }

# Standard Library
from typing import Literal

# Third Party
from ninja import Schema
from pydantic import field_validator

# Django
from django.utils.timezone import datetime


class ErrorSchema(Schema):
    """Schema for error responses."""

    error: str

    @field_validator("error", mode="before")
    @classmethod
    def coerce_error(cls, v):
        return str(v)


class MessageSchema(Schema):
    """Schema for simple success responses."""

    message: str

    @field_validator("message", mode="before")
    @classmethod
    def coerce_message(cls, v):
        return str(v)


class MenuLink(Schema):
    """A navigation link. `link` is relative to the app root unless `is_external` is set."""

    name: str
    link: str
    badge: int | None = None
    is_external: bool = False


class MenuSchema(Schema):
    """The navigation menu of the application."""

    left_links: list[MenuLink] = []
    right_links: list[MenuLink] = []


class UserData(Schema):
    """The current user, main character and permissions."""

    user_id: int
    character_id: int = 0
    character_name: str = ""
    corporation_id: int = 0
    corporation_name: str = ""
    alliance_id: int | None = None
    alliance_name: str | None = None
    portrait: str | None = None
    is_admin: bool = False
    can_manage: bool = False
    can_create: bool = False


class UserSettingsSchema(Schema):
    """User notification preferences."""

    disable_notifications: bool


class UserSettingsUpdateRequest(Schema):
    """Request to update user notification preferences."""

    disable_notifications: bool


class AdminUpdateRequest(Schema):
    """Request to trigger background update tasks."""

    target: Literal["all", "corporation", "alliance"]
    eve_id: int | None = None
    force_refresh: bool = False


class OwnerOverviewSchema(Schema):
    """Overview item for an owner corporation or alliance."""

    id: int
    name: str
    type: Literal["corporation", "alliance"]
    type_display: str
    portrait_url: str
    active: bool
    open_invoices: int
    can_manage: bool


class OverviewSchema(Schema):
    """List of all visible owners."""

    owners: list[OwnerOverviewSchema]
    total_count: int


class DataTableSchema(Schema):
    """Legacy DataTable wrapper schema (kept for backwards compatibility)."""

    raw: str | int | float | bool
    display: str
    sort: str | None = None
    translation: str | None = None
    dropdown_text: str | None = None


class RequestStatusSchema(Schema):
    status: str
    code: str | None = None
    color: str | None = None
    icon: str | None = None
    html: str | None = None


class UpdateStatusSchema(RequestStatusSchema):
    status: dict


class OwnerSchema(Schema):
    owner_id: int
    owner_name: str
    owner_type: str | None = None
    owner_portrait: str | None = None


class CharacterSchema(Schema):
    character_id: int
    character_name: str
    character_portrait: str | None = None
    corporation_id: int | None = None
    corporation_name: str | None = None
    alliance_id: int | None = None
    alliance_name: str | None = None
    display: str | None = None


class CorporationSchema(OwnerSchema):
    corporation_id: int
    corporation_name: str
    corporation_portrait: str | None = None
    corporation_ticker: str | None = None


class AllianceSchema(OwnerSchema):
    alliance_id: int
    alliance_name: str
    alliance_logo: str | None = None
    alliance_ticker: str | None = None
    main_corporation_id: int
    main_corporation_name: str | None = None
    main_corporation_ticker: str | None = None


class AccountSchema(CharacterSchema):
    alt_ids: list[int] | None = None


class MembersSchema(Schema):
    character: CharacterSchema
    is_missing: bool
    is_noaccount: bool
    status: str
    joined: datetime
    actions: str | None = None


class DeletePaymentRequest(Schema):
    comment: str = "Deleted via TaxSystem"


class PaymentSchema(Schema):
    payment_id: int
    amount: int
    date: str
    request_status: RequestStatusSchema
    division_name: str
    reason: str
    reviser: str
    is_custom: bool = False
    can_delete: bool = False
    can_approve: bool = False
    can_reject: bool = False
    can_undo: bool = False
    actions: str | None = None


class PaymentCorporationSchema(PaymentSchema):
    character: CharacterSchema


class PaymentSystemSchema(Schema):
    account_id: int | None = None
    account: AccountSchema
    status: str
    deposit: int
    has_paid: bool | DataTableSchema
    last_paid: datetime | None = None
    next_due: datetime | None = None
    is_active: bool
    actions: str | None = None


class DivisionSchema(Schema):
    name: str
    balance: float


class DashboardDivisionsSchema(Schema):
    divisions: list[DivisionSchema]
    total_balance: float


class PaymentHistorySchema(Schema):
    log_id: int
    reviser: str
    date: str
    action: str
    comment: str
    status: str


class AdminHistorySchema(Schema):
    log_id: int
    user_name: str
    date: str
    target: str
    action: str | DataTableSchema
    comment: str


class FilterSetModelSchema(Schema):
    id: int | None = None
    owner_id: int
    name: str
    description: str
    enabled: bool
    status: bool | DataTableSchema | None = None
    actions: str | None = None


class FilterModelSchema(Schema):
    id: int | None = None
    filter_set: FilterSetModelSchema
    filter_type: str
    match_type: str
    value: str | DataTableSchema
    actions: str | None = None


class GroupSchema(Schema):
    id: int
    name: str


class GroupManagementSchema(Schema):
    id: int | None = None
    name: str
    groups: list[GroupSchema] | None = None
    actions: str | None = None


class TaxAccountSchema(Schema):
    account_id: int
    account_name: str
    account_status: str
    character: CharacterSchema
    payment_pool: int


class PaymentsDetailsResponse(Schema):
    owner: OwnerSchema
    account: TaxAccountSchema
    payment: PaymentSchema
    payment_histories: list[PaymentHistorySchema]


class CreateFilterSetRequest(Schema):
    name: str
    description: str = ""


class CreateFilterRequest(Schema):
    filter_set_id: int
    filter_type: Literal["reason", "amount"]
    match_type: Literal["exact", "contains"]
    value: str


class CreateGroupRequest(Schema):
    name: str
    group_ids: list[int]


class AddPaymentRequest(Schema):
    amount: int
    comment: str


class UserAccountSchema(Schema):
    id: int
    name: str
    owner_id: int
    owner_name: str
    owner_type: str
    owner_logo: str | None = None
    character_id: int | None = None
    character_name: str | None = None
    character_portrait: str | None = None
    status: str
    status_display: str
    deposit: float
    tax_amount: float
    tax_period: int
    has_paid: bool
    last_paid: str | None = None
    next_due: str | None = None
    joined: str | None = None
    last_login: str | None = None
    notice: str | None = None
    open_invoices: int = 0


class ActionCommentRequest(Schema):
    comment: str = ""


class BulkActionPaymentsRequest(Schema):
    pks: list[int]
    action: Literal["approve", "reject"]
    comment: str = ""


class BulkActionAccountsRequest(Schema):
    pks: list[int]
    action: Literal["activate", "deactivate"]
    comment: str = ""


class UpdateTaxAmountRequest(Schema):
    tax_amount: float


class UpdateTaxPeriodRequest(Schema):
    tax_period: int

# Third Party
from ninja import Schema

# Django
from django.utils.timezone import datetime


class DataTableSchema(Schema):
    raw: str | int | float | bool
    display: str
    sort: str | None = None
    translation: str | None = None
    dropdown_text: str | None = None


class RequestStatusSchema(Schema):
    status: str
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


class PaymentSchema(Schema):
    payment_id: int
    amount: int
    date: str
    request_status: RequestStatusSchema
    division_name: str
    reason: str
    reviser: str
    actions: str | None = None


class PaymentSystemSchema(Schema):
    account: AccountSchema
    status: str
    deposit: int
    has_paid: DataTableSchema
    last_paid: datetime | None = None
    next_due: datetime | None = None
    is_active: bool
    actions: str


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
    action: str
    comment: str


class FilterSetModelSchema(Schema):
    owner_id: int
    name: str
    description: str
    enabled: bool
    status: DataTableSchema | None = None
    actions: str | None = None


class FilterModelSchema(Schema):
    filter_set: FilterSetModelSchema
    filter_type: str
    match_type: str
    value: str | DataTableSchema
    actions: str | None = None

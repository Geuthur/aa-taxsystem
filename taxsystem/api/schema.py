# Third Party
from ninja import Schema


class DataTableSchema(Schema):
    raw: str
    display: str
    sort: str | None = None
    translation: str | None = None
    dropdown_text: str | None = None


class CorporationSchema(Schema):
    corporation_id: int
    corporation_name: str
    corporation_portrait: str | None = None
    corporation_ticker: str | None = None


class CharacterSchema(Schema):
    character_id: int
    character_name: str
    character_portrait: str | None = None
    corporation_id: int | None = None
    corporation_name: str | None = None
    alliance_id: int | None = None
    alliance_name: str | None = None


class AccountSchema(CharacterSchema):
    alt_ids: list[int] | None = None


class RequestStatusSchema(Schema):
    status: str
    color: str | None = None
    icon: str | None = None
    html: str | None = None


class UpdateStatusSchema(RequestStatusSchema):
    status: dict


class PaymentSchema(Schema):
    payment_id: int
    amount: int
    date: str
    request_status: RequestStatusSchema
    division_name: str
    reason: str
    reviser: str
    actions: str | None = None


class LogHistorySchema(Schema):
    log_id: int
    reviser: str
    date: str
    action: str
    comment: str
    status: str

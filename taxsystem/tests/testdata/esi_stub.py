# Standard Library
import json
from pathlib import Path

# Alliance Auth (External Libs)
from app_utils.esi_testing import EsiClientStub, EsiClientStubOpenApi, EsiEndpoint


def load_test_data():
    file_path = Path(__file__).parent / "esi.json"
    with file_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


_esi_data = load_test_data()

_endpoints = [
    EsiEndpoint(
        "Character",
        "GetCharactersCharacterIdRoles",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Corporation",
        "GetCorporationsCorporationIdDivisions",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Corporation",
        "GetCorporationsCorporationIdMembertracking",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWallets",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWalletsDivisionJournal",
        "corporation_id",
        needs_token=False,
    ),
]

esi_client_stub = EsiClientStub(_esi_data, endpoints=_endpoints)
esi_client_stub_openapi = EsiClientStubOpenApi(_esi_data, endpoints=_endpoints)
esi_client_error_stub = EsiClientStub(_esi_data, endpoints=_endpoints, http_error=502)

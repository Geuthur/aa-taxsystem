from .admin import AdminApiEndpoints
from .character import CharacterApiEndpoints
from .corporation import CorporationApiEndpoints


def setup(api):
    AdminApiEndpoints(api)
    CorporationApiEndpoints(api)
    CharacterApiEndpoints(api)

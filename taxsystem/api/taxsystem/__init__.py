from .admin import AdminApiEndpoints
from .corporation import CorporationApiEndpoints


def setup(api):
    AdminApiEndpoints(api)
    CorporationApiEndpoints(api)

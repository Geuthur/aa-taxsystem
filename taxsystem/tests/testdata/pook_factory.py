# Standard Library
from http import HTTPStatus

# Third Party
import pook

ESI_BASE_URL = "https://esi.evetech.net"


class PookFactory:
    """
    Factory class for creating Pook mock responses for ESI API calls in tests.
    This class provides static methods to create mock responses for various ESI endpoints, allowing for consistent and reusable test setups.
    """

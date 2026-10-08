# Standard Library
import json
from typing import cast

# Third Party
from ninja.parser import Parser
from ninja.types import DictStrAny

# Django
from django.http import HttpRequest


class SafeNinjaParser(Parser):
    """
    Parser that safely handles empty request bodies without throwing 400 errors.
    If the body is empty or not valid JSON, returns an empty dictionary.
    """

    def parse_body(self, request: HttpRequest) -> DictStrAny:
        if not getattr(request, "body", None):
            return {}
        try:
            return cast(DictStrAny, json.loads(request.body))
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            return {}

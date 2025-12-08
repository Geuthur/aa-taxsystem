"""
ESI OpenAPI Client Stub for Testing

This module provides a stub implementation for ESI OpenAPI clients that can be used
in tests to return predefined test data without making actual API calls.
"""

# Standard Library
import json
from pathlib import Path
from typing import Any

# Third Party
from pydantic import BaseModel, create_model


def _to_pydantic_model_instance(name: str, data: Any) -> Any:
    """
    Recursively convert dicts/lists to Pydantic model instances.
    """
    # Lists -> convert each item
    if isinstance(data, list):
        return [_to_pydantic_model_instance(name + "Item", v) for v in data]

    # Dicts -> create a transient pydantic model class and instantiate it
    if isinstance(data, dict):
        fields: dict[str, tuple[type, Any]] = {}
        values: dict[str, Any] = {}
        for k, v in data.items():
            # Use Any for field type; instantiate nested models recursively
            fields[k] = (Any, ...)
            values[k] = _to_pydantic_model_instance(name + k.capitalize(), v)

        Model = create_model(name, **fields, __base__=BaseModel)
        return Model(**values)

    # Primitives -> return as-is
    return data


class MockResponse:
    """
    Mock HTTP response object for testing.

    Mimics the response object returned by ESI when return_response=True.
    """

    def __init__(self, status_code: int = 200, headers: dict | None = None):
        """
        Initialize mock response.

        :param status_code: HTTP status code
        :type status_code: int
        :param headers: Response headers
        :type headers: dict | None
        """
        self.status_code = status_code
        self.headers = headers or {"X-Pages": 1}
        self.text = ""
        self.content = b""


class EsiEndpoint:
    """
    Definition of an ESI endpoint for stub configuration.

    Defines which endpoints should be stubbed and with what side effects.
    """

    def __init__(
        self,
        category: str,
        method: str,
        param_names: str | tuple[str, ...],
        side_effect: Exception | None = None,
    ):
        """
        Initialize an ESI endpoint definition.

        :param category: ESI category name (e.g., "Character", "Skills")
        :type category: str
        :param method: ESI method name (e.g., "GetCharactersCharacterIdSkills")
        :type method: str
        :param param_names: Parameter name(s) used to look up test data
        :type param_names: str | tuple[str, ...]
        :param side_effect: Optional exception to raise when this endpoint is called
        :type side_effect: Exception | None
        """
        self.category = category
        self.method = method
        self.param_names = (
            param_names if isinstance(param_names, tuple) else (param_names,)
        )
        self.side_effect = side_effect

    def __repr__(self):
        return f"EsiEndpoint({self.category}.{self.method})"


class EsiOperationStub:
    """
    Stub for ESI operation that mimics the behavior of openapi_clients operations.

    This class simulates the result() and results() methods that are called on
    ESI operations in the actual implementation.

    If a side_effect is configured, calling result() or results() will raise that exception
    instead of returning test data.
    """

    def __init__(self, test_data: Any, side_effect: Exception | None = None):
        """
        Initialize the operation stub with test data or side effect.

        :param test_data: The data to return when result() or results() is called
        :type test_data: Any
        :param side_effect: Exception to raise when result() or results() is called
        :type side_effect: Exception | None
        """
        self._test_data = test_data
        self._side_effect = side_effect

    def result(
        self,
        use_etag: bool = True,  # not implemented yet
        return_response: bool = False,
        force_refresh: bool = False,  # not implemented yet
        use_cache: bool = True,  # not implemented yet
        **kwargs,
    ) -> Any:
        """
        Simulate the result() method of an ESI operation.

        Returns a single result (not a list) as an object with attributes.
        When return_response=True, returns tuple of (data, response).

        If a side_effect was configured, raises that exception instead.

        :param use_etag: Whether to use ETag (ignored in stub)
        :type use_etag: bool
        :param return_response: Whether to return response object
        :type return_response: bool
        :param force_refresh: Whether to force refresh (ignored in stub)
        :type force_refresh: bool
        :param use_cache: Whether to use cache (ignored in stub)
        :type use_cache: bool
        :return: Test data as object, or tuple of (data, response) if return_response=True
        :rtype: Any
        :raises: Exception if side_effect was configured
        """
        # If side_effect is configured, raise it
        if self._side_effect is not None:
            # Support both exception instances and lists of exceptions/values
            if isinstance(self._side_effect, list):
                # Pop from list for sequential side effects
                if self._side_effect:
                    effect = self._side_effect.pop(0)
                    if isinstance(effect, Exception):
                        raise effect
                    # If not an exception, return it as data
                    return (
                        _to_pydantic_model_instance("SideEffect", effect)
                        if not return_response
                        else (
                            _to_pydantic_model_instance("SideEffect", effect),
                            MockResponse(),
                        )
                    )
            elif isinstance(self._side_effect, Exception):
                raise self._side_effect

        # Convert dict to Pydantic model instance to mimic OpenAPI 3 behavior
        data = _to_pydantic_model_instance("Result", self._test_data)

        if return_response:
            # Return tuple of (data, response)
            response = MockResponse()
            return (data, response)

        return data

    def results(
        self,
        use_etag: bool = True,  # not implemented yet
        return_response: bool = False,
        force_refresh: bool = False,  # not implemented yet
        use_cache: bool = True,  # not implemented yet
        **kwargs,
    ) -> list[Any]:
        """
        Simulate the results() method of an ESI operation.

        Returns a list of results (paginated data) as objects with attributes.
        When return_response=True, returns tuple of (data, response).

        If a side_effect was configured, raises that exception instead.

        :param use_etag: Whether to use ETag (ignored in stub)
        :type use_etag: bool
        :param return_response: Whether to return response object
        :type return_response: bool
        :param force_refresh: Whether to force refresh (ignored in stub)
        :type force_refresh: bool
        :param use_cache: Whether to use cache (ignored in stub)
        :type use_cache: bool
        :return: Test data as list of objects, or tuple of (data, response) if return_response=True
        :rtype: list[Any]
        :raises: Exception if side_effect was configured
        """
        # If side_effect is configured, raise it
        if self._side_effect is not None:
            # Support both exception instances and lists of exceptions/values
            if isinstance(self._side_effect, list):
                # Pop from list for sequential side effects
                if self._side_effect:
                    effect = self._side_effect.pop(0)
                    if isinstance(effect, Exception):
                        raise effect
                    # If not an exception, return it as data
                    data = _to_pydantic_model_instance("SideEffect", effect)
                    result_data = data if isinstance(data, list) else [data]
                    return (
                        (result_data, MockResponse())
                        if return_response
                        else result_data
                    )
            elif isinstance(self._side_effect, Exception):
                raise self._side_effect

        # Convert to Pydantic model instances first
        data = _to_pydantic_model_instance("Results", self._test_data)

        # If test data is already a list, use it as is
        if isinstance(data, list):
            result_data = data
        else:
            # If single item, wrap in list
            result_data = [data]

        if return_response:
            # Return tuple of (data, response)
            response = MockResponse()
            return (result_data, response)

        return result_data


class EsiCategoryStub:
    """
    Stub for an ESI category (e.g., Skills, Character, Wallet).

    This class holds methods for a specific ESI category and returns
    EsiOperationStub instances when methods are called.
    """

    def __init__(
        self,
        category_name: str,
        test_data: dict[str, Any],
        endpoints: dict[str, EsiEndpoint],
    ):
        """
        Initialize the category stub.

        :param category_name: Name of the ESI category (e.g., "Skills")
        :type category_name: str
        :param test_data: Dictionary mapping method names to test data
        :type test_data: dict[str, Any]
        :param endpoints: Dictionary mapping method names to endpoint definitions
        :type endpoints: dict[str, EsiEndpoint]
        """
        self._category_name = category_name
        self._test_data = test_data
        self._endpoints = endpoints

    def __getattr__(self, method_name: str) -> callable:
        """
        Return a callable that creates an EsiOperationStub when invoked.

        :param method_name: Name of the ESI method
        :type method_name: str
        :return: Callable that returns EsiOperationStub
        :rtype: callable
        """

        def operation_caller(**kwargs) -> EsiOperationStub:
            """
            Create and return an operation stub with test data and optional side effect.

            :return: Operation stub with test data
            :rtype: EsiOperationStub
            :raises AttributeError: If endpoints were provided and this method is not registered
            """
            # Check if endpoint is registered
            endpoint = self._endpoints.get(method_name)

            # Only registered methods are allowed
            if endpoint is None:
                raise AttributeError(
                    f"Method '{self._category_name}.{method_name}' is not registered. "
                    f"Available methods: {list(self._endpoints.keys())}"
                )

            # Look up test data for this method
            method_data = self._test_data.get(method_name, {})

            # If method_data is callable, call it with the kwargs to get dynamic data
            if callable(method_data):
                data = method_data(**kwargs)
            else:
                data = method_data

            # Get side effect from endpoint if defined
            side_effect = endpoint.side_effect if endpoint else None

            return EsiOperationStub(test_data=data, side_effect=side_effect)

        return operation_caller


class EsiClientStub:
    """
    Stub for ESI OpenAPI client that mimics ESIClientProvider.client.

    This class provides access to ESI categories and their methods,
    returning test data instead of making real API calls.
    """

    def __init__(
        self,
        test_data_config: dict[str, dict[str, Any]],
        endpoints: list[EsiEndpoint],
    ):
        """
        Initialize the ESI client stub.

        :param test_data_config: Dictionary mapping category names to their method data
                                 Format: {"CategoryName": {"MethodName": test_data}}
        :type test_data_config: dict[str, dict[str, Any]]
        :param endpoints: List of endpoint definitions (REQUIRED). Only these endpoints will be available.
        :type endpoints: list[EsiEndpoint]
        :raises ValueError: If endpoints is None or empty
        """
        if not endpoints:
            raise ValueError(
                "endpoints parameter is required and cannot be empty. "
                "You must provide a list of EsiEndpoint definitions."
            )

        self._test_data_config = test_data_config
        self._categories = {}
        self._endpoints_by_category = {}

        # Build endpoint lookup by category and method
        for endpoint in endpoints:
            if endpoint.category not in self._endpoints_by_category:
                self._endpoints_by_category[endpoint.category] = {}
            self._endpoints_by_category[endpoint.category][endpoint.method] = endpoint

        # Create category stubs only for categories that have registered endpoints
        for category_name in self._endpoints_by_category.keys():
            methods_data = test_data_config.get(category_name, {})
            category_endpoints = self._endpoints_by_category[category_name]
            self._categories[category_name] = EsiCategoryStub(
                category_name=category_name,
                test_data=methods_data,
                endpoints=category_endpoints,
            )

    def __getattr__(self, category_name: str) -> EsiCategoryStub:
        """
        Return the category stub for the requested ESI category.

        :param category_name: Name of the ESI category
        :type category_name: str
        :return: Category stub
        :rtype: EsiCategoryStub
        :raises AttributeError: If category is not registered in endpoints
        """
        if category_name in self._categories:
            return self._categories[category_name]

        # Only registered categories are allowed
        raise AttributeError(
            f"Category '{category_name}' is not registered. "
            f"Available categories: {list(self._categories.keys())}"
        )


def load_test_data_from_json(file_name: str = "esi_test_data.json") -> dict:
    """
    Load test data from a JSON file in the testdata directory.

    :param file_name: Name of the JSON file
    :type file_name: str
    :return: Loaded test data
    :rtype: dict
    """
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        return {}

    with file_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def create_esi_client_stub(
    test_data_config: dict[str, dict[str, Any]] | None = None,
    endpoints: list[EsiEndpoint] | None = None,
) -> EsiClientStub:
    """
    Create an ESI client stub with the provided test data configuration.

    :param test_data_config: Test data configuration, if None loads from JSON file
    :type test_data_config: dict[str, dict[str, Any]] | None
    :param endpoints: List of endpoint definitions (REQUIRED)
    :type endpoints: list[EsiEndpoint] | None
    :return: ESI client stub
    :rtype: EsiClientStub
    :raises ValueError: If endpoints is None or empty
    """
    if test_data_config is None:
        test_data_config = load_test_data_from_json()

    if not endpoints:
        raise ValueError(
            "endpoints parameter is required. "
            "You must provide a list of EsiEndpoint definitions."
        )

    return EsiClientStub(test_data_config=test_data_config, endpoints=endpoints)

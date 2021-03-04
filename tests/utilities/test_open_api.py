from copy import deepcopy
from unittest.mock import create_autospec
from unittest.mock import patch

from fastapi import FastAPI
from pytest import fixture
from starlette.routing import BaseRoute

from src.utilities.openapi.open_api import create_custom_openapi_function
from src.utilities.openapi.open_api import remove_422_responses
from src.utilities.openapi.open_api import remove_validation_error_schema

EXPECTED = {
    "paths": {
        "/foo": {"post": {"responses": {"200": {}}}},
        "/bar": {"put": {"responses": {"200": {}, "404": {}}}},
    },
    "components": {"schemas": {}},
}


@fixture
def patched_get_openapi():
    with patch(
        "src.utilities.openapi.open_api.get_openapi", autospec=True
    ) as mocked_get_openapi:
        mocked_get_openapi.return_value = EXPECTED
        yield mocked_get_openapi


@fixture
def fastapi_app_stub():
    stub = create_autospec(FastAPI)
    stub.openapi_schema = None
    yield stub


def test_remove_422_responses_works_when_422_responses_exist():
    original = deepcopy(EXPECTED)
    original["paths"]["/foo"]["post"]["responses"]["422"] = {}
    original["paths"]["/bar"]["put"]["responses"]["422"] = {}

    remove_422_responses(original)
    assert original == EXPECTED


def test_remove_422_responses_works_when_422_responses_do_not_exist():
    original = deepcopy(EXPECTED)
    remove_422_responses(original)
    assert original == EXPECTED


def test_remove_validation_error_schema_works_when_schemas_exist():
    original = deepcopy(EXPECTED)
    original["components"]["schemas"]["HTTPValidationError"] = {}
    original["components"]["schemas"]["ValidationError"] = {}
    remove_validation_error_schema(original)
    assert original == EXPECTED


def test_remove_validation_error_schema_works_when_schemas_do_not_exist():
    original = deepcopy(EXPECTED)
    remove_validation_error_schema(original)
    assert original == EXPECTED


def test_create_custom_openapi_function_returns_callable_as_expected(
    patched_get_openapi, fastapi_app_stub
):
    custom_api_function = create_custom_openapi_function(fastapi_app_stub)
    assert callable(custom_api_function)


def test_create_custom_openapi_function_return_calls_get_openapi_as_expected(
    patched_get_openapi, fastapi_app_stub
):
    title, version, description = "fooTitle", "fooVersion", "fooDescription"
    route1 = BaseRoute()
    route2 = BaseRoute()
    routes = [route1, route2]
    fastapi_app_stub.title = title
    fastapi_app_stub.version = version
    fastapi_app_stub.description = description
    fastapi_app_stub.routes = routes
    custom_api_function = create_custom_openapi_function(fastapi_app_stub)
    schema = custom_api_function()
    patched_get_openapi.assert_called_once_with(
        title=title, version=version, description=description, routes=routes
    )
    assert schema == EXPECTED


def test_create_custom_openapi_function_return_returns_schema_if_already_generated(
    patched_get_openapi, fastapi_app_stub
):
    fastapi_app_stub.openapi_schema = EXPECTED
    custom_api_function = create_custom_openapi_function(fastapi_app_stub)
    schema = custom_api_function()
    patched_get_openapi.assert_not_called()
    assert schema == EXPECTED

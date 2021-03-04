from typing import Callable

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def remove_422_responses(openapi_schema: dict):
    for path_value in openapi_schema.get("paths", {}).values():
        for method_value in path_value.values():
            responses = method_value.get("responses", {})
            responses.pop("422", None)


def remove_validation_error_schema(openapi_schema: dict):
    schemas = openapi_schema.get("components", {}).get("schemas")
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)


def create_custom_openapi_function(app: FastAPI) -> Callable:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        remove_422_responses(openapi_schema)
        remove_validation_error_schema(openapi_schema)
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi

from src.models.json_api.error import JSONApiError
from src.models.json_api.validation_error import InputValidationError


def create_bad_request_error(error: dict) -> JSONApiError:
    return JSONApiError[InputValidationError](
        status="400",
        code="BadRequest",
        title="Bad Request",
        detail=InputValidationError(
            location=error.get("loc", []),
            message=error.get("msg", ""),
            type=error.get("type", ""),
        ),
    )


def create_bad_request_error_with_detail(detail: str) -> JSONApiError:
    return JSONApiError[str](
        status="400", code="BadRequest", title="Bad Request", detail=detail
    )


def create_internal_server_error(detail: str) -> JSONApiError:
    return JSONApiError[str](
        status="500",
        code="InternalServerError",
        title="Internal Server Error",
        detail=detail,
    )


def create_notfound_server_error(detail: str) -> JSONApiError:
    return JSONApiError[str](
        status="404", code="NotFound", title="Not Found", detail=detail
    )


def create_forbidden_server_error(detail: str) -> JSONApiError:
    return JSONApiError[str](
        status="403", code="ForbiddenError", title="Forbidden Error", detail=detail
    )


def create_notallowed_server_error(detail: str) -> JSONApiError:
    return JSONApiError[str](
        status="405", code="MethodNotAllowed", title="Method Not Allowed", detail=detail
    )

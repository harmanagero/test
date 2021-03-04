from unittest.mock import call
from unittest.mock import create_autospec
from unittest.mock import MagicMock
from unittest.mock import NonCallableMagicMock
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from pytest import fixture
from pytest import mark
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from src.models.exceptions.badrequest_exception import BadRequestException
from src.models.exceptions.custom_exception import CustomException
from src.models.exceptions.forbidden_exception import ForbiddenException
from src.models.exceptions.notfound_exception import NotFoundException
from src.utilities.errorhandlers.exception_handlers import badrequest_exception_handler
from src.utilities.errorhandlers.exception_handlers import base_exception_handler
from src.utilities.errorhandlers.exception_handlers import forbidden_exception_handler
from src.utilities.errorhandlers.exception_handlers import http_exception_handler
from src.utilities.errorhandlers.exception_handlers import notfound_exception_handler
from src.utilities.errorhandlers.exception_handlers import register_exception_handlers
from src.utilities.errorhandlers.exception_handlers import validation_exception_handler
from src.utilities.errorhandlers.exception_handlers import valueerror_exception_handler

BAD_REQUEST_CODE = "BadRequest"
BAD_REQUEST_TITLE = "Bad Request"
BAD_REQUEST_STATUS = "400"
LOCATION = "loc"
MESSAGE = "msg"
TYPE = "type"


@fixture
def mock_json_response():
    with patch(
        "src.utilities.errorhandlers.exception_handlers.JSONResponse", autospec=True
    ) as mocked_response:
        yield mocked_response


@mark.asyncio
async def test_validation_exception_handler_returns_response_as_expected(
    mock_json_response
):
    error_stub = NonCallableMagicMock()
    error_stub.errors = MagicMock()
    error_stub.errors.return_value = [
        {"loc": [f"{LOCATION}1"], "msg": f"{MESSAGE}1", "type": f"{TYPE}1"},
        {"loc": [f"{LOCATION}2"], "msg": f"{MESSAGE}2", "type": f"{TYPE}2"},
    ]
    response = await validation_exception_handler(MagicMock(), error_stub)
    mock_json_response.assert_called_once_with(
        status_code=400,
        content={
            "errors": [
                {
                    "status": BAD_REQUEST_STATUS,
                    "code": BAD_REQUEST_CODE,
                    "title": BAD_REQUEST_TITLE,
                    "detail": {
                        "location": [f"{LOCATION}1"],
                        "message": f"{MESSAGE}1",
                        "type": f"{TYPE}1",
                    },
                },
                {
                    "status": BAD_REQUEST_STATUS,
                    "code": BAD_REQUEST_CODE,
                    "title": BAD_REQUEST_TITLE,
                    "detail": {
                        "location": [f"{LOCATION}2"],
                        "message": f"{MESSAGE}2",
                        "type": f"{TYPE}2",
                    },
                },
            ]
        },
    )
    assert isinstance(response, JSONResponse)


@mark.asyncio
async def test_http_exception_handler_returns_as_expected(mock_json_response):
    detail = "fooDetail"
    exception_stub = NonCallableMagicMock()
    exception_stub.detail = detail
    exception_stub.status_code = 500
    response = await http_exception_handler(NonCallableMagicMock(), exception_stub)
    mock_json_response.assert_called_once_with(
        status_code=500,
        content={
            "errors": [
                {
                    "status": "500",
                    "code": "InternalServerError",
                    "title": "Internal Server Error",
                    "detail": detail,
                }
            ]
        },
    )
    assert isinstance(response, JSONResponse)


@mark.asyncio
async def test_http_exception_handler_resource_not_found_returns_404(
    mock_json_response
):
    exception_stub = NonCallableMagicMock()
    exception_stub.detail = "not found"
    exception_stub.status_code = 404
    response = await http_exception_handler(NonCallableMagicMock(), exception_stub)
    mock_json_response.assert_called_once_with(
        status_code=404,
        content={
            "errors": [
                {
                    "status": "404",
                    "code": "NotFound",
                    "title": "Not Found",
                    "detail": "Missing Resource URI",
                }
            ]
        },
    )
    assert isinstance(response, JSONResponse)


@mark.asyncio
async def test_http_exception_handler_method_not_allowed_returns_405(
    mock_json_response
):
    exception_stub = NonCallableMagicMock()
    exception_stub.detail = "Method Not Allowed"
    exception_stub.status_code = 405
    response = await http_exception_handler(NonCallableMagicMock(), exception_stub)
    mock_json_response.assert_called_once_with(
        status_code=405,
        content={
            "errors": [
                {
                    "status": "405",
                    "code": "MethodNotAllowed",
                    "title": "Method Not Allowed",
                    "detail": "Method Not Allowed",
                }
            ]
        },
    )
    assert isinstance(response, JSONResponse)


@mark.asyncio
async def test_forbidden_exception_handler_returns_as_expected(mock_json_response):
    detail = "Detail"
    exception_stub = NonCallableMagicMock()
    exception_stub.detail = detail
    exception_stub.status_code = 403
    response = await forbidden_exception_handler(NonCallableMagicMock(), exception_stub)
    mock_json_response.assert_called_once_with(
        status_code=403,
        content={
            "errors": [
                {
                    "status": "403",
                    "code": "ForbiddenError",
                    "title": "Forbidden Error",
                    "detail": detail,
                }
            ]
        },
    )
    assert isinstance(response, JSONResponse)


@mark.asyncio
async def test_notfound_exception_handler_returns_as_expected(mock_json_response):
    detail = "Detail"
    exception_stub = NonCallableMagicMock()
    exception_stub.detail = detail
    exception_stub.status_code = 404
    response = await notfound_exception_handler(NonCallableMagicMock(), exception_stub)
    mock_json_response.assert_called_once_with(
        status_code=404,
        content={
            "errors": [
                {
                    "status": "404",
                    "code": "NotFound",
                    "title": "Not Found",
                    "detail": detail,
                }
            ]
        },
    )
    assert isinstance(response, JSONResponse)


def test_register_exception_handlers_registers_as_expected():
    mock_fastapi = create_autospec(FastAPI)
    register_exception_handlers(mock_fastapi)
    mock_fastapi.exception_handler.assert_has_calls(
        [
            call(RequestValidationError),
            call()(validation_exception_handler),
            call(ValueError),
            call()(valueerror_exception_handler),
            call(StarletteHTTPException),
            call()(http_exception_handler),
            call(HTTPException),
            call()(http_exception_handler),
            call(BadRequestException),
            call()(badrequest_exception_handler),
            call(NotFoundException),
            call()(notfound_exception_handler),
            call(CustomException),
            call()(base_exception_handler),
            call(ForbiddenException),
            call()(forbidden_exception_handler),
        ]
    )

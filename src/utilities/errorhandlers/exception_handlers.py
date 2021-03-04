from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_405_METHOD_NOT_ALLOWED

from src.models.exceptions.badrequest_exception import BadRequestException
from src.models.exceptions.custom_exception import CustomException
from src.models.exceptions.forbidden_exception import ForbiddenException
from src.models.exceptions.notfound_exception import NotFoundException
from src.models.json_api.error_response import JSONApiErrorResponse
from src.utilities.errorhandlers.errors import create_bad_request_error
from src.utilities.errorhandlers.errors import create_bad_request_error_with_detail
from src.utilities.errorhandlers.errors import create_forbidden_server_error
from src.utilities.errorhandlers.errors import create_internal_server_error
from src.utilities.errorhandlers.errors import create_notallowed_server_error
from src.utilities.errorhandlers.errors import create_notfound_server_error


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            JSONApiErrorResponse(
                errors=[create_bad_request_error(error) for error in exc.errors()]
            )
        ),
    )


async def valueerror_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            JSONApiErrorResponse(
                errors=
                [create_bad_request_error(error) for error in exc.errors()]
                if exc.args.__len__()>1
                else
                [create_bad_request_error_with_detail(exc.args[0])]
                )
        ),
    )


async def base_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            JSONApiErrorResponse(
                errors=[create_internal_server_error(error) for error in exc.errors()]
            )
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == HTTP_404_NOT_FOUND:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                JSONApiErrorResponse(
                    errors=[create_notfound_server_error("Missing Resource URI")]
                )
            ),
        )
    elif exc.status_code == HTTP_405_METHOD_NOT_ALLOWED:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                JSONApiErrorResponse(
                    errors=[create_notallowed_server_error("Method Not Allowed")]
                )
            ),
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            JSONApiErrorResponse(errors=[create_internal_server_error(exc.detail)])
        ),
    )


async def badrequest_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            JSONApiErrorResponse(
                errors=[create_bad_request_error_with_detail(exc.detail)]
            )
        ),
    )


async def notfound_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=jsonable_encoder(
            JSONApiErrorResponse(errors=[create_notfound_server_error(exc.detail)])
        ),
    )


async def forbidden_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=jsonable_encoder(
            JSONApiErrorResponse(errors=[create_forbidden_server_error(exc.detail)])
        ),
    )


def register_exception_handlers(app: FastAPI):
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(ValueError)(valueerror_exception_handler)
    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(BadRequestException)(badrequest_exception_handler)
    app.exception_handler(NotFoundException)(notfound_exception_handler)
    app.exception_handler(CustomException)(base_exception_handler)
    app.exception_handler(ForbiddenException)(forbidden_exception_handler)

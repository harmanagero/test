from pydantic import errors
from starlette import status
from starlette.exceptions import HTTPException


class BadRequestException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detail
        )

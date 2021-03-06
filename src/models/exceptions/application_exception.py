from starlette import status
from starlette.exceptions import HTTPException


class ApplicationException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )

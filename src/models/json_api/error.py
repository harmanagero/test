from typing import Generic
from typing import Optional
from typing import TypeVar

from pydantic.generics import GenericModel

from .validation_error import InputValidationError

ErrorT = TypeVar("ErrorT")


class JSONApiError(GenericModel, Generic[ErrorT]):
    status: Optional[str]
    code: str
    title: str
    detail: Optional[ErrorT]


class JSONApiValidationError(JSONApiError[InputValidationError]):
    pass


class JSONApiStandardError(JSONApiError[str]):
    pass

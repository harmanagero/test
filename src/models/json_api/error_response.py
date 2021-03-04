from typing import Generic
from typing import List
from typing import TypeVar

from pydantic.generics import GenericModel

ErrorT = TypeVar("ErrorT")


class JSONApiErrorResponse(GenericModel, Generic[ErrorT]):
    """
    JSON API compliant wrapper around the error type indicated in []
    """

    errors: List[ErrorT]

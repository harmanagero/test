from typing import Generic
from typing import TypeVar

from pydantic.generics import GenericModel

DataT = TypeVar("DataT")


class JSONApiSuccessResponse(GenericModel, Generic[DataT]):
    """
    JSON API compliant wrapper around the response type indicated in [].
    """

    data: DataT

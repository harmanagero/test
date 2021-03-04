from typing import List

from pydantic import BaseModel
from pydantic import Field


class InputValidationError(BaseModel):
    """
    Indicates an Input Validation Error has occurred
    """

    location: List[str] = Field(
        None,
        description="Array of strings indicating the element with the validation error",
    )
    message: str = Field(None, description="Message indicating the validation error")
    type: str = Field(None, description="Type of validation error")

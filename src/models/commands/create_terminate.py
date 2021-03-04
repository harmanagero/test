from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from src.models.enums.programcode_type import ProgramCode


class CreateTerminateCommand(BaseModel):
    referenceid: str = Field(description="Request identifier.")
    reasoncode: Optional[str] = Field(description="ReasonCode")
    programcode: ProgramCode = Field(description="Program Code Type")

    @validator("referenceid")
    def referenceid_must_not_be_empty(cls, v):
        if v == "" or v == "None":
            raise ValueError("ReferenceId cannot be null or empty")
        return v

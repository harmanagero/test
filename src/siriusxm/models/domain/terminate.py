from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.programcode_type import ProgramCode


class Terminate(BaseModel):
    referenceid: str = Field(description="Request identifier for Terminate.")
    reasoncode: Optional[str] = Field(description="Reason code for terminate")
    programcode: ProgramCode = Field(description="Accepted Program Codes")
    response_referenceid: Optional[str] = Field(
        description="Returned Request identifier for Terminate."
    )
    status: InternalStatusType = Field(
        InternalStatusType.UNKNOWN, description="Current status of terminate"
    )
    responsemessage: Optional[str] = Field(description="Response message")

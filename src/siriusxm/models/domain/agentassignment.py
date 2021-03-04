from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.programcode_type import ProgramCode


class AgentAssignment(BaseModel):
    referenceid: str = Field(description="Reference identifier for Agent assignment.")
    isassigned: bool = Field(False, description="Is Agent Assignment")
    programcode: ProgramCode = Field(description="Accepted Program Codes")

    response_referenceid: Optional[str] = Field(
        description="Response Reference identifier returned for Agent assignment."
    )
    responsestatus: InternalStatusType = Field(
        InternalStatusType.UNKNOWN,
        description="Response status returned for Agent assignment.",
    )
    responsemessage: Optional[str] = Field(
        description="Response message returned for Agent assignment."
    )

from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from src.models.domain.enums.internal_status_type import InternalStatusType


class Terminate(BaseModel):
    eventid: str = Field(
        description="eventid is the unique identifier created by TSP, and shared during call connection"
    )
    status: InternalStatusType = Field(
        InternalStatusType.UNKNOWN, description="Current status of terminate"
    )
    responsemessage: Optional[str] = Field(description="Response message")

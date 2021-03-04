from typing import Optional

from pydantic import BaseModel, Field
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.programcode_type import ProgramCode


class VehicleInfo(BaseModel):
    msisdn: Optional[str] = Field(
        None, description="Requested msisdn to retrieve the vehicle info"
    )
    programcode: Optional[ProgramCode] = Field(description="Accepted Program Codes")
    status: InternalStatusType = Field(
        InternalStatusType.UNKNOWN,
        description="Current status as returned from external service",
    )
    responsemessage: Optional[str] = Field(description="Response message")
    JSONData: Optional[dict] = Field(description="Input json payload")

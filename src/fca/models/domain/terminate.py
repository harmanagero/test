from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.callstatus_type import CallStatus


class Terminate(BaseModel):
    msisdn: str = Field(
        description="msisdn is associated with call that is received by call center. It stands for Mobile Station International Subscriber Directory Number and is required for callback incase call gets disconnected"
    )
    callstatus: Optional[CallStatus] = Field(description="callstatus like TERMINATED")
    status: InternalStatusType = Field(
        InternalStatusType.UNKNOWN, description="Current status of terminate"
    )
    responsemessage: Optional[str] = Field(description="Response message")

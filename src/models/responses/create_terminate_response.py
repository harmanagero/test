from typing import Optional

from pydantic import BaseModel, Field
from src.models.enums.status_type import Status


class CreateTerminateResponse(BaseModel):
    reference_id: Optional[str] = Field(None, description="Passed request ID to terminate")
    status: Status = Field(Status.UNKNOWN, description="Current status of terminate")
    msisdn: Optional[str] = Field(None, description="Requested msisdn to terminate the call")

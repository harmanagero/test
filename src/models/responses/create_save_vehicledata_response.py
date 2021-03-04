from typing import Optional

from pydantic import BaseModel, Field
from src.models.enums.status_type import Status


class CreateSaveVehicleDataResponse(BaseModel):
    msisdn: Optional[str] = Field(None, description="Requested msisdn to save the vehicle data")
    status: Status = Field(Status.UNKNOWN, description="Current status of save vehicle data")
    responsemessage: Optional[str] = Field(description="Response message")
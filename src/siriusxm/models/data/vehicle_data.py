from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from src.models.domain.enums.internal_status_type import InternalStatusType


class VehicleHexData(BaseModel):
    """
    Vehicle Hex Data Response
    """

    VarName: str = Field("User-to-User", description="Variable Name")
    Value: str = Field("Value")


class VehicleData(BaseModel):
    referenceid: Optional[str]
    ani: Optional[str]
    event_datetime: Optional[str]
    timestamp: Optional[datetime]
    programcode: Optional[str]
    geolocation: Optional[str]
    vin: Optional[str]
    longitude: Optional[str]
    latitude: Optional[str]
    language: Optional[str]
    calldate: Optional[str]
    calltime: Optional[str]
    hexvehicledata: Optional[VehicleHexData]
    status: InternalStatusType = Field(
        InternalStatusType.UNKNOWN,
        description="Current status as returned from external service",
    )
    responsemessage: Optional[str] = Field(description="Response message")

    @validator("latitude", always=True, pre=True)
    def set_latitude(cls, v, values):
        return get_value(values["geolocation"], 0) if values["geolocation"] else 0

    @validator("longitude", always=True, pre=True)
    def set_longitude(cls, v, values):
        return get_value(values["geolocation"], 1) if values["geolocation"] else 0


def get_value(geolocation, position):
    parsedstr = geolocation.split("~")
    val = parsedstr[position]
    return val

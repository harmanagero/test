from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from src.models.enums.status_type import Status
from src.models.responses.create_vehiclehex_response import CreateVehicleHexData


class CreateVehicleDataResponse(BaseModel):
    """
    Vehicle Data Response.
    """

    referenceid: Optional[str] = Field(
        None, description="Reference Identifier for the vehicle"
    )
    status: Status = Field(
        Status.UNKNOWN, description="Current status of vehicle data save."
    )
    responsemessage: Optional[str] = Field(description="Response message")
    programcode: str = Field(
        description="program code e.g.- nissan, infiniti, vwcarnet"
    )
    latitude: Optional[str] = Field("Latitude")
    longitude: Optional[str] = Field("Longitude")
    vin: Optional[str] = Field("Vin Number")
    language: Optional[str] = Field("language")
    hexvehicledata: List[CreateVehicleHexData] = Field(
        "Hex decimal string value of vehicle data"
    )

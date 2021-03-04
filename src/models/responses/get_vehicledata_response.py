from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.odometerscale_type import OdometerScaleType
from src.models.enums.status_type import Status


class Header(BaseModel):
    countrycode: Optional[str] = Field(description="US/CA")
    language: Optional[str] = Field(description="Language format like en-US")
    programcode: Optional[str] = Field(description="Program Code Type")
    version: Optional[CtsVersion] = Field(description="Program Version passed in input")
    referenceid: Optional[str] = Field(description="Reference identifier")
    eventid: Optional[str] = Field(description="Event identifier")
    msisdn: Optional[str] = Field(description="msisdn")
    calltype: Optional[str] = Field(description="CallType - Direct or Transfer")
    eventtype: Optional[str] = Field(description="Eventtype - SOS")
    calldate: Optional[str] = Field(description="Date on which call is placed")
    calltime: Optional[str] = Field(description="Time at which call is placed")
    timestamp: Optional[datetime] = Field(
        description="EventDateTime - datetime of save event"
    )
    odometer: Optional[int] = Field(description="Km or miles per odometer scale")
    odometerscale: Optional[OdometerScaleType] = Field(
        description="0 = MILES, 1 = KILOMETERS"
    )


class Location(BaseModel):
    latitude: Optional[float] = Field(
        description="Two digits followed by decimal value. Ex: 12.1234"
    )
    longitude: Optional[float] = Field(
        description="Two digits followed by decimal value. Ex: 12.1234"
    )
    headingdirection: Optional[str] = Field(
        description="one of these values EAST, WEST, NORTH, SOUTH, NORTH EAST, SOUTH EAST, SOUTH WEST, NORT WEST"
    )


class Brand(BaseModel):
    brandname: Optional[str] = Field(
        description="Vehicle brand name. Ex: vw, nissan etc"
    )
    modelname: Optional[str] = Field(
        description="Vehicle model name. Ex: Jetta, Passat..etc"
    )
    modelyear: Optional[str] = Field(
        description="Vehicle model year: 2018, 2019,2020..etc"
    )
    modelcode: Optional[str] = Field(description="VW model code. Ex:BX52N6")
    modeldesc: Optional[str] = Field(
        description="Description of the car model. Ex: Golf_Volkswagen_2008"
    )


class Vehicle(BaseModel):
    vin: Optional[str] = Field(description="Vehicle Identification Number")
    # brand
    brand: Optional[Brand] = Field(description="Brand of the vehicle")
    mileage: Optional[int] = Field(description="Km or miles value")
    mileageunit: Optional[OdometerScaleType] = Field(
        description="mi = MILES, km = KILOMETERS"
    )


class GetVehicleDataResponse(BaseModel):
    # header
    header: Optional[Header] = Field(description="Header object")
    # location
    location: Optional[Location] = Field(description="location details of vehicle")
    # vehicle
    vehicle: Optional[Vehicle] = Field(description="An object with vehicle details")

    status: Status = Field(
        Status.UNKNOWN, description="Current Http Status Code of vehicle data get."
    )
    responsemessage: Optional[str] = Field(description="Response message")

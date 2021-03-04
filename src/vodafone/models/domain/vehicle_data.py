from typing import Optional

from pydantic import BaseModel


class Registration(BaseModel):
    number: Optional[str]
    stateCode: Optional[str]
    countryCode: Optional[str]


class Mileage(BaseModel):
    value: Optional[str]
    unit: Optional[str]


class Range(BaseModel):
    value: Optional[str]
    unit: Optional[str]


class TyrePressureDelta(BaseModel):
    unit: Optional[str]
    frontLeft: Optional[str]
    frontRight: Optional[str]
    rearLeft: Optional[str]
    rearRight: Optional[str]


class UserData(BaseModel):
    phoneContact: Optional[str]


class GpsData(BaseModel):
    latitude: Optional[str]
    longitude: Optional[str]


class VehicleData(BaseModel):
    vin: Optional[str]
    registration: Optional[Registration]
    crankInhibition: Optional[str]
    ignitionKey: Optional[str]
    mileage: Optional[Mileage]
    fuelLevelPercentage: Optional[str]
    evBatteryPercentage: Optional[str]
    range: Optional[Range]
    tyrePressureDelta: Optional[TyrePressureDelta]


class VehicleDataRequest(BaseModel):
    countryCode: Optional[str]
    timestamp: Optional[str]
    gpsData: Optional[GpsData]
    vehicleData: Optional[VehicleData]
    userData: Optional[UserData]
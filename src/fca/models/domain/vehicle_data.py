from typing import Optional, Union
from decimal import Decimal
from pydantic import BaseModel


class Device(BaseModel):
    deviceType: Optional[str]
    deviceOS: Optional[str]
    headUnitType: Optional[str]
    manufacturerName: Optional[str]
    region: Optional[str]
    screenSize: Optional[str]
    tbmSerialNum: Optional[str]
    tbmPartNum: Optional[str]
    tbmHardwareVersion: Optional[str]
    tbmSoftwareVersion: Optional[str]
    simIccid: Optional[str]
    simImsi: Optional[str]
    simMsisdn: Optional[str]
    nadImei: Optional[str]
    nadHardwareVersion: Optional[str]
    nadSoftwareVersion: Optional[str]
    nadSerialNum: Optional[str]
    nadPartNum: Optional[str]
    wifiMac: Optional[str]
    huSerialNum: Optional[str]
    huPartNum: Optional[str]
    huHardwareVersion: Optional[str]
    huSoftwareVersion: Optional[str]
    isHUNavigationPresent: Optional[bool] = False


class TirePressure(BaseModel):
    flTirePressure: Optional[float]
    frTirePressure: Optional[float]
    rlTirePressure: Optional[float]
    rrTirePressure: Optional[float]
    rl2TirePressure: Optional[float]
    rr2TirePressure: Optional[float]
    flTireSts: Optional[str]
    frTireSts: Optional[str]
    rlTireSts: Optional[str]
    rrTireSts: Optional[str]


class ErrorTellTale(BaseModel):
    isOilPressure: Optional[bool]


class VehicleLocation(BaseModel):
    positionLatitude: Optional[float]
    positionLongitude: Optional[float]
    estimatedPositionError: Optional[int]
    positionAltitude: Optional[float]
    gpsFixTypeEnum: Optional[str]
    isGPSFixNotAvailable: Optional[bool]
    estimatedAltitudeError: Optional[int]
    positionDirection: Optional[int]


class VehicleInfo(BaseModel):
    vehicleLocation: VehicleLocation
    vehicleSpeed: Optional[float]
    odometer: Optional[float]
    engineStatusEnum: Optional[str]
    language: Optional[str]
    country: Optional[str]
    vehicleType: Optional[str]
    vin: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    year: Optional[str]


class VehicleDataUpload(BaseModel):
    callCenterNumber: Optional[str]
    CallReasonEnum: Optional[str]
    callTriggerEnum: Optional[str]
    calltype: Optional[str]
    daysRemainingForNextService: Optional[int]
    device: Optional[Device]
    distanceRemainingForNextService: Optional[int]
    errorTellTale: Union[str, ErrorTellTale, None]
    fuelRemaining: Optional[float]
    stateofCharge: Optional[float]
    tirePressure: Union[str, TirePressure, None]
    vehicleInfo: Optional[VehicleInfo]


class CustomExtension(BaseModel):
    vehicleDataUpload: Optional[VehicleDataUpload]
    callCenterNumber: Optional[str]
    CallReasonEnum: Optional[str]
    callTriggerEnum: Optional[str]
    calltype: Optional[str]
    daysRemainingForNextService: Optional[int]
    device: Optional[Device]
    distanceRemainingForNextService: Optional[int]
    errorTellTale: Union[str, ErrorTellTale, None]
    fuelRemaining: Optional[float]
    stateofCharge: Optional[float]
    tirePressure: Union[str, TirePressure, None]
    vehicleInfo: Optional[VehicleInfo]
    calltype : Optional[str]


class Data(BaseModel):
    callCenterNumber: Optional[str]
    bcallType: str
    callTrigger: str
    callReason: str
    customExtension: CustomExtension
    language: Optional[str]
    latitude: float = 0.0
    longitude: float = 0.0
    fuelRemaining: float = 0.0
    engineStatus: str


class VehicleData(BaseModel):
    Data: Data
    EventID: Optional[str]
    Timestamp: Optional[int]
    Version: Optional[str]
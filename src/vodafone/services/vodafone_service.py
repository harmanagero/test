import logging
from typing import Type

from pydantic.types import Json
from src.config.vodafone_config import VodafoneConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.client_service import ClientService
from src.services.dynamodb_tables import (
    ConnectedVehicleSupplementTable,
    ConnectedVehicleTable,
)
from src.utilities.extensions.datetime_extension import (
    convert_epoch_to_utc_timestamp,
    get_utc_epoch,
)
from src.utilities.extensions.json_extension import checkjsonnode
from src.utilities.metric_scale import MileageUnit
from src.vodafone.models.data.vehicle_data import VehicleData
from src.vodafone.models.data.vehicle_info import VehicleInfo
from src.vodafone.models.domain.vehicle_data import VehicleDataRequest

logger = logging.getLogger(__name__)


class VodafoneService(ClientService):
    def __init__(
        self,
        config: VodafoneConfig,
        table: Type[ConnectedVehicleTable],
        supplementtable: Type[ConnectedVehicleSupplementTable],
    ):
        self._logger = logger
        self._config = config
        self._Table = table
        self._SupplementTable = supplementtable

    def get_vehicledata(self, msisdn: str, programcode: ProgramCode):
        try:
            msisdn = reformat_msisdn(msisdn)

            self._logger.info(
                "GetVehicleData: Vehicle data for msisdn: {} programcode: {}".format(
                    msisdn, programcode
                ),
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "GetVehicleData",
                },
            )
            for dataitem in self._Table.query(
                programcode + "-" + msisdn,
                self._Table.msisdn == msisdn,
                scan_index_forward=False,
                limit=1,
            ):
                self._logger.info(
                    "GetVehicleData: Successfully retrieved response from database for msisdn:{} programcode:{}".format(
                        msisdn, programcode
                    ),
                    extra={
                        "msisdn": msisdn,
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": "GetVehicleData",
                    },
                )

                return VehicleData(
                    status=InternalStatusType.SUCCESS,
                    responsemessage="Successfully retrieved",
                    msisdn=msisdn,
                    programcode=programcode,
                    event_datetime=dataitem.event_datetime,
                    calldate=dataitem.timestamp.strftime("%Y-%m-%d"),
                    calltime=dataitem.timestamp.strftime("%H:%M"),
                    timestamp=dataitem.timestamp,
                    countrycode=dataitem.countrycode,
                    latitude=dataitem.latitude,
                    longitude=dataitem.longitude,
                    vin=dataitem.vin,
                    brand=dataitem.brand,
                    mileage=dataitem.mileage,
                    mileageunit=MileageUnit(dataitem.mileageunit),
                )

            return VehicleData(
                status=InternalStatusType.NOTFOUND, responsemessage="No data found"
            )

        except Exception as e:
            self._logger.info(
                "GetVehicleData: Error retrieving data from DynamoDB for msisdn:{} e:{}".format(
                    msisdn, e
                ),
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "GetVehicleData",
                },
            )

            return VehicleData(
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=e.args[0] if e.args.__len__() > 0 else None,
            )

    def save_vehicledata(self, msisdn, programcode, savevehicledata):
        if (
            savevehicledata is None
            or checkjsonnode("gpsData", savevehicledata) == False
            or checkjsonnode("userData", savevehicledata) == False
            or checkjsonnode("vehicleData", savevehicledata) == False
        ):
            self._logger.error(
                "SaveVehicleData: Json payload: {} is invalid for msisdn: {}".format(
                    savevehicledata, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "SaveVehicleData",
                },
            )

            return VehicleData(
                msisdn=msisdn,
                status=InternalStatusType.BADREQUEST,
                responsemessage="SaveVehicleData: Json payload is invalid for msisdn: {}".format(
                    msisdn
                ),
            )

        try:
            self._logger.info(
                "SaveVehicleData: Vehicle data for msisdn: {} data: {}".format(
                    msisdn, savevehicledata
                ),
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "SaveVehicleData",
                },
            )

            vehicledata = self.populate_vehicledata(
                msisdn, programcode, savevehicledata
            )
            vehicle_table = map_primarytable(
                msisdn, programcode, vehicledata, self._Table, savevehicledata
            )
            vehicle_table.save()
            self._logger.info(
                "SaveVehicleData: Successfully saved Vehicle data onto main table {} for msisdn: {}".format(
                    vehicledata, msisdn
                ),
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "SaveVehicleData",
                },
            )

            save_supplementdata(self, msisdn, programcode, vehicledata)

            return VehicleData(
                msisdn=msisdn,
                status=InternalStatusType.SUCCESS,
                responsemessage="Successfully saved the vehicledata for msisdn: {}".format(
                    msisdn
                ),
            )
        except Exception as e:
            self._logger.error(
                "SaveVehicleData: Error occured while saving vehicledata onto primary table: {} for msisdn: {}".format(
                    e, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "payload": savevehicledata,
                    "action": "SaveVehicleData",
                },
            )
            return VehicleData(
                msisdn=msisdn,
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage="Unable to save the vehicledata for msisdn: {}".format(
                    msisdn
                ),
            )

    def get_vehicleinfo(self, msisdn: str):
        programcode = ProgramCode.PORSCHE
        try:
            msisdn = reformat_msisdn(msisdn)

            self._logger.info(
                "GetVehicleInfo: Received request to retrive data for msisdn: {} programcode: {}".format(
                    msisdn, programcode
                ),
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "GetVehicleInfo",
                },
            )
            for dataitem in self._Table.query(
                programcode + "-" + msisdn,
                self._Table.msisdn == msisdn,
                scan_index_forward=False,
                limit=1,
            ):
                self._logger.info(
                    "GetVehicleInfo: Successfully retrieved response from database for msisdn:{} programcode:{}".format(
                        msisdn, programcode
                    ),
                    extra={
                        "msisdn": msisdn,
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": "GetVehicleInfo",
                    },
                )

                return VehicleInfo(
                    status=InternalStatusType.SUCCESS,
                    responsemessage="Successfully retrieved",
                    msisdn=msisdn,
                    programcode=programcode,
                    JSONData=dataitem.JSONData,
                )

            self._logger.error(
                "GetVehicleInfo: No data found for msisdn: {} programcode: {}".format(
                    msisdn, programcode
                ),
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "GetVehicleInfo",
                },
            )

            return VehicleInfo(
                status=InternalStatusType.NOTFOUND, responsemessage="No data found"
            )

        except Exception as e:
            self._logger.info(
                "GetVehicleInfo: Error retrieving data from DynamoDB for msisdn:{} e:{}".format(
                    msisdn, e
                ),
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "GetVehicleInfo",
                },
            )

            return VehicleInfo(
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=e.args[0] if e.args.__len__() > 0 else None,
            )

    def populate_vehicledata(self, msisdn, programcode, data):
        try:
            vehicle_data = VehicleDataRequest(**data)
            return vehicle_data
        except Exception as e:
            self._logger.error(
                "SaveVehicleData: Data Population failed: {} for msisdn: {}".format(
                    e, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "payload": data,
                    "action": "SaveVehicleData",
                },
            )

    def assign_agent(self, any):
        raise NotImplementedError

    def terminate(self, any):
        raise NotImplementedError

    def health(self, programcode: ProgramCode, ctsversion: CtsVersion):
        raise NotImplementedError


def reformat_msisdn(msisdn):
    if len(msisdn) == 10:
        msisdn = "1" + msisdn

    return msisdn


def map_primarytable(
    msisdn: str,
    programcode: ProgramCode,
    request: VehicleDataRequest,
    tblprimary: ConnectedVehicleTable,
    savevehicledata: Json,
):
    return tblprimary(
        msisdn=msisdn,
        programcode=programcode,
        request_key="{}-{}".format(programcode, msisdn),
        countrycode=request.countryCode,
        timestamp=convert_epoch_to_utc_timestamp(int(request.timestamp)),
        event_datetime=get_utc_epoch(),  # UTCs epoch
        latitude=float(request.gpsData.latitude),
        longitude=float(request.gpsData.longitude),
        vin=request.vehicleData.vin,
        brand=programcode.upper(),
        mileage=int(request.vehicleData.mileage.value),
        mileageunit=request.vehicleData.mileage.unit,
        JSONData=savevehicledata,
    )


def save_supplementdata(
    self,
    msisdn: str,
    programcode: ProgramCode,
    request: VehicleDataRequest,
):
    try:
        vehicle_supplementtable = map_supplementtable(
            msisdn,
            programcode,
            request,
            self._SupplementTable,
        )
        vehicle_supplementtable.save()
        self._logger.info(
            "SaveVehicleData: Successfully saved additional vehicle data onto supplement table {} for msisdn: {}".format(
                request, msisdn
            ),
            extra={
                "programcode": programcode,
                "cts-version": CtsVersion.ONE_DOT_ZERO,
                "action": "SaveVehicleData",
            },
        )
    except Exception as e:
        self._logger.error(
            "SaveVehicleData: Error occured while saving data onto supplement table: {} for msisdn: {}".format(
                e, msisdn
            ),
            exc_info=True,
            stack_info=True,
            extra={
                "programcode": programcode,
                "cts-version": CtsVersion.ONE_DOT_ZERO,
                "action": "SaveVehicleData",
            },
        )


def map_supplementtable(
    msisdn: str,
    programcode: ProgramCode,
    request: VehicleDataRequest,
    tblsupplement: ConnectedVehicleSupplementTable,
):
    return tblsupplement(
        msisdn=msisdn,
        programcode=programcode,
        request_key="{}-{}".format(programcode, msisdn),
        timestamp=convert_epoch_to_utc_timestamp(int(request.timestamp)),
        event_datetime=get_utc_epoch(),
        registrationnumber=request.vehicleData.registration.number,
        registrationstatecode=request.vehicleData.registration.stateCode,
        registrationcountrycode=request.vehicleData.registration.countryCode,
        crankinhibition=float(request.vehicleData.crankInhibition),
        ignitionkey=request.vehicleData.ignitionKey,
        evbatterypercentage=request.vehicleData.evBatteryPercentage,
        fuellevelpercentage=float(request.vehicleData.fuelLevelPercentage),
        range=int(request.vehicleData.range.value),
        rangeunit=request.vehicleData.range.unit,
        tirepressureunit=request.vehicleData.tyrePressureDelta.unit,
        tirepressurefrontleft=float(request.vehicleData.tyrePressureDelta.frontLeft),
        tirepressurefrontright=float(request.vehicleData.tyrePressureDelta.frontRight),
        tirepressurerearleft=float(request.vehicleData.tyrePressureDelta.rearLeft),
        tirepressurerearright=float(request.vehicleData.tyrePressureDelta.rearRight),
    )

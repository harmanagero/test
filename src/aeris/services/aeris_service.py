from datetime import datetime
import logging
from typing import Type

import requests
from src.aeris.models.domain.vehicle_data import VehicleData
from src.config.aeris_config import AerisConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.models.enums.status_type import Status
from src.services.client_service import ClientService
from src.services.dynamodb_tables import ConnectedVehicleTable
from src.services.dynamodb_helper import get_vehicledata_for_config_enabled_client_only
from src.utilities.extensions.datetime_extension import get_utc_epoch
from src.utilities.extensions.string_extension import isnotnull_whitespaceorempty
from src.utilities.extensions.json_extension import checkjsonnode, seterrorjson
from src.utilities.metric_scale import OdometerScale
from starlette.status import HTTP_200_OK

logger = logging.getLogger(__name__)


class AerisService(ClientService):
    def __init__(self, config: AerisConfig, table: Type[ConnectedVehicleTable]):
        self._logger = logger
        self._config = config
        self._Table = table

    def get_vehicledata(self, msisdn: str, programcode: ProgramCode):
        try:
            self._logger.info(
                "GetVehicleData: Payload received for msisdn: {} programcode: {}".format(
                    msisdn, programcode
                ),
                extra={
                    "programcode": programcode,
                    "msisdn": msisdn,
                    "action": "GetVehicleData",
                    "cts-version": CtsVersion.TWO_DOT_ZERO,
                },
            )

            if not self._config.base_url.endswith("/"):
                self._config.base_url = "{url}{suffix}".format(
                    url=self._config.base_url, suffix="/"
                )

            dataresponse = None
            # check and get data from database based of db check flag
            if self._config.dynamodb_check_enable:
                dataresponse = get_data_from_database(
                    self, msisdn, programcode, CtsVersion.TWO_DOT_ZERO
                )

            if dataresponse is not None:
                return dataresponse
            else:
                response = requests.get(
                    "{serviceurl}{msisdn}".format(
                        serviceurl=self._config.base_url, msisdn=msisdn
                    ),
                    verify=self._config.root_cert,
                )

                self._logger.info(
                    "GetVehicleData: Response from vordel for msisdn: {} is: "
                    "status_code: {}, response_text: {}, response_reason: {}".format(
                        msisdn, response.status_code, response.text, response.reason
                    ),
                    extra={
                        "programcode": programcode,
                        "msisdn": msisdn,
                        "response": str(response),
                        "action": "GetVehicleData",
                        "cts-version": CtsVersion.TWO_DOT_ZERO,
                    },
                )

                validjsonresponse = (
                    response.headers.get("content-type") is not None
                    and "json" in response.headers.get("content-type").lower()
                )
                if (
                    response.status_code == HTTP_200_OK
                    and validjsonresponse
                    and checkjsonnode("data", response.json())
                ):
                    responsejson = response.json()["data"]

                    self._logger.info(
                        "GetVehicleData: Successfully received response for msisdn:{} status:{} programcode:{} response_payload:{}".format(
                            msisdn, Status.SUCCESS, programcode, responsejson
                        ),
                        extra={
                            "programcode": programcode,
                            "msisdn": msisdn,
                            "action": "GetVehicleData",
                            "cts-version": CtsVersion.TWO_DOT_ZERO,
                        },
                    )

                    vehicledata = VehicleData(
                        status=InternalStatusType.SUCCESS,
                        responsemessage="Successfully retrieved",
                        msisdn=msisdn,
                        programcode=programcode,
                        event_datetime=get_utc_epoch(),
                        calldate=responsejson["callDate"],
                        calltime=responsejson["callTime"],
                        timestamp=datetime.strptime(
                            "{} {}".format(
                                responsejson["callDate"], responsejson["callTime"]
                            ),
                            "%Y-%m-%d %H:%M",
                        ),
                        odometer=responsejson["odometer"],
                        odometerscale=OdometerScale(responsejson["odometerScale"]),
                        activationtype=responsejson["activationType"],
                        latitude=responsejson["location"]["latitude"],
                        longitude=responsejson["location"]["longitude"],
                        headingdirection=responsejson["location"]["headingDirection"],
                        vin=responsejson["vehicle"]["vin"],
                        brand=responsejson["vehicle"]["brand"],
                        modelname=responsejson["vehicle"]["modelName"],
                        modelyear=responsejson["vehicle"]["modelYear"],
                        modelcode=responsejson["vehicle"]["modelCode"],
                        modeldesc=responsejson["vehicle"]["modelDesc"],
                        market=responsejson["vehicle"]["ocuSim"]["market"],
                    )
                    # Save the data in dynamodb for audit and return the model on success
                    self.save_vehicledata(msisdn, programcode, vehicledata)

                    return vehicledata

                errorjson = (
                    response.json()["error"]
                    if validjsonresponse and checkjsonnode("error", response.json())
                    else seterrorjson(response.reason, response.text)
                )
                errorstatus = internalstatustype_conversion(errorjson["status"])
                self._logger.error(
                    "GetVehicleData: Error occurred for msisdn:{} status:{} programcode:{} error_response_payload:{}".format(
                        msisdn,
                        errorstatus,
                        programcode,
                        errorjson
                        if validjsonresponse
                        else "ErrorResponse {}".format(response),
                    ),
                    exc_info=True,
                    stack_info=True,
                    extra={
                        "programcode": programcode,
                        "msisdn": msisdn,
                        "action": "GetVehicleData",
                        "cts-version": CtsVersion.TWO_DOT_ZERO,
                    },
                )
                return VehicleData(
                    status=errorstatus,
                    responsemessage="{code}{description}".format(
                        code=errorjson["errorCode"]
                        if checkjsonnode("errorCode", errorjson)
                        else "",
                        description=", {}".format(errorjson["errorDescription"])
                        if checkjsonnode("errorDescription", errorjson)
                        else "",
                    ),
                )
        except Exception as e:
            self._logger.error(
                "GetVehicleData: Gateway error: Aeris: Error Occured: {} for msisdn: {}".format(
                    e, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "msisdn": msisdn,
                    "action": "GetVehicleData",
                    "cts-version": CtsVersion.TWO_DOT_ZERO,
                },
            )
            return VehicleData(
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=e.args[0] if e.args.__len__() > 0 else None,
            )

    def save_vehicledata(self, msisdn, programcode, vehicledata):
        if vehicledata is not None:
            self._logger.info(
                "SaveVehicleData: Payload received for msisdn: {} data: {}".format(
                    msisdn, vehicledata
                ),
                extra={
                    "programcode": programcode,
                    "msisdn": msisdn,
                    "cts-version": CtsVersion.TWO_DOT_ZERO,
                    "action": "SaveVehicleData",
                },
            )
            if type(vehicledata) is not VehicleData:
                vehicledata = self.populate_vehicledata(
                    msisdn, programcode, vehicledata
                )
            try:
                vehicle_table = self._Table(
                    msisdn=vehicledata.msisdn,
                    programcode=vehicledata.programcode,
                    request_key=vehicledata.programcode + "-" + vehicledata.msisdn,
                    activationtype=vehicledata.activationtype,
                    event_datetime=vehicledata.event_datetime,
                    timestamp=vehicledata.timestamp,
                    vin=vehicledata.vin,
                    latitude=float(vehicledata.latitude),
                    longitude=float(vehicledata.longitude),
                    headingdirection=vehicledata.headingdirection,
                    brand=vehicledata.brand,
                    modelname=vehicledata.modelname,
                    modelyear=vehicledata.modelyear,
                    modelcode=vehicledata.modelcode,
                    modeldesc=vehicledata.modeldesc,
                    market=vehicledata.market,
                    odometer=vehicledata.odometer,
                    odometerscale=vehicledata.odometerscale,
                )

                vehicle_table.save()
                self._logger.info(
                    "SaveVehicleData: Successfully saved Vehicle data for msisdn: {} programcode: {} data: {} and the savequeryinfo: {}".format(
                        vehicledata.msisdn,
                        vehicledata.programcode,
                        vehicledata,
                        vehicle_table,
                    ),
                    extra={
                        "programcode": vehicledata.programcode,
                        "msisdn": vehicledata.msisdn,
                        "action": "SaveVehicleData",
                        "cts-version": CtsVersion.TWO_DOT_ZERO,
                    },
                )
                return VehicleData(
                    msisdn=msisdn,
                    status=InternalStatusType.SUCCESS,
                    responsemessage="Successfully saved the vehicledata for msisdn: {}".format(
                        msisdn
                    ),
                )
            except Exception as e:
                self._logger.error(
                    "SaveVehicleData: Unable to save the data onto dynamodb : {}".format(
                        e
                    ),
                    exc_info=True,
                    stack_info=True,
                    extra={
                        "programcode": programcode,
                        "msisdn": msisdn,
                        "action": "SaveVehicleData",
                        "cts-version": CtsVersion.TWO_DOT_ZERO,
                    },
                )
                return VehicleData(
                    msisdn=msisdn,
                    status=InternalStatusType.INTERNALSERVERERROR,
                    responsemessage="Unable to save the vehicledata for msisdn: {}".format(
                        msisdn
                    ),
                )

    def populate_vehicledata(self, msisdn, programcode, data):
        try:
            vehicle_data = VehicleData(**data)
            return vehicle_data
        except Exception as e:
            self._logger.error(
                "SaveVehicleData: Data Population failed: {} for msisdn: {}".format(
                    e, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": CtsVersion.TWO_DOT_ZERO,
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


def internalstatustype_conversion(responsestatus: str):
    #  responsestatus can be of any case which gets internally converted to uppercase
    responsestatus = responsestatus.upper()
    switcher = {
        "ILLEGAL_ARGUMENT_ERROR": InternalStatusType.NOTFOUND,
        "INVALID_STATE_ERROR": InternalStatusType.FORBIDDEN,
        "NOT_FOUND": InternalStatusType.NOTFOUND,
        "INTERNAL_SERVER_ERROR": InternalStatusType.INTERNALSERVERERROR,
        "BAD_REQUEST": InternalStatusType.BADREQUEST,
    }
    return switcher.get(responsestatus, InternalStatusType.INTERNALSERVERERROR)


def get_data_from_database(self, msisdn, programcode, ctsversion):
    try:
        self._logger.info(
            "GetVehicleData: Check data from database for msisdn: {} programcode: {}".format(
                msisdn, programcode
            ),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": ctsversion,
                "action": "GetVehicleData",
            },
        )
        db_response = get_vehicledata_for_config_enabled_client_only(
            self, msisdn, programcode, ctsversion
        )
        if db_response is not None:
            dataresponse = create_vehicledata_response(
                db_response,
                msisdn,
                programcode,
                InternalStatusType.SUCCESS,
                "Successfully retrieved",
            )
            self._logger.info(
                "GetVehicleData: Successfully retrieved response from database for msisdn:{} programcode:{} status:{} and received response:{}".format(
                    msisdn, programcode, Status.SUCCESS, dataresponse
                ),
                extra={
                    "msisdn": msisdn,
                    "programcode": programcode,
                    "cts-version": ctsversion,
                    "action": "GetVehicleData",
                },
            )
            return dataresponse
        self._logger.info(
            "GetVehicleData: No data found from database for msisdn:{} programcode:{}".format(
                msisdn, programcode
            ),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": ctsversion,
                "action": "GetVehicleData",
            },
        )
        return None
    except Exception as e:
        self._logger.error(
            "GetVehicleData: Check data from database : Error Occurred:{} for msisdn: {} programcode: {}".format(
                e, msisdn, programcode
            ),
            exc_info=True,
            stack_info=True,
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": ctsversion,
                "action": "GetVehicleData",
            },
        )
        return None


def create_vehicledata_response(
    response,
    msisdn,
    programcode: ProgramCode,
    responsestatus: InternalStatusType,
    responsemessage,
):
    if response is not None:
        return VehicleData(
            status=responsestatus,
            responsemessage=responsemessage,
            msisdn=msisdn,
            programcode=programcode,
            event_datetime=response.event_datetime,
            calldate=response.timestamp.strftime("%Y-%m-%d"),
            calltime=response.timestamp.strftime("%H:%M"),
            timestamp=response.timestamp,
            activationtype=response.activationtype,
            odometer=response.odometer,
            odometerscale=response.odometerscale,
            latitude=response.latitude,
            longitude=response.longitude,
            headingdirection=response.headingdirection,
            vin=response.vin,
            brand=response.brand,
            modelname=response.modelname,
            modelyear=response.modelyear,
            modelcode=response.modelcode,
            modeldesc=response.modeldesc,
            market=response.market,
        )

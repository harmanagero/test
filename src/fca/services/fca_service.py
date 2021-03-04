import logging
from time import sleep
from typing import Type

import requests
from requests.models import Response
from src.config.fca_config import FcaConfig
from src.fca.models.data.vehicle_data import VehicleData
from src.fca.models.domain.terminate import Terminate
from src.fca.models.domain.vehicle_data import CustomExtension
from src.fca.models.domain.vehicle_data import VehicleData as VehicleDataRequest
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.callstatus_type import CallStatus
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.models.enums.status_type import Status
from src.services.client_service import ClientService
from src.services.dynamodb_tables import (
    ConnectedVehicleSupplementTable,
    ConnectedVehicleTable,
)
from src.utilities.extensions.datetime_extension import (
    convert_epoch_to_utc_timestamp,
    get_utc_epoch,
)
from src.utilities.extensions.json_extension import checkjsonnode, seterrorjson
from src.utilities.extensions.string_extension import isnull_whitespaceorempty
from starlette.status import HTTP_200_OK, HTTP_202_ACCEPTED

logger = logging.getLogger(__name__)


class FcaService(ClientService):
    def __init__(
        self,
        config: FcaConfig,
        table: Type[ConnectedVehicleTable],
        supplementtable: Type[ConnectedVehicleSupplementTable],
    ):
        self._logger = logger
        self._config = config
        self._Table = table
        self._SupplementTable = supplementtable

    def get_vehicledata(self, msisdn: str, programcode: ProgramCode):
        try:
            msisdn = reformat_msisdn(msisdn, self._config.max_ani_length)

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

            dataresponse = None
            # get data from database
            db_response = get_vehicledata_response(self, msisdn, programcode)
            if db_response is not None:
                dataresponse = create_vehicledata_response(
                    db_response,
                    msisdn,
                    programcode,
                    InternalStatusType.SUCCESS,
                    "Successfully retrieved",
                )
                self._logger.info(
                    "GetVehicleData: Successfully retrieved response from database for msisdn:{} status:{} programcode:{}".format(
                        msisdn, Status.SUCCESS, programcode
                    ),
                    extra={
                        "msisdn": msisdn,
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": "GetVehicleData",
                    },
                )
                return dataresponse
            else:
                payload = {"msisdn": msisdn}
                response = None
                validjsonresponse = None
                (
                    response,
                    validjsonresponse,
                    dataresponse,
                ) = retrial_request_bcall_get_vehicledata(
                    self, msisdn, programcode, payload, "GetVehicleData"
                )
                if dataresponse is not None:
                    return dataresponse
                if (
                    response.status_code == HTTP_200_OK
                    or response.status_code == HTTP_202_ACCEPTED
                ) and validjsonresponse:
                    self._logger.error(
                        "GetVehicleData: Request BCall Data Successful, but no record found from database for msisdn:{} status:{} programcode:{}".format(
                            msisdn, Status.NOT_FOUND, programcode
                        ),
                        extra={
                            "msisdn": msisdn,
                            "programcode": programcode,
                            "cts-version": CtsVersion.ONE_DOT_ZERO,
                            "action": "GetVehicleData",
                        },
                    )
                    return VehicleData(
                        msisdn=msisdn,
                        status=InternalStatusType.NOTFOUND,
                        responsemessage="No data is available for msisdn: {}".format(
                            msisdn
                        ),
                    )

                elif validjsonresponse:
                    responsejson = response.json()[0]
                    errorjson = seterrorjson(
                        responsejson["detailedErrorCode"]
                        if checkjsonnode("detailedErrorCode", responsejson)
                        else (
                            responsejson["error"]
                            if checkjsonnode("error", responsejson)
                            else "NA"
                        ),
                        responsejson["message"]
                        if checkjsonnode("message", responsejson)
                        else "NA",
                    )
                else:
                    errorjson = seterrorjson(response.reason, response.text)

                errorstatus = internalstatus_conversion(errorjson["status"])
                self._logger.info(
                    "GetVehicleData: Error occurred in FCA BData call for msisdn:{} status:{} error_response_payload:{}".format(
                        msisdn,
                        errorstatus,
                        errorjson
                        if validjsonresponse
                        else "{}, missing json response from external fca service".format(
                            response
                        ),
                    ),
                    extra={
                        "msisdn": msisdn,
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": "GetVehicleData",
                    },
                )

                return VehicleData(
                    msisdn=msisdn,
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
                "GetVehicleData: Gateway error: FCA: Error Occured: {} for msisdn {}".format(
                    e, msisdn
                ),
                exc_info=True,
                stack_info=True,
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

    def terminate(self, msisdn: str, programcode: ProgramCode, payload):
        if (
            payload is None
            or checkjsonnode("callstatus", payload) == False
            or isnull_whitespaceorempty(payload["callstatus"])
            or payload["callstatus"] != CallStatus.TERMINATED
        ):
            self._logger.error(
                "Terminate: Missing callstatus in payload: {} for msisdn {}".format(
                    payload, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "payload": payload,
                    "action": "Terminate",
                },
            )

            return Terminate(
                msisdn=msisdn,
                status=InternalStatusType.BADREQUEST,
                responsemessage="callstatus in payload is missing or invalid",
            )
        callstatus = payload["callstatus"]
        try:
            self._logger.info(
                "Terminate: Request for msisdn: {}".format(msisdn),
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "Terminate",
                    "callstatus": callstatus,
                },
            )

            msisdn = reformat_msisdn(msisdn, self._config.max_ani_length)
            requestbody = {"msisdn": msisdn, "callStatus": callstatus}
            serviceurl = "{}{}".format(
                self._config.base_url, self._config.terminate_bcall_url
            )
            headers = {
                "content-type": "application/json",
                "APIKey": self._config.raw_api_key,
            }
            response = requests.post(
                serviceurl,
                headers=headers,
                json=requestbody,
                verify=self._config.root_cert,
            )
            validjsonresponse = (
                response.headers.get("content-type") is not None
                and "json" in response.headers.get("content-type").lower()
            )
            if (
                response.status_code == HTTP_200_OK
                or response.status_code == HTTP_202_ACCEPTED
            ) and validjsonresponse:
                responsejson = response.json()

                self._logger.info(
                    "Terminate: FCA response for msisdn:{} status:{} success_response_payload:{}".format(
                        msisdn, Status.CREATED, responsejson
                    ),
                    extra={
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": "Terminate",
                        "callstatus": callstatus,
                    },
                )

                return Terminate(
                    msisdn=msisdn,
                    status=InternalStatusType.SUCCESS,
                    responsemessage=responsejson["message"]
                    if checkjsonnode("message", responsejson)
                    else "Successfully terminated the call",
                    callstatus=callstatus,
                )
            if validjsonresponse:
                responsejson = response.json()[0]
                errorjson = seterrorjson(
                    responsejson["detailedErrorCode"]
                    if checkjsonnode("detailedErrorCode", responsejson)
                    else (
                        responsejson["error"]
                        if checkjsonnode("error", responsejson)
                        else "NA"
                    ),
                    responsejson["message"]
                    if checkjsonnode("message", responsejson)
                    else "NA",
                )
            else:
                errorjson = seterrorjson(response.reason, response.text)

            errorstatus = internalstatus_conversion(errorjson["status"])
            self._logger.error(
                "Terminate: Error occurred in FCA Terminate call for msisdn:{} status:{} error_response_payload:{}".format(
                    msisdn,
                    errorstatus,
                    errorjson
                    if validjsonresponse
                    else "{}, missing json response from external fca service".format(
                        response
                    ),
                ),
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "Terminate",
                    "callstatus": callstatus,
                },
            )

            return Terminate(
                msisdn=msisdn,
                status=errorstatus,
                responsemessage="{code}{description}".format(
                    code=errorjson["errorCode"]
                    if checkjsonnode("errorCode", errorjson)
                    else "",
                    description=", {}".format(errorjson["errorDescription"])
                    if checkjsonnode("errorDescription", errorjson)
                    else "",
                    callstatus=callstatus,
                ),
            )
        except Exception as e:
            self._logger.error(
                "Terminate: Gateway error: External FCA: Error Occured: {} for msisdn {}".format(
                    e, msisdn
                ),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "action": "Terminate",
                    "callstatus": callstatus,
                },
            )

            return Terminate(
                msisdn=msisdn,
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=e.args[0] if e.args.__len__() > 0 else None,
                callstatus=callstatus,
            )

    def save_vehicledata(self, msisdn, programcode, savevehicledata):
        if (
            savevehicledata is None
            or checkjsonnode("Data", savevehicledata) == False
            or checkjsonnode("customExtension", savevehicledata["Data"]) == False
            or savevehicledata["Data"]["customExtension"] is None
            or (
                checkjsonnode(
                    "vehicleDataUpload", savevehicledata["Data"]["customExtension"]
                )
                and savevehicledata["Data"]["customExtension"]["vehicleDataUpload"]
                is None
            )
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

            if vehicledata.Data.customExtension.vehicleInfo is None:
                custom_extension = vehicledata.Data.customExtension.vehicleDataUpload
            else:
                custom_extension = vehicledata.Data.customExtension

            vehicle_table = map_primarytable(
                msisdn, programcode, vehicledata, custom_extension, self._Table
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

            save_supplementdata(
                self, msisdn, programcode, vehicledata, custom_extension
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

    def health(self, programcode: ProgramCode, ctsversion: CtsVersion):
        raise NotImplementedError


def get_vehicledata_response(self, msisdn: str, programcode: ProgramCode):
    try:
        if msisdn:
            # Query for Items Matching a Partition/Sort Key in descending order
            for dataresponse in self._Table.query(
                programcode + "-" + msisdn,
                self._Table.msisdn == msisdn,
                scan_index_forward=False,
                limit=1,
            ):
                if dataresponse:
                    return dataresponse
                else:
                    return None
            return None
        return None
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
            countrycode=response.countrycode,
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
        )


def request_bcall_data(self, msisdn, programcode: ProgramCode, payload, action):
    try:
        serviceurl = "{}{}".format(self._config.base_url, self._config.bcall_data_url)
        headers = {
            "content-type": "application/json",
            "APIKey": self._config.raw_api_key,
        }
        response = requests.post(
            serviceurl, headers=headers, json=payload, verify=self._config.root_cert
        )
        self._logger.info(
            "GetVehicleData: FCA returned {} for the msisdn: {} .".format(
                response.json(), msisdn
            ),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": CtsVersion.ONE_DOT_ZERO,
                "action": action,
            },
        )
        return response
    except Exception as ex:
        self._logger.error(
            "GetVehicleData: Error calling fca bcall endpoint for the msisdn: {}. Exception: {}".format(
                msisdn, ex
            ),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": CtsVersion.ONE_DOT_ZERO,
                "action": action,
            },
        )
        errorresponse = Response()
        errorresponse.headers = {"content-type": "text/plain"}
        errorresponse.status_code = 500
        errormessage = "Exception calling fca bcall endpoint for msisdn: {}".format(
            msisdn
        )
        errorresponse._content = errormessage.encode("ASCII")
        errorresponse.reason = "Internal Server Error"
        return errorresponse


def retrial_request_bcall_get_vehicledata(
    self, msisdn, programcode: ProgramCode, payload, action
):
    validjsonresponse = None
    dataresponse = None
    response = None
    for i in range(self._config.max_retries):
        self._logger.info(
            "GetVehicleData: Requesting BCALL Data for msisdn {}. Retry attempt :: {}".format(
                msisdn, i
            ),
            extra={
                "msisdn": msisdn,
                "programcode": programcode,
                "cts-version": CtsVersion.ONE_DOT_ZERO,
                "action": action,
            },
        )
        # Requesting FCA External telematics BCALL to push data to us for the requested msisdn
        response = request_bcall_data(self, msisdn, programcode, payload, action)

        validjsonresponse = (
            response.headers.get("content-type") is not None
            and "json" in response.headers.get("content-type").lower()
        )
        if (
            response.status_code == HTTP_200_OK
            or response.status_code == HTTP_202_ACCEPTED
        ) and validjsonresponse:
            responsejson = response.json()
            # After successful request for FCA External telematics BCALL to push data to us and
            # Data push call from FCA calls Save Vehicle data endpoint
            # to save data in database so we search here again in database to look for data.
            db_response = get_vehicledata_response(self, msisdn, programcode)
            if db_response is not None:
                responsemessage = (
                    responsejson["message"]
                    if checkjsonnode("message", responsejson)
                    else "Successfully retrieved"
                )
                dataresponse = create_vehicledata_response(
                    db_response,
                    msisdn,
                    programcode,
                    InternalStatusType.SUCCESS,
                    responsemessage,
                )
                self._logger.info(
                    "GetVehicleData: Received BCALL Data from FCA from msisdn {} in Retry attempt :: {}".format(
                        msisdn, i
                    ),
                    extra={
                        "msisdn": msisdn,
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": action,
                    },
                )
                break

        sleep(self._config.delay_for_each_retry)
    return response, validjsonresponse, dataresponse


def internalstatus_conversion(responsestatus: str):
    #  responsestatus can be of any case which gets internally converted to uppercase
    responsestatus = responsestatus.upper()
    switcher = {
        "NOT FOUND": InternalStatusType.NOTFOUND,
        "ILLEGAL_ARGUMENT_ERROR": InternalStatusType.NOTFOUND,
        "MSISDN_DOESNT_EXIST": InternalStatusType.NOTFOUND,
        "REQUEST_SCHEMA_VALIDATION_FAILED": InternalStatusType.BADREQUEST,
        "BAD REQUEST": InternalStatusType.BADREQUEST,
        "INVALID_STATE_ERROR": InternalStatusType.FORBIDDEN,
        "FORBIDDEN": InternalStatusType.FORBIDDEN,
        "UNAUTHORIZED": InternalStatusType.FORBIDDEN,
        "INTERNAL SERVER ERROR": InternalStatusType.INTERNALSERVERERROR,
        "CANCELLED": InternalStatusType.CANCELED,
        "ERROR": InternalStatusType.ERROR,
        "SERVICE_NOT_PROVISIONED": InternalStatusType.FORBIDDEN,
    }
    return switcher.get(responsestatus, InternalStatusType.INTERNALSERVERERROR)


def reformat_msisdn(msisdn, max_length):
    if len(msisdn) == 10:
        msisdn = "1" + msisdn
    else:
        # Due to FCA telecomm config limitation, below logic had to be implemented to read defined size
        # It strips from the end for max_length
        msisdn = msisdn[-int(max_length) :]

    return msisdn


def map_primarytable(
    msisdn: str,
    programcode: ProgramCode,
    vehicledata: VehicleDataRequest,
    custom_extension: CustomExtension,
    tblprimary: ConnectedVehicleTable,
):
    return tblprimary(
        msisdn=msisdn,
        programcode=programcode,
        request_key="{}-{}".format(programcode, msisdn),
        countrycode=custom_extension.vehicleInfo.country,
        eventid=vehicledata.EventID,
        language=custom_extension.vehicleInfo.language,
        servicetype=vehicledata.Data.bcallType,
        timestamp=convert_epoch_to_utc_timestamp(vehicledata.Timestamp),
        event_datetime=get_utc_epoch(),  # UTC epoch
        latitude=float(
            custom_extension.vehicleInfo.vehicleLocation.positionLatitude
            if custom_extension.vehicleInfo.vehicleLocation.positionLatitude is not None
            else vehicledata.Data.latitude
        ),
        longitude=float(
            custom_extension.vehicleInfo.vehicleLocation.positionLongitude
            if custom_extension.vehicleInfo.vehicleLocation.positionLongitude
            is not None
            else vehicledata.Data.longitude
        ),
        altitude=str(custom_extension.vehicleInfo.vehicleLocation.positionAltitude)
        if custom_extension.vehicleInfo.vehicleLocation.positionAltitude is not None
        else None,
        vin=custom_extension.vehicleInfo.vin,
        brand=custom_extension.vehicleInfo.brand,
        modelname=custom_extension.vehicleInfo.model,
        modelyear=custom_extension.vehicleInfo.year,
        calltype=custom_extension.calltype,
        vehicletype=custom_extension.vehicleInfo.vehicleType,
        enginestatus=custom_extension.vehicleInfo.engineStatusEnum,
        odometer=custom_extension.vehicleInfo.odometer,
        positiondirection="{}".format(
            custom_extension.vehicleInfo.vehicleLocation.positionDirection
        ),
        vehiclespeed=custom_extension.vehicleInfo.vehicleSpeed,
        callreason=vehicledata.Data.callReason,
        calltrigger=vehicledata.Data.callTrigger,
    )


def save_supplementdata(
    self,
    msisdn: str,
    programcode: ProgramCode,
    vehicledata: VehicleDataRequest,
    custom_extension: CustomExtension,
):
    try:
        vehicle_supplementtable = map_supplementtable(
            msisdn,
            programcode,
            vehicledata,
            custom_extension,
            self._SupplementTable,
        )
        vehicle_supplementtable.save()
        self._logger.info(
            "SaveVehicleData: Successfully saved additional vehicle data onto supplement table {} for msisdn: {}".format(
                vehicledata, msisdn
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
    vehicledata: VehicleDataRequest,
    custom_extension: CustomExtension,
    tblsupplement: ConnectedVehicleSupplementTable,
):
    return tblsupplement(
        msisdn=msisdn,
        programcode=programcode,
        request_key="{}-{}".format(programcode, msisdn),
        timestamp=convert_epoch_to_utc_timestamp(vehicledata.Timestamp),
        event_datetime=get_utc_epoch(),
        callcenternumber=vehicledata.Data.callCenterNumber,
        devicetype=custom_extension.device.deviceType,
        deviceos=custom_extension.device.deviceOS,
        headunittype=custom_extension.device.headUnitType,
        manufacturername=custom_extension.device.manufacturerName,
        region=custom_extension.device.region,
        screensize=custom_extension.device.screenSize,
        tbmserialnum=custom_extension.device.tbmSerialNum,
        tbmpartnum=custom_extension.device.tbmPartNum,
        tbmhardwareversion=custom_extension.device.tbmHardwareVersion,
        tbmsoftwareversion=custom_extension.device.tbmSoftwareVersion,
        simiccid=int(custom_extension.device.simIccid),
        simimsi=custom_extension.device.simImsi,
        nadimei=custom_extension.device.nadImei,
        nadhardwareversion=custom_extension.device.nadHardwareVersion,
        nadsoftwareversion=custom_extension.device.nadSoftwareVersion,
        nadserialnum=custom_extension.device.nadSerialNum,
        nadpartnum=custom_extension.device.nadPartNum,
        wifimac=custom_extension.device.wifiMac,
        huserialnum=custom_extension.device.huSerialNum,
        hupartnum=custom_extension.device.huPartNum,
        huhardwareversion=custom_extension.device.huHardwareVersion,
        husoftwareversion=custom_extension.device.huSoftwareVersion,
        ishunavigationpresent=custom_extension.device.isHUNavigationPresent,
        distanceremainingfornextservice=custom_extension.distanceRemainingForNextService,
        estimatedpositionerror=custom_extension.vehicleInfo.vehicleLocation.estimatedPositionError,
        estimatedaltitudeerror=custom_extension.vehicleInfo.vehicleLocation.estimatedAltitudeError,
        isgpsfixnotavailable=custom_extension.vehicleInfo.vehicleLocation.isGPSFixNotAvailable,
        gpsfixtype=custom_extension.vehicleInfo.vehicleLocation.gpsFixTypeEnum,
        errortelltale=None
        if hasattr(custom_extension.errorTellTale, "isOilPressure")
        else custom_extension.errorTellTale,
        isoilpressure=custom_extension.errorTellTale.isOilPressure
        if hasattr(custom_extension.errorTellTale, "isOilPressure")
        else None,
        fuelremaining=custom_extension.fuelRemaining,
        stateofcharge=custom_extension.stateofCharge,
        tirepressure=None
        if hasattr(custom_extension.tirePressure, "flTirePressure")
        else custom_extension.tirePressure,
        fltirepressure=custom_extension.tirePressure.flTirePressure
        if hasattr(custom_extension.tirePressure, "flTirePressure")
        else None,
        frtirepressure=custom_extension.tirePressure.frTirePressure
        if hasattr(custom_extension.tirePressure, "frTirePressure")
        else None,
        rltirepressure=custom_extension.tirePressure.rlTirePressure
        if hasattr(custom_extension.tirePressure, "rlTirePressure")
        else None,
        rrtirepressure=custom_extension.tirePressure.rrTirePressure
        if hasattr(custom_extension.tirePressure, "rrTirePressure")
        else None,
        rl2tirepressure=custom_extension.tirePressure.rl2TirePressure
        if hasattr(custom_extension.tirePressure, "rl2TirePressure")
        else None,
        rr2tirepressure=custom_extension.tirePressure.rr2TirePressure
        if hasattr(custom_extension.tirePressure, "rr2TirePressure")
        else None,
        fltirests=custom_extension.tirePressure.flTireSts
        if hasattr(custom_extension.tirePressure, "flTireSts")
        else None,
        frtirests=custom_extension.tirePressure.frTireSts
        if hasattr(custom_extension.tirePressure, "frTireSts")
        else None,
        rltirests=custom_extension.tirePressure.rlTireSts
        if hasattr(custom_extension.tirePressure, "rlTireSts")
        else None,
        rrtirests=custom_extension.tirePressure.rrTireSts
        if hasattr(custom_extension.tirePressure, "rrTireSts")
        else None,
        daysremainingfornextservice=custom_extension.daysRemainingForNextService,
    )

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Type, Optional
import requests
from src.config.verizon_config import VerizonConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.models.enums.status_type import Status
from src.services.client_service import ClientService
from src.services.dynamodb_tables import (
    ConnectedVehicleSupplementTable,
    ConnectedVehicleTable,
)
from src.services.dynamodb_helper import get_vehicledata_for_config_enabled_client_only
from src.services.soaphandlers.soap_handler import get_zeepclient
from src.utilities.extensions.datetime_extension import get_utc_epoch
from src.utilities.extensions.string_extension import isnotnull_whitespaceorempty
from src.verizon.models.data.vehicle_data import VehicleData
from starlette.status import HTTP_200_OK

logger = logging.getLogger(__name__)


class VerizonService(ClientService):
    def __init__(
        self,
        config: VerizonConfig,
        table: Type[ConnectedVehicleTable],
        supplementtable: Type[ConnectedVehicleSupplementTable],
    ):
        self._logger = logger
        self._config = config
        self._Table = table
        self._SupplementTable = supplementtable

    def get_vehicledata(self, msisdn: str, programcode: ProgramCode):
        try:
            self._logger.info(
                "GetVehicleData: Payload received for msisdn: {} programcode: {}".format(
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
            # check and get data from database based of db check flag
            if self._config.dynamodb_check_enable:
                dataresponse = get_data_from_database(
                    self, msisdn, programcode, CtsVersion.ONE_DOT_ZERO
                )

            if dataresponse is not None:
                return dataresponse
            else:
                client = retrieve_zeepclient(
                    self._config.base_url,
                    super()._localstore,
                    self._config.wsdl,
                    self._config.root_cert,
                )

                vehicle_locationrequest = {
                    "Header": {
                        "SourceName": "",
                        # Optional
                        "TargetName": "",
                        "TransactionId": "",
                        "Timestamp": datetime.now(),
                    },
                    # Optional
                    "CTIInteractionID": "",
                    "MDN": msisdn,
                }
                with client.settings(raw_response=True):
                    fullresponse = client.service.RequestVehicleLocation(
                        **vehicle_locationrequest
                    )

                    operation = client.service._binding._operations[
                        "RequestVehicleLocation"
                    ]

                    response = client.service._binding.process_reply(
                        client, operation, fullresponse
                    )
                    headerresponse = get_additionaldata_from_header(
                        self, fullresponse, msisdn, programcode
                    )

                response_status = InternalStatusType.INTERNALSERVERERROR
                if (
                    isnotnull_whitespaceorempty(response)
                    and ("Response") in response
                    and ("ResponseStatus") in response["Response"]
                    and response["Response"]["ResponseStatus"] is not None
                    and ("ResponseDescription") in response["Response"]
                    and response["Response"]["ResponseDescription"] is not None
                ):
                    response_status = internalstatus_conversion(
                        response["Response"]["ResponseStatus"],
                        response["Response"]["ResponseDescription"],
                    )

                    if response_status == InternalStatusType.SUCCESS:
                        self._logger.info(
                            "GetVehicleData: Successfully received response from external SOAP call for msisdn:{} status:{} programcode:{} response_payload:{}".format(
                                msisdn, Status.SUCCESS, programcode, response
                            ),
                            extra={
                                "msisdn": msisdn,
                                "programcode": programcode,
                                "cts-version": CtsVersion.ONE_DOT_ZERO,
                                "action": "GetVehicleData",
                            },
                        )

                        # Map vehicle data success response using external call response
                        vehicledata = map_vehicledata_response(
                            msisdn, programcode, response_status, response
                        )

                        # Save the data in dynamodb for audit and return the model on success
                        self.save_vehicledata(
                            msisdn, programcode, vehicledata, headerresponse
                        )

                        return vehicledata

            self._logger.error(
                "GetVehicleData: Error occurred in external SOAP call for msisdn: {} programcode: {} status: {} error_response_payload: {}".format(
                    msisdn, programcode, response_status, response
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
                msisdn=msisdn,
                status=response_status,
                responsemessage="{status}{description}".format(
                    status=response["Response"]["ResponseStatus"],
                    description=", {} ".format(
                        response["Response"]["ResponseDescription"]
                    ),
                ),
            )

        except Exception as e:
            self._logger.error(
                "GetVehicleData: Gateway error: External Verizon : Error Occured: {} for msisdn: {} programcode: {}".format(
                    e, msisdn, programcode
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

    def health(self, programcode: ProgramCode, ctsversion: CtsVersion):
        try:
            self._logger.info(
                "Health: Performing healthcheck for programcode: {} and cts-version: {}".format(
                    programcode, ctsversion
                ),
                extra={
                    "programcode": programcode,
                    "cts-version": ctsversion,
                    "action": "Health",
                },
            )

            response = requests.get(
                "{base_url}?wsdl".format(base_url=self._config.base_url),
                verify=self._config.root_cert,
            )

            validresponse = (
                response.headers.get("content-type") is not None
                and "xml" in response.headers.get("content-type").lower()
            )

            if validresponse and response.status_code == HTTP_200_OK:
                self._logger.info(
                    "Health: Success for programcode: {} and cts-version: {} status:{}".format(
                        programcode,
                        ctsversion,
                        InternalStatusType.SUCCESS,
                    ),
                    extra={
                        "programcode": programcode,
                        "action": "Health",
                        "cts-version": ctsversion,
                    },
                )

                return VehicleData(
                    status=InternalStatusType.SUCCESS,
                    responsemessage="HealthCheck passed",
                )
            else:
                response_status = internalstatus_conversion(response.text)
                self._logger.error(
                    "Health: Failed for programcode: {} and cts-version: {} status:{}".format(
                        programcode,
                        ctsversion,
                        response_status,
                    ),
                    exc_info=True,
                    stack_info=True,
                    extra={
                        "programcode": programcode,
                        "action": "Health",
                        "cts-version": ctsversion,
                    },
                )

                return VehicleData(
                    status=response_status, responsemessage=response.text
                )
        except Exception as e:
            self._logger.error(
                "Health: Gateway error: External Verizon : Error Occured: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "action": "Health",
                    "cts-version": ctsversion,
                },
            )
            return VehicleData(
                status=InternalStatusType.INTERNALSERVERERROR, responsemessage=str(e)
            )

    def assign_agent(self, any):
        raise NotImplementedError

    def populate_vehicledata(self, any):
        raise NotImplementedError

    def save_vehicledata(
        self, msisdn, programcode, vehicledata, headerresponse: Optional[dict] = None
    ):
        if vehicledata is not None:
            try:
                self._logger.info(
                    "SaveVehicleData: Payload received for msisdn: {} data: {}".format(
                        msisdn, vehicledata
                    ),
                    extra={
                        "programcode": programcode,
                        "msisdn": msisdn,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "action": "SaveVehicleData",
                    },
                )
                if type(vehicledata) is not VehicleData:
                    vehicledata = self.populate_vehicledata(
                        msisdn, programcode, vehicledata
                    )
                vehicle_table = self._Table(
                    msisdn=vehicledata.msisdn,
                    programcode=vehicledata.programcode,
                    eventid=headerresponse["floweventid"]
                    if headerresponse is not None and "floweventid" in headerresponse
                    else "NONE",
                    flowid=headerresponse["flowid"]
                    if headerresponse is not None and "flowid" in headerresponse
                    else "NONE",
                    correlationid=headerresponse["correlationflowid"]
                    if headerresponse is not None
                    and "correlationflowid" in headerresponse
                    else "NONE",
                    calldate=vehicledata.calldate,
                    calltime=vehicledata.calltime,
                    request_key=vehicledata.programcode + "-" + vehicledata.msisdn,
                    event_datetime=vehicledata.event_datetime,
                    timestamp=vehicledata.timestamp,
                    vin=vehicledata.vin,
                    latitude=float(vehicledata.latitude)
                    if vehicledata.latitude is not None
                    else 0,
                    longitude=float(vehicledata.longitude)
                    if vehicledata.longitude is not None
                    else 0,
                    headingdirection=vehicledata.headingdirection,
                    brand=vehicledata.brand,
                    modelname=vehicledata.modelname,
                    modelyear=vehicledata.modelyear,
                    modelcode=vehicledata.modelcode,
                    modeldesc="NONE",
                    calltype="NONE",
                    phonenumber=vehicledata.phonenumber,
                    customerfirstname=vehicledata.customerfirstname,
                    customerlastname=vehicledata.customerlastname,
                    modelcolor=vehicledata.modelcolor,
                    srnumber=vehicledata.srnumber,
                    locationaddress=vehicledata.locationaddress,
                    locationcity=vehicledata.locationcity,
                    locationstate=vehicledata.locationstate,
                    locationpostalcode=vehicledata.locationpostalcode,
                    countrycode=vehicledata.countrycode,
                    locationconfidence=vehicledata.locationconfidence,
                    locationtrueness=vehicledata.locationtrueness,
                    cruisingrange=vehicledata.cruisingrange,
                    ismoving=vehicledata.ismoving,
                    altitude=vehicledata.altitude,
                    language=vehicledata.language,
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
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
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
                    "SaveVehicleData: Unable to save the data onto dynamodb : {} for msisdn: {} programcode: {}".format(
                        e, msisdn, programcode
                    ),
                    exc_info=True,
                    stack_info=True,
                    extra={
                        "programcode": programcode,
                        "msisdn": msisdn,
                        "action": "SaveVehicleData",
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
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
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "payload": data,
                    "action": "SaveVehicleData",
                },
            )

    def terminate(self, any):
        raise NotImplementedError


def internalstatus_conversion(responsestatus: str, responsemessage: str = ""):
    #  responsestatus can be of any case which gets internally converted to uppercase
    responsestatus = responsestatus.upper()
    switcher = {
        "FAILED EXECUTION": serviceerror_conversion(responsemessage),
        "SUCCESSFUL EXECUTION": InternalStatusType.SUCCESS,
        "FILE NOT FOUND": InternalStatusType.NOTFOUND,
    }
    return switcher.get(responsestatus, InternalStatusType.INTERNALSERVERERROR)


def serviceerror_conversion(responsemessage: str):
    if (
        isnotnull_whitespaceorempty(responsemessage)
        and ("No Data Found").casefold() in responsemessage.casefold()
    ):
        return InternalStatusType.NOTFOUND

    return InternalStatusType.INTERNALSERVERERROR


def retrieve_zeepclient(serviceurl, localstore, wsdl, root_cert):
    return get_zeepclient(wsdl, serviceurl, root_cert, "verizon_zeepclient", localstore)


def get_timestamp_from_calldate(calldate, calltime):
    try:
        return datetime.strptime(
            "{} {}".format(calldate, calltime),
            "%m/%d/%Y %H:%M:%S",
        )
    except Exception as e:
        return datetime.now()


# For saving verizon header data response in db
def get_additionaldata_from_header(self, fullresponse, msisdn, programcode):
    try:
        root = ET.fromstring(fullresponse.text)

        floweventid = (
            (root[0].getchildren()[2].getchildren()[1].getchildren()[1].text)
            if ("FlowEventId")
            in root[0].getchildren()[2].getchildren()[1].getchildren()[1].tag
            else "NONE"
        )
        flowid = (
            (root[0].getchildren()[2].getchildren()[1].getchildren()[2].text)
            if ("FlowId")
            in root[0].getchildren()[2].getchildren()[1].getchildren()[2].tag
            else "NONE"
        )
        correlationflowid = (
            (root[0].getchildren()[2].getchildren()[1].getchildren()[3].text)
            if ("CorrelationFlowId")
            in root[0].getchildren()[2].getchildren()[1].getchildren()[3].tag
            else "NONE"
        )

        headerresponse = {
            "floweventid": floweventid,
            "flowid": flowid,
            "correlationflowid": correlationflowid,
        }
        self._logger.info(
            "GetVehicleData: Successfully retrieved additional data headerresponse: {} from response: {} for msisdn: {} programcode: {}".format(
                headerresponse, fullresponse.text, msisdn, programcode
            ),
            extra={
                "programcode": programcode,
                "msisdn": msisdn,
                "action": "GetVehicleData",
                "cts-version": CtsVersion.ONE_DOT_ZERO,
            },
        )
        return headerresponse
    except Exception as e:
        self._logger.error(
            "GetVehicleData: Unable to get addtional data from response: {} Error Occured: {} for msisdn: {} programcode: {}".format(
                fullresponse, e, msisdn, programcode
            ),
            exc_info=True,
            stack_info=True,
            extra={
                "programcode": programcode,
                "msisdn": msisdn,
                "action": "GetVehicleData",
                "cts-version": CtsVersion.ONE_DOT_ZERO,
            },
        )
        headerresponse = {
            "floweventid": "NONE",
            "flowid": "NONE",
            "correlationflowid": "NONE",
        }
        return headerresponse


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


def map_vehicledata_response(msisdn, programcode, response_status, response):
    return VehicleData(
        msisdn=msisdn,
        status=response_status,
        programcode=programcode,
        calldate=response["CallDate"]
        if ("CallDate") in response
        and isnotnull_whitespaceorempty(response["CallDate"])
        else "NONE",
        calltime=response["CallTime"]
        if ("CallTime") in response
        and isnotnull_whitespaceorempty(response["CallTime"])
        else "NONE",
        event_datetime=get_utc_epoch(),
        timestamp=get_timestamp_from_calldate(
            response["CallDate"],
            response["CallTime"],
        )
        if (
            isnotnull_whitespaceorempty(
                response["CallDate"] if ("CallDate") in response else None
            )
            and isnotnull_whitespaceorempty(
                response["CallTime"] if ("CallTime") in response else None
            )
        )
        else datetime.now(),
        customerfirstname=response["CustomerFirstName"]
        if ("CustomerFirstName") in response
        and isnotnull_whitespaceorempty(response["CustomerFirstName"])
        else "NONE",
        customerlastname=response["CustomerLastName"]
        if ("CustomerLastName") in response
        and isnotnull_whitespaceorempty(response["CustomerLastName"])
        else "NONE",
        modelyear=response["VehicleYear"]
        if ("VehicleYear") in response
        and isnotnull_whitespaceorempty(response["VehicleYear"])
        else "NONE",
        brand=response["Make"]
        if ("Make") in response and isnotnull_whitespaceorempty(response["Make"])
        else "NONE",
        modelname=response["Model"]
        if ("Model") in response and isnotnull_whitespaceorempty(response["Model"])
        else "NONE",
        modelcode=response["Make"]
        if ("Make") in response and isnotnull_whitespaceorempty(response["Make"])
        else "NONE",
        vin=response["VIN"]
        if ("VIN") in response and isnotnull_whitespaceorempty(response["VIN"])
        else "NONE",
        modelcolor=response["ExteriorColor"]
        if ("ExteriorColor") in response
        and isnotnull_whitespaceorempty(response["ExteriorColor"])
        else "NONE",
        phonenumber=response["FromLocationPhoneNo"]
        if ("FromLocationPhoneNo") in response
        and isnotnull_whitespaceorempty(response["FromLocationPhoneNo"])
        else "NONE",
        srnumber=response["SRNumber"]
        if ("SRNumber") in response
        and isnotnull_whitespaceorempty(response["SRNumber"])
        else "NONE",
        locationaddress=response["FromLocationAddress"]
        if ("FromLocationAddress") in response
        and isnotnull_whitespaceorempty(response["FromLocationAddress"])
        else "NONE",
        locationcity=response["FromLocationCity"]
        if ("FromLocationCity") in response
        and isnotnull_whitespaceorempty(response["FromLocationCity"])
        else "NONE",
        locationstate=response["FromLocationState"]
        if ("FromLocationState") in response
        and isnotnull_whitespaceorempty(response["FromLocationState"])
        else "NONE",
        locationpostalcode=response["FromLocationZip"]
        if ("FromLocationZip") in response
        and isnotnull_whitespaceorempty(response["FromLocationZip"])
        else "NONE",
        countrycode=response["FromLocationCountry"]
        if ("FromLocationCountry") in response
        and isnotnull_whitespaceorempty(response["FromLocationCountry"])
        else "NONE",
        locationconfidence=response["Location_confidence"]
        if ("Location_confidence") in response
        and isnotnull_whitespaceorempty(response["Location_confidence"])
        else "NONE",
        locationtrueness=response["Location_trueness"]
        if ("Location_trueness") in response
        and isnotnull_whitespaceorempty(response["Location_trueness"])
        else "NONE",
        cruisingrange=response["Cruising_range"]
        if ("Cruising_range") in response
        and isnotnull_whitespaceorempty(response["Cruising_range"])
        else "NONE",
        ismoving=response["Is_moving"]
        if ("Is_moving") in response
        and isnotnull_whitespaceorempty(response["Is_moving"])
        else False,
        latitude=response["FromLocationLatitude"]
        if ("FromLocationLatitude") in response
        and isnotnull_whitespaceorempty(response["FromLocationLatitude"])
        else 0,
        longitude=response["FromLocationLongitude"]
        if ("FromLocationLongitude") in response
        and isnotnull_whitespaceorempty(response["FromLocationLongitude"])
        else 0,
        altitude=response["Altitude"]
        if ("Altitude") in response
        and isnotnull_whitespaceorempty(response["Altitude"])
        else "NONE",
        headingdirection=response["Direction_heading"]
        if ("Direction_heading") in response
        and isnotnull_whitespaceorempty(response["Direction_heading"])
        else "NONE",
        language=response["Hmi_language"]
        if ("Hmi_language") in response
        and isnotnull_whitespaceorempty(response["Hmi_language"])
        else "NONE",
        responsemessage="Successfully retrieved",
    )


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
            customerfirstname=response.customerfirstname,
            customerlastname=response.customerlastname,
            modelyear=response.modelyear,
            brand=response.brand,
            modelname=response.modelname,
            modelcode=response.modelcode,
            vin=response.vin,
            modelcolor=response.modelcolor,
            phonenumber=response.phonenumber,
            srnumber=response.srnumber,
            locationaddress=response.locationaddress,
            locationcity=response.locationcity,
            locationstate=response.locationstate,
            locationpostalcode=response.locationpostalcode,
            countrycode=response.countrycode,
            locationconfidence=response.locationconfidence,
            locationtrueness=response.locationtrueness,
            cruisingrange=response.cruisingrange,
            ismoving=response.ismoving,
            latitude=response.latitude,
            longitude=response.longitude,
            altitude=response.altitude,
            headingdirection=response.headingdirection,
            language=response.language,
        )

import logging
from datetime import datetime
from typing import Type

import requests
from src.config.siriusxm_config import SiriusXmConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.models.exceptions.application_exception import ApplicationException
from src.services.client_service import ClientService
from src.services.dynamodb_tables import ConnectedVehicleTable
from src.services.soaphandlers.soap_handler import get_zeepclient
from src.siriusxm.models.data.vehicle_data import VehicleData, VehicleHexData
from src.siriusxm.models.domain.agentassignment import AgentAssignment
from src.siriusxm.models.domain.terminate import Terminate
from src.utilities.extensions.datetime_extension import get_utc_epoch
from src.utilities.extensions.string_extension import isnotnull_whitespaceorempty
from starlette.status import HTTP_200_OK

logger = logging.getLogger(__name__)


class SiriusXmService(ClientService):
    def __init__(self, config: SiriusXmConfig, table: Type[ConnectedVehicleTable]):
        self._logger = logger
        self._config = config
        self._Table = table

    def save_vehicledata(self, data):
        vehicledata = self.populate_vehicledata(data)

        try:
            self._logger.info(
                "SaveVehicleData: Vehicle data for referenceid: {} programcode: {} data: {}".format(
                    vehicledata.referenceid, vehicledata.programcode, data
                ),
                extra={
                    "programcode": vehicledata.programcode,
                    "referenceid": vehicledata.referenceid,
                    "action": "SaveVehicleData",
                },
            )

            # Create an vehicle data item.
            vehicle_table = self._Table(
                request_key=vehicledata.programcode + "-" + vehicledata.referenceid,
                event_datetime=get_utc_epoch(),
                referenceid=vehicledata.referenceid,
                programcode=vehicledata.programcode,
                timestamp=datetime.now(),
                vin=vehicledata.vin,
                language=vehicledata.language,
                longitude=float(vehicledata.longitude),
                latitude=float(vehicledata.latitude),
            )

            # Save the data in dynamodb
            vehicle_table.save()

            hexvaluedata = self.populate_hex(
                vehicledata.referenceid,
                vehicledata.latitude,
                vehicledata.longitude,
                vehicledata.vin,
                vehicledata.language,
            )
            hexdata = VehicleHexData(Value=hexvaluedata)
            vehicledata.hexvehicledata = hexdata
            vehicledata.status = InternalStatusType.SUCCESS
            vehicledata.responsemessage = "Successfully Saved."
            return vehicledata

        except Exception as e:
            self._logger.error(
                "SaveVehicleData: error occured: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": vehicledata.programcode,
                    "referenceid": vehicledata.referenceid,
                    "action": "SaveVehicleData",
                },
            )
            vehicledata.responsemessage = e.args[0]
            vehicledata.status = InternalStatusType.INTERNALSERVERERROR

            return vehicledata

    def populate_vehicledata(self, data):
        try:
            if data is None:
                raise ApplicationException("SaveVehicleData: No Data found")
            vehicle_data = VehicleData(**data)
            return vehicle_data
        except Exception as e:
            self._logger.error(
                "SaveVehicleData: Data Population failed: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={"action": "SaveVehicleData"},
            )

    def populate_hex(self, referenceid, latitude, longitude, vin, language):
        strings = ["ROADSIDE", referenceid, latitude, longitude, vin, language]
        hexvalue = "~".join(strings)
        val = hexvalue.encode("utf-8").hex()
        # Appending 00 in front of hex
        val = "00" + val
        return val

    def get_vehicledata(self, id: str, programcode: ProgramCode):
        try:
            self._logger.info(
                "GetVehicleData: Vehicle data for referenceid: {} programcode: {}".format(
                    id, programcode
                ),
                extra={
                    "programcode": programcode,
                    "referenceid": id,
                    "action": "GetVehicleData",
                },
            )

            for dataitem in self._Table.query(
                programcode + "-" + id,
                self._Table.referenceid == id,
                scan_index_forward=False,
                limit=1,
            ):
                self._logger.info(
                    "GetVechicleData: Response for referenceid: {} programcode: {}".format(
                        id, programcode
                    ),
                    extra={
                        "programcode": programcode,
                        "referenceid": id,
                        "action": "GetVehicleData",
                    },
                )

                return VehicleData(
                    status=InternalStatusType.SUCCESS,
                    responsemessage="Successfully retrieved",
                    language=dataitem.language,
                    programcode=dataitem.programcode,
                    referenceid=dataitem.referenceid,
                    calldate=dataitem.timestamp.strftime("%Y-%m-%d"),
                    calltime=dataitem.timestamp.strftime("%H:%M"),
                    timestamp=dataitem.timestamp,
                    latitude=dataitem.latitude,
                    longitude=dataitem.longitude,
                    event_datetime=dataitem.event_datetime,
                    vin=dataitem.vin,
                )

            return VehicleData(
                status=InternalStatusType.NOTFOUND, responsemessage="No data found"
            )

        except Exception as e:
            self._logger.error(
                "GetVehicleData: Gateway error: SiriusXm: Error Occured: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "referenceid": id,
                    "action": "GetVehicleData",
                },
            )

            return VehicleData(
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=e.args[0] if e.args.__len__() > 0 else None,
            )

    def assign_agent(self, agentassignment: AgentAssignment):
        try:
            self._logger.info(
                "AgentAssignment: Request for Referenceid: {} programcode {} .".format(
                    agentassignment.referenceid, agentassignment.programcode
                ),
                extra={
                    "programcode": agentassignment.programcode,
                    "referenceid": agentassignment.referenceid,
                    "action": "AgentAssignment",
                },
            )
            client = retrieve_zeepclient(
                self._config.base_url,
                super()._localstore,
                self._config.wsdl,
                self._config.root_cert,
            )
            agent_assignment = {
                "reference-id": agentassignment.referenceid,
                "is-assigned": agentassignment.isassigned,
            }

            response = client.service.agentAssigned(**agent_assignment)
            if (
                isnotnull_whitespaceorempty(response)
                and isnotnull_whitespaceorempty(response["result-code"])
                and response["result-msg"] is not None
            ):
                agentassignment.response_referenceid = response["reference-id"]
                agentassignment.responsestatus = internalstatus_conversion(
                    response["result-code"], response["result-msg"]
                )
                agentassignment.responsemessage = response["result-msg"]

                self._logger.info(
                    "AgentAssignment:Response for referenceid:{} status:{} message:{} programcode:{}".format(
                        agentassignment.referenceid,
                        response["result-code"],
                        agentassignment.responsemessage,
                        agentassignment.programcode,
                    ),
                    extra={
                        "programcode": agentassignment.programcode,
                        "referenceid": agentassignment.referenceid,
                        "action": "AgentAssignment",
                    },
                )

                if (
                    agentassignment.responsestatus.casefold()
                    == InternalStatusType.SUCCESS.casefold()
                ):
                    return True
        except Exception as e:
            self._logger.error(
                "AgentAssignment: Gateway error: SiriusXm: Error Occured: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": agentassignment.programcode,
                    "referenceid": agentassignment.referenceid,
                    "action": "AgentAssignment",
                },
            )
            agentassignment.responsemessage = e

        return False

    def terminate(self, terminate: Terminate):
        try:
            self._logger.info(
                "Terminate: Request for Referenceid: {} and programcode {}".format(
                    terminate.referenceid, terminate.programcode
                ),
                extra={
                    "programcode": terminate.programcode,
                    "referenceid": terminate.referenceid,
                    "action": "Terminate",
                },
            )

            client = retrieve_zeepclient(
                self._config.base_url,
                super()._localstore,
                self._config.wsdl,
                self._config.root_cert,
            )
            payload = {"reference-id": terminate.referenceid}

            response = client.service.terminate(**payload)
            if (
                isnotnull_whitespaceorempty(response)
                and isnotnull_whitespaceorempty(response["result-code"])
                and response["result-msg"] is not None
            ):
                terminate.response_referenceid = response["reference-id"]
                terminate.status = internalstatus_conversion(
                    response["result-code"], response["result-msg"]
                )
                terminate.responsemessage = response["result-msg"]
                self._logger.info(
                    "Terminate: Response for referenceid:{} status:{} message:{} programcode:{}".format(
                        terminate.referenceid,
                        response["result-code"],
                        terminate.responsemessage,
                        terminate.programcode,
                    ),
                    extra={
                        "programcode": terminate.programcode,
                        "referenceid": terminate.referenceid,
                        "action": "Terminate",
                    },
                )

                if terminate.status.casefold() == InternalStatusType.SUCCESS.casefold():
                    return True
        except Exception as e:
            self._logger.error(
                "Terminate: Gateway error: SiriusXm: Error Occured: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": terminate.programcode,
                    "referenceid": terminate.referenceid,
                    "action": "Terminate",
                },
            )
            terminate.responsemessage = e

        return False

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

                return VehicleData(status=InternalStatusType.SUCCESS, responsemessage="HealthCheck passed")
            else:
                response_status = internalstatus_conversion(response.text)
                self._logger.error(
                    "Health: Failed for programcode: {} and cts-version: {} status:{}".format(
                        programcode,
                        ctsversion,
                        response_status,
                    ),
                    extra={
                        "programcode": programcode,
                        "action": "Health",
                        "cts-version": ctsversion,
                    },
                )

                return VehicleData(status=response_status, responsemessage=response.text)
        except Exception as e:
            self._logger.error(
                "Health: Gateway error: SiriusXM: Error Occured: {}".format(e),
                exc_info=True,
                stack_info=True,
                extra={
                    "programcode": programcode,
                    "action": "Health",
                    "cts-version": ctsversion,
                },
            )
            return VehicleData(
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=str(e)
            )


def internalstatus_conversion(responsestatus: str, responsemessage: str = ""):
    #  responsestatus can be of any case which gets internally converted to uppercase
    responsestatus = responsestatus.upper()
    switcher = {
        "NO_ERROR": InternalStatusType.SUCCESS,
        "ILLEGAL_ARGUMENT_ERROR": InternalStatusType.NOTFOUND,
        "INVALID_STATE_ERROR": InternalStatusType.FORBIDDEN,
        "REFERENCE_ID_NOT_FOUND": InternalStatusType.NOTFOUND,
        "INTERNAL_SERVER_ERROR": InternalStatusType.INTERNALSERVERERROR,
        "BAD_REQUEST": InternalStatusType.BADREQUEST,
        "CANCELLED": InternalStatusType.CANCELED,
        "ERROR": InternalStatusType.ERROR,
        "SERVICE_ERROR": serviceerror_conversion(responsemessage),
        "FILE NOT FOUND": InternalStatusType.NOTFOUND,
    }
    return switcher.get(responsestatus, InternalStatusType.INTERNALSERVERERROR)


def serviceerror_conversion(responsemessage: str):
    if (
        isnotnull_whitespaceorempty(responsemessage)
        and ("No reference id found").casefold() in responsemessage.casefold()
    ):
        return InternalStatusType.NOTFOUND

    return InternalStatusType.INTERNALSERVERERROR


def retrieve_zeepclient(serviceurl, localstore, wsdl, root_cert):
    return get_zeepclient(
        wsdl, serviceurl, root_cert, "siriusxm_zeepclient", localstore
    )

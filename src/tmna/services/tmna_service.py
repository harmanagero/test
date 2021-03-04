import logging

import requests
from src.config.tmna_config import TmnaConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.client_service import ClientService
from src.tmna.models.data.terminate import Terminate
from src.utilities.extensions.json_extension import checkjsonnode, seterrorjson
from src.utilities.extensions.string_extension import isnull_whitespaceorempty
from starlette.status import HTTP_200_OK, HTTP_202_ACCEPTED

logger = logging.getLogger(__name__)


class TmnaService(ClientService):
    def __init__(
        self,
        config: TmnaConfig,
    ):
        self._logger = logger
        self._config = config

    def terminate(self, eventid: str, programcode: ProgramCode, payload):
        if (
            payload is None
            or checkjsonnode("eventId", payload) == False
            or isnull_whitespaceorempty(payload["eventId"])
            or checkjsonnode("callEndIntentional", payload) == False
            or checkjsonnode("dispositionType", payload) == False
        ):
            self._logger.error(
                "Terminate: Payload is missing or invalid: {} for eventid {}".format(
                    payload, eventid
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
                eventid=eventid,
                status=InternalStatusType.BADREQUEST,
                responsemessage="Payload is missing or invalid",
            )
        try:
            self._logger.info(
                "Terminate: Request for eventid: {}".format(eventid),
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "payload": payload,
                    "action": "Terminate",
                },
            )

            requestbody = payload
            serviceurl = "{}{}".format(
                self._config.base_url, self._config.terminate_url
            )
            headers = {
                "content-type": "application/json",
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
                    "Terminate: TMNA response for eventid:{} status:{} success_response_payload:{}".format(
                        eventid, InternalStatusType.SUCCESS, responsejson
                    ),
                    extra={
                        "programcode": programcode,
                        "cts-version": CtsVersion.ONE_DOT_ZERO,
                        "payload": payload,
                        "action": "Terminate",
                    },
                )

                return Terminate(
                    eventid=eventid,
                    status=InternalStatusType.SUCCESS,
                    responsemessage=responsejson["resultMessage"]
                    if checkjsonnode("resultMessage", responsejson)
                    else "Successfully terminated the call",
                )
            if validjsonresponse:
                responsejson = response.json()[0]
                errorjson = seterrorjson(
                    responsejson["resultCode"]
                    if checkjsonnode("resultCode", responsejson)
                    else (
                        responsejson["error"]
                        if checkjsonnode("error", responsejson)
                        else "NA"
                    ),
                    responsejson["resultMessage"]
                    if checkjsonnode("resultMessage", responsejson)
                    else (
                        responsejson["message"]
                        if checkjsonnode("message", responsejson)
                        else "NA"
                    ),
                )
            else:
                errorjson = seterrorjson(response.reason, response.text)

            errorstatus = internalstatus_conversion(errorjson["status"])
            self._logger.error(
                "Terminate: Error occurred in TMNA Terminate call for eventid:{} status:{} error_response_payload:{}".format(
                    eventid,
                    errorstatus,
                    errorjson
                    if validjsonresponse
                    else "{}, missing json response from external TMNA service".format(
                        response
                    ),
                ),
                extra={
                    "programcode": programcode,
                    "cts-version": CtsVersion.ONE_DOT_ZERO,
                    "payload": payload,
                    "action": "Terminate",
                },
            )

            return Terminate(
                eventid=eventid,
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
                "Terminate: Gateway error: External TMNA: Error Occured: {} for eventid {}".format(
                    e, eventid
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
                eventid=eventid,
                status=InternalStatusType.INTERNALSERVERERROR,
                responsemessage=e.args[0] if e.args.__len__() > 0 else None,
            )

    def save_vehicledata(self, any):
        raise NotImplementedError

    def get_vehicledata(self, any):
        raise NotImplementedError

    def assign_agent(self, any):
        raise NotImplementedError

    def populate_vehicledata(self, any):
        raise NotImplementedError

    def health(self, programcode: ProgramCode, ctsversion: CtsVersion):
        raise NotImplementedError


def internalstatus_conversion(responsestatus: str):
    #  responsestatus can be of any case which gets internally converted to uppercase
    responsestatus = responsestatus.upper()
    switcher = {
        "NOT FOUND": InternalStatusType.NOTFOUND,
        "ILLEGAL_ARGUMENT_ERROR": InternalStatusType.NOTFOUND,
        "INVALID EVENT ID": InternalStatusType.NOTFOUND,
        "REQUEST_SCHEMA_VALIDATION_FAILED": InternalStatusType.BADREQUEST,
        "INVALID REQUEST": InternalStatusType.BADREQUEST,
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

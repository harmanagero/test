from unittest.mock import patch

import pytest
from src.config.tmna_config import TmnaConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.tmna.models.data.terminate import Terminate
from src.tmna.services.tmna_service import TmnaService


@pytest.fixture
def patched_rest_client():
    with patch("src.tmna.services.tmna_service.requests") as patched_rest_client:
        yield patched_rest_client


successjson = {"resultMessage": "Request processed successfully"}
notfoundjson = [
    {
        "resultMessage": "Record with specified eventid does not exist",
        "resultCode": "Invalid event id",
    }
]
badrequestjson = [{"resultCode": "Invalid request", "resultMessage": "Bad Request"}]
schemaerrorjson = [
    {
        "resultCode": "REQUEST_SCHEMA_VALIDATION_FAILED",
        "resultMessage": "schema validation failed",
    }
]
unauthorizedjson = [{"error": "unauthorized", "message": "not authorized"}]
servicenotprovisionedjson = [
    {
        "resultMessage": "Service not provisioned",
        "resultCode": "SERVICE_NOT_PROVISIONED",
    }
]


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.headers = {"content-type": "application/json;charset=UTF-8"}

        def json(self):
            return self.json_data

    if "successjson" in args[0]:
        return MockResponse(successjson, 200)
    elif "badrequestjson" in args[0]:
        return MockResponse(badrequestjson, 400)
    elif "schemaerrorjson" in args[0]:
        return MockResponse(schemaerrorjson, 400)
    elif "unauthorizedjson" in args[0]:
        return MockResponse(unauthorizedjson, 403)
    elif "servicenotprovisionedjson" in args[0]:
        return MockResponse(servicenotprovisionedjson, 403)
    elif "content_notsupported" in args[0]:
        mock = MockResponse("b'Server Error", 500)
        mock.headers = {"content-type": "text/plain"}
        mock.reason = "Internal Server Error"
        mock.text = "Server Error"
        return mock

    return MockResponse(notfoundjson, 404)


@pytest.fixture
def setup_tmna_service(
    mock_logger,
):
    uut = TmnaService(
        config=TmnaConfig(
            base_url="https://baseurl",
            terminate_url="https://terminate_url",
            root_cert="root_cert",
        ),
    )
    yield uut


@pytest.mark.parametrize("payload_instruction", ["all_nodes", "mandated_nodes"])
def test_service_terminate_on_success_return_200(
    patched_rest_client, mock_logger, payload_instruction
):
    patched_rest_client.post.side_effect = mocked_requests_post
    tmnaservice = TmnaService(
        config=TmnaConfig(
            base_url="https://successjson",
            terminate_url="/a",
            root_cert="root_cert",
        ),
    )

    if payload_instruction == "all_nodes":
        payload = tmna_payload()
    else:
        payload = tmna_payload_mandate_nodes()

    dataresponse = tmnaservice.terminate(
        "5feaba04a3a41e0001990550", ProgramCode.TOYOTA, payload
    )

    assert type(dataresponse) == Terminate
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.eventid == "5feaba04a3a41e0001990550"
    assert dataresponse.responsemessage == "Request processed successfully"


@pytest.mark.parametrize(
    "requesturl, expectedmessage",
    [
        ("https://badrequestjson/", "Bad Request"),
        ("https://schemaerrorjson/", "schema validation failed"),
    ],
)
def test_service_terminate_on_badrequest_should_return_400(
    setup_tmna_service, patched_rest_client, requesturl, expectedmessage
):
    patched_rest_client.post.side_effect = mocked_requests_post
    tmnaservice = setup_tmna_service
    tmnaservice._config.base_url = requesturl

    dataresponse = tmnaservice.terminate(
        "5feaba04a3a41e0001990552", ProgramCode.TOYOTA, tmna_payload()
    )

    assert type(dataresponse) == Terminate
    assert dataresponse.status == InternalStatusType.BADREQUEST
    assert dataresponse.eventid == "5feaba04a3a41e0001990552"
    assert dataresponse.responsemessage == expectedmessage


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {
            "callEndIntentional": "true",
            "dispositionType": "ACN_ESCALATION",
            "dispositionNotes": "Notes by RSA",
        },
        {
            "eventId": None,
            "callEndIntentional": "true",
            "dispositionType": "ACN_ESCALATION",
        },
        {
            "eventId": "eventId",
            "incidentClosureTime": "2020-11-30T21:45:17Z",
            "dispositionType": "ACN_ESCALATION",
            "dispositionNotes": "Notes by RSA",
        },
        {
            "eventId": "eventId",
            "callEndIntentional": "true",
            "incidentClosureTime": "2020-11-30T21:45:17Z",
        },
    ],
    ids=[
        "payload_None",
        "Missing_Eventid",
        "Eventid_None",
        "Missing_callEndIntentional",
        "Missing_dispositionType",
    ],
)
def test_service_terminate_on_invalid_payload_should_return_400(
    setup_tmna_service, payload
):
    dataresponse = setup_tmna_service.terminate("eventid", ProgramCode.TOYOTA, payload)

    assert type(dataresponse) == Terminate
    assert dataresponse.status == InternalStatusType.BADREQUEST
    assert dataresponse.eventid == "eventid"
    assert dataresponse.responsemessage == "Payload is missing or invalid"


def test_service_terminate_on_request_unauthorised_should_return_403(
    setup_tmna_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post
    tmnaservice = setup_tmna_service
    tmnaservice._config.base_url = "https://unauthorizedjson/"

    response = setup_tmna_service.terminate(
        "eventid", ProgramCode.TOYOTA, tmna_payload_mandate_nodes()
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.FORBIDDEN
    assert response.responsemessage == "not authorized"


def test_service_terminate_on_request_service_not_provisioned_should_return_403(
    setup_tmna_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post
    tmnaservice = setup_tmna_service
    tmnaservice._config.base_url = "https://servicenotprovisionedjson/"

    response = setup_tmna_service.terminate(
        "eventid", ProgramCode.TOYOTA, tmna_payload_mandate_nodes()
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.FORBIDDEN
    assert response.responsemessage == "Service not provisioned"


def test_service_terminate_on_request_not_found_should_return_404(
    setup_tmna_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post

    response = setup_tmna_service.terminate(
        "12345678901", ProgramCode.TOYOTA, tmna_payload()
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.NOTFOUND
    assert response.responsemessage == "Record with specified eventid does not exist"


def test_service_terminate_on_exception_should_return_500(
    setup_tmna_service, patched_rest_client
):
    patched_rest_client.post.side_effect = Exception("something wrong")

    response = setup_tmna_service.terminate(
        "12345678901", ProgramCode.TOYOTA, tmna_payload()
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "something wrong"


def test_service_terminate_on_content_notsupported_should_return_500(
    setup_tmna_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post
    tmnaservice = setup_tmna_service
    tmnaservice._config.base_url = "https://content_notsupported/"

    response = tmnaservice.terminate("12345678901", ProgramCode.TOYOTA, tmna_payload())

    assert type(response) == Terminate
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "Server Error"


def tmna_payload():
    return {
        "callEndIntentional": "true",
        "dispositionNotes": "NA",
        "dispositionType": "ACN_ESCALATION",
        "eventId": "5feaba04a3a41e0001990550",
        "incidentClosureTime": "2020-12-29T05:10:07Z",
    }


def tmna_payload_mandate_nodes():
    return {
        "callEndIntentional": "true",
        "dispositionType": "ACN_ESCALATION",
        "eventId": "5feaba04a3a41e0001990550",
    }


# Not implemented abstract method tests
def test_tmna_serivce_on_calling_save_vehicledata_raise_notimplementedexception(
    setup_tmna_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_tmna_service.save_vehicledata(any)
    assert execinfo.type == NotImplementedError


def test_tmna_serivce_on_calling_get_vehicledata_raise_notimplementedexception(
    setup_tmna_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_tmna_service.get_vehicledata(any)
    assert execinfo.type == NotImplementedError


def test_tmna_serivce_on_calling_assign_agent_raise_notimplementedexception(
    setup_tmna_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_tmna_service.assign_agent(any)
    assert execinfo.type == NotImplementedError


def test_tmna_serivce_on_calling_populate_vehicledata_raise_notimplementedexception(
    setup_tmna_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_tmna_service.populate_vehicledata(any)
    assert execinfo.type == NotImplementedError


def test_tmna_serivce_on_calling_health_raise_notimplementedexception(
    setup_tmna_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_tmna_service.health(ProgramCode.TOYOTA, CtsVersion.ONE_DOT_ZERO)
    assert execinfo.type == NotImplementedError

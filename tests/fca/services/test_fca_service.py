from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
from src.config.dynamo_config import DynamoConfig
from src.config.fca_config import FcaConfig
from src.fca.models.data.vehicle_data import VehicleData
from src.fca.models.domain.terminate import Terminate
from src.fca.services.fca_service import (
    FcaService,
    create_vehicledata_response,
    get_vehicledata_response,
    request_bcall_data,
    retrial_request_bcall_get_vehicledata,
)
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.callstatus_type import CallStatus
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.dynamodb_tables import (
    ConnectedVehicleTable,
    get_main_table,
    get_supplement_table,
)

BASE_URL = "fooBaseURL"
DYNAMO_TABLE_NAME = "cv-table"
API_KEY = "fooAPIKEY"
BCALL_DATA_URL = "fooBcallURL"
TERMINATE_BCALL_URL = "fooTerminateURL"
MAX_RETRIES = 3
DELAY_FOR_EACH_RETRY = 1
MAX_ANI_LENGTH = 11
API_GATEWAY_BASE_PATH = "foopath"


@pytest.fixture
def patched_setup_logger():
    with patch("src.fca.services.fca_service.logger") as mocked_setup:
        yield mocked_setup


@pytest.fixture
def setup_fca_service(mock_dynamo_cv_table, mock_dynamo_supplement_cv_table):
    uut = FcaService(
        config=FcaConfig(
            base_url=BASE_URL,
            raw_api_key=API_KEY,
            api_key=API_KEY,
            dynamo_table_name=DYNAMO_TABLE_NAME,
            bcall_data_url=BCALL_DATA_URL,
            terminate_bcall_url=TERMINATE_BCALL_URL,
            max_retries=MAX_RETRIES,
            delay_for_each_retry=DELAY_FOR_EACH_RETRY,
            max_ani_length=MAX_ANI_LENGTH,
            api_gateway_base_path=API_GATEWAY_BASE_PATH,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    yield uut


@pytest.fixture
def patched_rest_client():
    with patch("src.fca.services.fca_service.requests") as patched_rest_client:
        yield patched_rest_client


successjson = {"message": "Bcall request sent successfully"}
notfoundjson = [
    {
        "message": "Record with specified msisdn does not exist",
        "detailedErrorCode": "MSISDN_DOESNT_EXIST",
    }
]
badrequestjson = [{"message": "bad request", "detailedErrorCode": "Bad Request"}]
schemaerrorjson = [
    {
        "detailedErrorCode": "REQUEST_SCHEMA_VALIDATION_FAILED",
        "message": "invalid request",
    }
]
unauthorizedjson = [{"error": "unauthorized", "message": "not authorized"}]
servicenotprovisionedjson = [
    {
        "message": "Service not provisioned",
        "detailedErrorCode": "SERVICE_NOT_PROVISIONED",
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
        return MockResponse(successjson, 202)
    elif "badrequestjson" in args[0]:
        return MockResponse(badrequestjson, 400)
    elif "schemaerrorjson" in args[0]:
        return MockResponse(schemaerrorjson, 400)
    elif "unauthorizedjson" in args[0]:
        return MockResponse(unauthorizedjson, 403)
    elif "servicenotprovisionedjson" in args[0]:
        return MockResponse(servicenotprovisionedjson, 403)
    elif "bcallcontent_notsupported" in args[0]:
        errormessage = "Exception calling fca bcall endpoint for msisdn: 12345678901"
        mock = MockResponse(errormessage.encode("ASCII"), 500)
        mock.headers = {"content-type": "text/plain"}
        mock.reason = "Internal Server Error"
        mock.text = errormessage
        return mock
    elif "content_notsupported" in args[0]:
        mock = MockResponse("b'Server Error", 500)
        mock.headers = {"content-type": "text/plain"}
        mock.reason = "Internal Server Error"
        mock.text = "Server Error"
        return mock

    return MockResponse(notfoundjson, 404)


def test_fca_service_get_vehicledata_on_success_return_200(
    mock_logger, mock_dynamo_cv_table, setup_fca_service
):
    mock_dynamo_cv_table.query.return_value = generate_valid_fca_data_singlelist()
    dataresponse = setup_fca_service.get_vehicledata(
        msisdn="12345678901", programcode="fca"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.calldate == dataresponse.timestamp.strftime("%Y-%m-%d")
    assert dataresponse.calltime == dataresponse.timestamp.strftime("%H:%M")
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "fca"
    assert dataresponse.vin == "TESTFIRSTVIN"


def test_fca_service_get_vehicledata_on_exception_should_return_500(
    patched_setup_logger, mock_dynamo_cv_table, setup_fca_service
):
    patched_setup_logger.info.side_effect = Exception
    dataresponse = setup_fca_service.get_vehicledata(
        msisdn="12345678901", programcode="fca"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.INTERNALSERVERERROR


def test_fca_service_get_vehicledata_on_bcall_request_success_return_200(
    patched_rest_client,
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
):
    patched_rest_client.post.side_effect = mocked_requests_post
    mock_dynamo_cv_table.query.return_value = [None]
    mock_dynamo_cv_table.query.side_effect = [
        [None],
        [None],
        generate_valid_fca_data_singlelist(),
    ]
    fcaservice = FcaService(
        config=FcaConfig(
            base_url="https://successjson",
            max_ani_length=11,
            bcall_data_url="/a",
            max_retries=3,
            delay_for_each_retry=1,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    dataresponse = fcaservice.get_vehicledata(msisdn="12345678901", programcode="fca")
    assert type(dataresponse) == VehicleData
    assert dataresponse.calldate == dataresponse.timestamp.strftime("%Y-%m-%d")
    assert dataresponse.calltime == dataresponse.timestamp.strftime("%H:%M")
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "fca"
    assert dataresponse.vin == "TESTFIRSTVIN"
    assert dataresponse.responsemessage == "Bcall request sent successfully"


def test_fca_service_get_vehicledata_on_bcall_request_success_but_no_data_in_db_return_404(
    patched_rest_client,
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
):
    patched_rest_client.post.side_effect = mocked_requests_post
    mock_dynamo_cv_table.query.return_value = [None]
    mock_dynamo_cv_table.query.side_effect = [[None], [None]]
    fcaservice = FcaService(
        config=FcaConfig(
            base_url="https://successjson",
            max_ani_length=11,
            bcall_data_url="/a",
            max_retries=3,
            delay_for_each_retry=1,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    dataresponse = fcaservice.get_vehicledata(msisdn="12345678901", programcode="fca")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.NOTFOUND
    assert (
        dataresponse.responsemessage == "No data is available for msisdn: 12345678901"
    )


@pytest.mark.parametrize(
    "requesturl, expectedmessage",
    [
        ("https://badrequestjson/", "bad request"),
        ("https://schemaerrorjson/", "invalid request"),
    ],
)
def test_fca_service_get_vehicledata_on_bcall_request_badrequest_should_return_400(
    patched_rest_client,
    mock_dynamo_cv_table,
    requesturl,
    expectedmessage,
    setup_fca_service,
):
    patched_rest_client.post.side_effect = mocked_requests_post
    mock_dynamo_cv_table.query.return_value = [None]
    mock_dynamo_cv_table.query.side_effect = [[None], [None]]
    fcaservice = setup_fca_service
    fcaservice._config.base_url = requesturl
    dataresponse = fcaservice.get_vehicledata(msisdn="12345678901", programcode="fca")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.BADREQUEST
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.responsemessage == expectedmessage


def test_fca_service_get_vehicledata_on_bcall_request_unauthorised_should_return_403(
    patched_rest_client, mock_dynamo_cv_table, setup_fca_service
):
    patched_rest_client.post.side_effect = mocked_requests_post
    mock_dynamo_cv_table.query.return_value = [None]
    mock_dynamo_cv_table.query.side_effect = [[None], [None]]
    fcaservice = setup_fca_service
    fcaservice._config.base_url = "https://unauthorizedjson/"
    dataresponse = fcaservice.get_vehicledata(msisdn="12345678901", programcode="fca")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.FORBIDDEN
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.responsemessage == "not authorized"


def test_fca_service_get_vehicledata_on_bcall_request_service_not_provisioned_should_return_403(
    patched_rest_client, mock_dynamo_cv_table, setup_fca_service
):
    patched_rest_client.post.side_effect = mocked_requests_post
    mock_dynamo_cv_table.query.return_value = [None]
    mock_dynamo_cv_table.query.side_effect = [[None], [None]]
    fcaservice = setup_fca_service
    fcaservice._config.base_url = "https://servicenotprovisionedjson/"
    dataresponse = fcaservice.get_vehicledata(msisdn="12345678901", programcode="fca")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.FORBIDDEN
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.responsemessage == "Service not provisioned"


def test_fca_service_get_vehicledata_on_bcall_request_bcallcontent_notsupported_should_return_500(
    patched_rest_client, mock_dynamo_cv_table, setup_fca_service
):
    patched_rest_client.post.side_effect = mocked_requests_post
    mock_dynamo_cv_table.query.return_value = [None]
    mock_dynamo_cv_table.query.side_effect = [[None], [None]]
    fcaservice = setup_fca_service
    fcaservice._config.base_url = "https://bcallcontent_notsupported/"
    dataresponse = fcaservice.get_vehicledata(msisdn="12345678901", programcode="fca")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.INTERNALSERVERERROR
    assert dataresponse.msisdn == "12345678901"
    assert (
        dataresponse.responsemessage
        == "Exception calling fca bcall endpoint for msisdn: 12345678901"
    )


@pytest.mark.parametrize(
    "msisdn, formatted_msisdn",
    [
        ("1234", "1234"),
        ("1234567890", "11234567890"),
        ("12345678901", "12345678901"),
        ("1234567890112", "34567890112"),
    ],
)
def test_fca_service_get_vehicledata_should_format_msisdn_as_expected(
    setup_fca_service, patched_rest_client, msisdn, formatted_msisdn
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = setup_fca_service

    dataresponse = fcaservice.get_vehicledata(msisdn=msisdn, programcode="fca")

    assert type(dataresponse) == VehicleData
    assert dataresponse.msisdn == formatted_msisdn


def test_service_terminate_on_success_return_200(
    patched_rest_client,
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = FcaService(
        config=FcaConfig(
            base_url="https://successjson",
            max_ani_length="11",
            terminate_bcall_url="/a",
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )

    dataresponse = fcaservice.terminate(
        "5243583607", "fca", {"callstatus": "TERMINATED"}
    )

    assert type(dataresponse) == Terminate
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "15243583607"
    assert dataresponse.responsemessage == "Bcall request sent successfully"
    assert dataresponse.callstatus == CallStatus.TERMINATED


@pytest.mark.parametrize(
    "msisdn, formatted_msisdn",
    [
        ("1234", "1234"),
        ("1234567890", "11234567890"),
        ("12345678901", "12345678901"),
        ("1234567890112", "34567890112"),
    ],
)
def test_service_terminate_should_format_msisdn_as_expected(
    setup_fca_service, patched_rest_client, msisdn, formatted_msisdn
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = setup_fca_service

    dataresponse = fcaservice.terminate(msisdn, "fca", {"callstatus": "TERMINATED"})

    assert type(dataresponse) == Terminate
    assert dataresponse.msisdn == formatted_msisdn


@pytest.mark.parametrize(
    "requesturl, expectedmessage",
    [
        ("https://badrequestjson/", "bad request"),
        ("https://schemaerrorjson/", "invalid request"),
    ],
)
def test_service_terminate_on_badrequest_should_return_400(
    setup_fca_service, patched_rest_client, requesturl, expectedmessage
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = setup_fca_service
    fcaservice._config.base_url = requesturl

    dataresponse = fcaservice.terminate(
        "123456789011", "fca", {"callstatus": "TERMINATED"}
    )

    assert type(dataresponse) == Terminate
    assert dataresponse.status == InternalStatusType.BADREQUEST
    assert dataresponse.msisdn == "23456789011"
    assert dataresponse.responsemessage == expectedmessage


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"call": "TERMINATED"},
        {"callstatus": ""},
        {"callstatus": " "},
        {"callstatus": "tErMiNaTeD"},
        {"callstatus": "ANY"},
    ],
)
def test_service_terminate_on_invalid_payload_should_return_400(
    setup_fca_service, payload
):
    dataresponse = setup_fca_service.terminate("12345678901", "fca", payload)

    assert type(dataresponse) == Terminate
    assert dataresponse.status == InternalStatusType.BADREQUEST
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.responsemessage == "callstatus in payload is missing or invalid"


def test_service_terminate_on_request_unauthorised_should_return_403(
    setup_fca_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = setup_fca_service
    fcaservice._config.base_url = "https://unauthorizedjson/"

    response = setup_fca_service.terminate(
        "12345678901", "fca", {"callstatus": "TERMINATED"}
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.FORBIDDEN
    assert response.responsemessage == "not authorized"


def test_service_terminate_on_request_service_not_provisioned_should_return_403(
    setup_fca_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = setup_fca_service
    fcaservice._config.base_url = "https://servicenotprovisionedjson/"

    response = setup_fca_service.terminate(
        "12345678901", "fca", {"callstatus": "TERMINATED"}
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.FORBIDDEN
    assert response.responsemessage == "Service not provisioned"


def test_service_terminate_on_request_not_found_should_return_404(
    setup_fca_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post

    response = setup_fca_service.terminate(
        "12345678901", "fca", {"callstatus": "TERMINATED"}
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.NOTFOUND
    assert response.responsemessage == "Record with specified msisdn does not exist"


def test_service_terminate_on_exception_should_return_500(
    setup_fca_service, patched_rest_client
):
    patched_rest_client.post.side_effect = Exception("something wrong")

    response = setup_fca_service.terminate(
        "12345678901", "fca", {"callstatus": "TERMINATED"}
    )

    assert type(response) == Terminate
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "something wrong"


def test_service_terminate_on_content_notsupported_should_return_500(
    setup_fca_service, patched_rest_client
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = setup_fca_service
    fcaservice._config.base_url = "https://content_notsupported/"

    response = fcaservice.terminate("12345678901", "fca", {"callstatus": "TERMINATED"})

    assert type(response) == Terminate
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "Server Error"


@mock_dynamodb2
@pytest.mark.parametrize(
    "is_brand_assist", [(True), (False)], ids=["Brand_Assist", "Roadside_Assist"]
)
def test_service_save_vehicledata_returns_200_if_success(mock_logger, is_brand_assist):
    TABLE_NAME = dynamodb_primarytable_setup("local-cv")
    primary_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    SUPPLEMENT_TABLE_NAME = dynamodb_primarytable_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    fcaservice = FcaService(
        config=FcaConfig(base_url="someurl"),
        table=primary_table,
        supplementtable=supplement_table,
    )

    if is_brand_assist:
        vehicledatajson = generate_valid_fca_maserati_data()
    else:
        vehicledatajson = generate_valid_maserati_roadside_assist_data()

    response = fcaservice.save_vehicledata("13234826699", "fca", vehicledatajson)

    conn = boto3.resource("dynamodb", region_name="us-east-1")
    primarytable = conn.Table(TABLE_NAME)
    result = primarytable.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("fca-13234826699"),
    )

    supplementtable = conn.Table(SUPPLEMENT_TABLE_NAME)
    supplementtable_result = supplementtable.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("fca-13234826699"),
    )

    assert type(response) == VehicleData
    assert response.msisdn == "13234826699"
    assert response.status == InternalStatusType.SUCCESS
    assert (
        response.responsemessage
        == "Successfully saved the vehicledata for msisdn: 13234826699"
    )

    assert result["Items"][0]["request_key"] == "fca-13234826699"
    assert result["Items"][0]["msisdn"] == "13234826699"

    assert result["Items"][0]["vin"] == "ZN661XUAXMX1007HT"
    assert result["Items"][0]["latitude"] == Decimal("42.53224182128906")
    assert result["Items"][0]["longitude"] == Decimal("-83.28421020507812")
    assert result["Items"][0]["brand"] == "MASERATI"
    assert result["Items"][0]["calltype"] == "BRAND"
    assert result["Items"][0]["altitude"] == "0.0"

    assert supplementtable_result["Items"][0]["callcenternumber"] == "+18449232959"
    assert supplementtable_result["Items"][0]["devicetype"] == "ENUM"
    assert supplementtable_result["Items"][0]["ishunavigationpresent"] == False
    assert supplementtable_result["Items"][0]["daysremainingfornextservice"] == Decimal(
        "0"
    )


@mock_dynamodb2
def test_save_vehicledata_returns_success_even_if_secondary_data_save_is_unsuccessful(
    mock_logger,
):

    TABLE_NAME = dynamodb_primarytable_setup("local-cv")
    primary_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    supplement_table = "invalid"

    fcaservice = FcaService(
        config=FcaConfig(base_url="someurl"),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_fca_maserati_data()
    response = fcaservice.save_vehicledata("13234826699", "fca", vehicledatajson)
    assert type(response) == VehicleData
    assert response.msisdn == "13234826699"
    assert response.status == InternalStatusType.SUCCESS
    assert (
        response.responsemessage
        == "Successfully saved the vehicledata for msisdn: 13234826699"
    )


@mock_dynamodb2
def test_save_vehicledata_returns_500_if_primary_data_save_is_unsuccessful(mock_logger):
    primary_table = "invalid"
    SUPPLEMENT_TABLE_NAME = dynamodb_primarytable_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    fcaservice = FcaService(
        config=FcaConfig(base_url="someurl"),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_fca_maserati_data()
    response = fcaservice.save_vehicledata("13234826699", "fca", vehicledatajson)
    assert type(response) == VehicleData
    assert response.msisdn == "13234826699"
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert (
        response.responsemessage
        == "Unable to save the vehicledata for msisdn: 13234826699"
    )


@mock_dynamodb2
@pytest.mark.parametrize(
    "valid_parent_nodes",
    [
        ({"Data": {"customExtension": {"some": "some"}}}),
        ({"Data": {"customExtension": {"vehicleDataUpload": {"some": "some"}}}}),
    ],
    ids=["Brand_Assist", "Roadside_Assist"],
)
def test_save_vehicledata_on_populate_vehicle_data_error_returns_500(
    setup_fca_service, valid_parent_nodes
):
    response = setup_fca_service.save_vehicledata(
        "5243583607", "fca", valid_parent_nodes
    )
    assert type(response) == VehicleData
    assert response.msisdn == "5243583607"
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert (
        response.responsemessage
        == "Unable to save the vehicledata for msisdn: 5243583607"
    )


@pytest.mark.parametrize(
    "invalid_json",
    [
        (None),
        ({"customExtension": {"some": "some"}}),
        ({"Data": {"vehicleDataUpload": {"some": "some"}}}),
        ({"Data": {"customExtension": None}}),
        ({"Data": {"customExtension": {"vehicleDataUpload": None}}}),
    ],
    ids=[
        "None",
        "Missing_Data_Node",
        "Missing_CustomExtension",
        "CustomExtension_None",
        "VehicleDataUpload_None",
    ],
)
def test_save_vehicledata_on_bad_request_returns_400(setup_fca_service, invalid_json):
    response = setup_fca_service.save_vehicledata("5243583607", "fca", invalid_json)
    assert type(response) == VehicleData
    assert response.msisdn == "5243583607"
    assert response.status == InternalStatusType.BADREQUEST
    assert (
        response.responsemessage
        == "SaveVehicleData: Json payload is invalid for msisdn: 5243583607"
    )


def dynamodb_primarytable_setup(tblname):
    TABLE_NAME = tblname
    client = boto3.client("dynamodb", region_name="us-east-1")
    client.create_table(
        AttributeDefinitions=[
            {"AttributeName": "request_key", "AttributeType": "S"},
            {"AttributeName": "event_datetime", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "request_key", "KeyType": "HASH"},
            {"AttributeName": "event_datetime", "KeyType": "RANGE"},
        ],
        TableName=TABLE_NAME,
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    return TABLE_NAME


def generate_valid_fca_maserati_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1605801545525,
        "Data": {
            "callCenterNumber": "+18449232959",
            "bcallType": "BRAND_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "en_US",
            "latitude": 42.53224182128906,
            "longitude": -83.28421020507812,
            "fuelRemaining": 0.0,
            "engineStatus": "STARTED",
            "customExtension": {
                "callCenterNumber": "+18449232959",
                "CallReasonEnum": "DEFAULT",
                "callTriggerEnum": "MANUAL",
                "calltype": "BRAND",
                "daysRemainingForNextService": 0,
                "device": {
                    "deviceType": "ENUM",
                    "deviceOS": "QNX",
                    "headUnitType": "",
                    "manufacturerName": "",
                    "region": "NAFTA",
                    "screenSize": "Five",
                    "tbmSerialNum": "",
                    "tbmPartNum": "",
                    "tbmHardwareVersion": "",
                    "tbmSoftwareVersion": "",
                    "simIccid": "89011704272516122319",
                    "simImsi": "",
                    "simMsisdn": "13234826699",
                    "nadImei": "015395000488103",
                    "nadHardwareVersion": "",
                    "nadSoftwareVersion": "",
                    "nadSerialNum": "",
                    "nadPartNum": "",
                    "wifiMac": "",
                    "huSerialNum": "",
                    "huPartNum": "",
                    "huHardwareVersion": "",
                    "huSoftwareVersion": "",
                    "isHUNavigationPresent": False,
                },
                "distanceRemainingForNextService": 0,
                "errorTellTale": None,
                "fuelRemaining": 0.0,
                "stateofCharge": 0.0,
                "tirePressure": "None",
                "vehicleInfo": {
                    "vehicleLocation": {
                        "positionLatitude": 42.53224182128906,
                        "positionLongitude": -83.28421020507812,
                        "estimatedPositionError": 0,
                        "positionAltitude": 0.0,
                        "gpsFixTypeEnum": "ID_FIX_NO_POS",
                        "isGPSFixNotAvailable": False,
                        "estimatedAltitudeError": 0,
                        "positionDirection": 0.0,
                    },
                    "vehicleSpeed": 0.0,
                    "odometer": 0,
                    "engineStatusEnum": "RUN",
                    "language": "en_US",
                    "country": "US",
                    "vehicleType": "PASSENGER_CLASSM1",
                    "vin": "ZN661XUAXMX1007HT",
                    "brand": "MASERATI",
                    "model": "",
                    "year": "",
                },
            },
        },
    }


def generate_valid_maserati_roadside_assist_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1606849518918,
        "Data": {
            "callCenterNumber": "+18449232959",
            "bcallType": "ROADSIDE_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "en_US",
            "latitude": 42.53224182128906,
            "longitude": -83.28421020507812,
            "fuelRemaining": 0.0,
            "engineStatus": "STARTED",
            "customExtension": {
                "vehicleDataUpload": {
                    "callCenterNumber": "+18449232959",
                    "CallReasonEnum": "DEFAULT",
                    "callTriggerEnum": "MANUAL",
                    "calltype": "BRAND",
                    "daysRemainingForNextService": 0,
                    "device": {
                        "deviceType": "ENUM",
                        "deviceOS": "QNX",
                        "headUnitType": "",
                        "manufacturerName": "",
                        "region": "NAFTA",
                        "screenSize": "Five",
                        "tbmSerialNum": "",
                        "tbmPartNum": "",
                        "tbmHardwareVersion": "",
                        "tbmSoftwareVersion": "",
                        "simIccid": "89011704272519496322",
                        "simImsi": "",
                        "simMsisdn": "13234826699",
                        "nadImei": "015395000737897",
                        "nadHardwareVersion": "",
                        "nadSoftwareVersion": "",
                        "nadSerialNum": "",
                        "nadPartNum": "",
                        "wifiMac": "",
                        "huSerialNum": "",
                        "huPartNum": "",
                        "huHardwareVersion": "",
                        "huSoftwareVersion": "",
                        "isHUNavigationPresent": False,
                    },
                    "distanceRemainingForNextService": 0,
                    "fuelRemaining": 0.0,
                    "stateofCharge": 0.0,
                    "vehicleInfo": {
                        "vehicleLocation": {
                            "positionLatitude": 42.53224182128906,
                            "positionLongitude": -83.28421020507812,
                            "estimatedPositionError": 0,
                            "positionAltitude": 0.0,
                            "gpsFixTypeEnum": "ID_FIX_NO_POS",
                            "isGPSFixNotAvailable": False,
                            "estimatedAltitudeError": 0,
                            "positionDirection": 0.0,
                        },
                        "vehicleSpeed": 0.0,
                        "odometer": 0,
                        "engineStatusEnum": "RUN",
                        "language": "en_US",
                        "country": "US",
                        "vehicleType": "PASSENGER_CLASSM1",
                        "vin": "ZN661XUAXMX1007HT",
                        "brand": "MASERATI",
                        "model": "",
                        "year": "",
                    },
                }
            },
        },
    }


def test_populate_vehicledata_with_valid_brand_assist_data_populate_as_expected(
    setup_fca_service,
):
    fca_maserati_json = generate_valid_fca_maserati_data()
    vehicledata = setup_fca_service.populate_vehicledata(
        "12345678901", "fca", fca_maserati_json
    )
    assert vehicledata.EventID == fca_maserati_json["EventID"]
    assert vehicledata.Data.bcallType == fca_maserati_json["Data"]["bcallType"]
    assert (
        vehicledata.Data.customExtension.device
        == fca_maserati_json["Data"]["customExtension"]["device"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleInfo
        == fca_maserati_json["Data"]["customExtension"]["vehicleInfo"]
    )


def test_populate_vehicledata_with_valid_roadside_assist_data_populate_as_expected(
    setup_fca_service,
):
    fca_maserati_roadside_assist_json = generate_valid_maserati_roadside_assist_data()
    vehicledata = setup_fca_service.populate_vehicledata(
        "12345678901", "fca", fca_maserati_roadside_assist_json
    )
    assert vehicledata.EventID == fca_maserati_roadside_assist_json["EventID"]
    assert (
        vehicledata.Data.bcallType
        == fca_maserati_roadside_assist_json["Data"]["bcallType"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleDataUpload.device
        == fca_maserati_roadside_assist_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["device"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleDataUpload.vehicleInfo
        == fca_maserati_roadside_assist_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["vehicleInfo"]
    )


@mock_dynamodb2
@pytest.mark.parametrize(
    "is_brand_assist",
    [(True), (False)],
    ids=["Brand_Assist", "Roadside_Assist"],
)
def test_service_save_jeep_vehicledata_returns_200_if_success(
    mock_logger, is_brand_assist
):
    TABLE_NAME = dynamodb_primarytable_setup("local-cv")
    primary_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    SUPPLEMENT_TABLE_NAME = dynamodb_primarytable_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    fcaservice = FcaService(
        config=FcaConfig(base_url="someurl"),
        table=primary_table,
        supplementtable=supplement_table,
    )

    if is_brand_assist:
        vehicledatajson = generate_valid_brand_assist_jeep_vehicle_data()
        response = fcaservice.save_vehicledata("9999954321", "fca", vehicledatajson)

        conn = boto3.resource("dynamodb", region_name="us-east-1")
        primarytable = conn.Table(TABLE_NAME)
        result = primarytable.query(
            Limit=1,
            ScanIndexForward=False,
            KeyConditionExpression=Key("request_key").eq("fca-9999954321"),
        )

        supplementtable = conn.Table(SUPPLEMENT_TABLE_NAME)
        supplementtable_result = supplementtable.query(
            Limit=1,
            ScanIndexForward=False,
            KeyConditionExpression=Key("request_key").eq("fca-9999954321"),
        )

        assert type(response) == VehicleData
        assert response.msisdn == "9999954321"
        assert response.status == InternalStatusType.SUCCESS
        assert (
            response.responsemessage
            == "Successfully saved the vehicledata for msisdn: 9999954321"
        )

        assert result["Items"][0]["request_key"] == "fca-9999954321"
        assert result["Items"][0]["msisdn"] == "9999954321"

        assert result["Items"][0]["latitude"] == Decimal("42.6812744140625")
        assert result["Items"][0]["longitude"] == Decimal("-83.21455383300781")
        assert result["Items"][0]["vehiclespeed"] == Decimal("0.0")
        assert result["Items"][0]["brand"] == "JEEP"
        assert result["Items"][0]["altitude"] == "0.0"

        assert supplementtable_result["Items"][0]["callcenternumber"] == "+18449232963"
        assert supplementtable_result["Items"][0]["devicetype"] == "ENUM"
        assert supplementtable_result["Items"][0]["ishunavigationpresent"] == False
        assert supplementtable_result["Items"][0][
            "daysremainingfornextservice"
        ] == Decimal("0")

        assert supplementtable_result["Items"][0]["stateofcharge"] == Decimal("0")
        assert supplementtable_result["Items"][0]["estimatedpositionerror"] == Decimal(
            "0"
        )
        assert supplementtable_result["Items"][0]["isgpsfixnotavailable"] == False
        assert supplementtable_result["Items"][0]["estimatedaltitudeerror"] == Decimal(
            "0"
        )
        assert supplementtable_result["Items"][0]["fuelremaining"] == Decimal("0.0")

    else:
        vehicledatajson = generate_valid_roadside_assist_jeep_vehicle_data()

        response = fcaservice.save_vehicledata("9999954321", "fca", vehicledatajson)

        conn = boto3.resource("dynamodb", region_name="us-east-1")
        primarytable = conn.Table(TABLE_NAME)
        result = primarytable.query(
            Limit=1,
            ScanIndexForward=False,
            KeyConditionExpression=Key("request_key").eq("fca-9999954321"),
        )

        supplementtable = conn.Table(SUPPLEMENT_TABLE_NAME)
        supplementtable_result = supplementtable.query(
            Limit=1,
            ScanIndexForward=False,
            KeyConditionExpression=Key("request_key").eq("fca-9999954321"),
        )

        assert type(response) == VehicleData
        assert response.msisdn == "9999954321"
        assert response.status == InternalStatusType.SUCCESS
        assert (
            response.responsemessage
            == "Successfully saved the vehicledata for msisdn: 9999954321"
        )

        assert result["Items"][0]["request_key"] == "fca-9999954321"
        assert result["Items"][0]["msisdn"] == "9999954321"

        assert result["Items"][0]["latitude"] == Decimal("42.6812744140625")
        assert result["Items"][0]["longitude"] == Decimal("-83.21455383300781")
        assert result["Items"][0]["brand"] == "JEEP"
        assert result["Items"][0]["altitude"] == "0.0"

        assert supplementtable_result["Items"][0]["callcenternumber"] == "+18449232963"
        assert supplementtable_result["Items"][0]["devicetype"] == "ENUM"
        assert supplementtable_result["Items"][0]["ishunavigationpresent"] == False
        assert supplementtable_result["Items"][0][
            "daysremainingfornextservice"
        ] == Decimal("0")

        assert supplementtable_result["Items"][0]["stateofcharge"] == Decimal(
            "66.69174194335938"
        )
        assert supplementtable_result["Items"][0]["estimatedpositionerror"] == Decimal(
            "0"
        )
        assert supplementtable_result["Items"][0]["isgpsfixnotavailable"] == False
        assert supplementtable_result["Items"][0]["isoilpressure"] == True
        assert supplementtable_result["Items"][0]["estimatedaltitudeerror"] == Decimal(
            "0"
        )
        assert supplementtable_result["Items"][0]["fuelremaining"] == Decimal(
            "11.636523"
        )


@mock_dynamodb2
def test_save_jeep_vehicledata_returns_success_even_if_secondary_data_save_is_unsuccessful(
    mock_logger,
):

    TABLE_NAME = dynamodb_primarytable_setup("local-cv")
    primary_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    supplement_table = "invalid"

    fcaservice = FcaService(
        config=FcaConfig(base_url="someurl"),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_brand_assist_jeep_vehicle_data()
    response = fcaservice.save_vehicledata("12482026960", "fca", vehicledatajson)
    assert type(response) == VehicleData
    assert response.msisdn == "12482026960"
    assert response.status == InternalStatusType.SUCCESS
    assert (
        response.responsemessage
        == "Successfully saved the vehicledata for msisdn: 12482026960"
    )


@mock_dynamodb2
def test_save_jeep_vehicledata_returns_500_if_primary_data_save_is_unsuccessful(
    mock_logger,
):
    primary_table = "invalid"
    SUPPLEMENT_TABLE_NAME = dynamodb_primarytable_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    fcaservice = FcaService(
        config=FcaConfig(base_url="someurl"),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_fca_maserati_data()
    response = fcaservice.save_vehicledata("12482026960", "fca", vehicledatajson)
    assert type(response) == VehicleData
    assert response.msisdn == "12482026960"
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert (
        response.responsemessage
        == "Unable to save the vehicledata for msisdn: 12482026960"
    )


@mock_dynamodb2
@pytest.mark.parametrize(
    "valid_parent_nodes",
    [
        ({"Data": {"customExtension": {"some": "some"}}}),
        ({"Data": {"customExtension": {"vehicleDataUpload": {"some": "some"}}}}),
    ],
    ids=["Brand_Assist", "Roadside_Assist"],
)
def test_save_jeep_vehicledata_on_populate_vehicle_data_error_returns_500(
    setup_fca_service, valid_parent_nodes
):
    response = setup_fca_service.save_vehicledata(
        "52435836072", "fca", valid_parent_nodes
    )
    assert type(response) == VehicleData
    assert response.msisdn == "52435836072"
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert (
        response.responsemessage
        == "Unable to save the vehicledata for msisdn: 52435836072"
    )


@pytest.mark.parametrize(
    "invalid_json",
    [
        (None),
        ({"customExtension": {"some": "some"}}),
        ({"Data": {"vehicleDataUpload": {"some": "some"}}}),
        ({"Data": {"customExtension": None}}),
        ({"Data": {"customExtension": {"vehicleDataUpload": None}}}),
    ],
    ids=[
        "None",
        "Missing_Data_Node",
        "Missing_CustomExtension",
        "CustomExtension_None",
        "VehicleDataUpload_None",
    ],
)
def test_save_jeep_vehicledata_on_bad_request_returns_400(
    setup_fca_service, invalid_json
):
    response = setup_fca_service.save_vehicledata("52435836072", "fca", invalid_json)
    assert type(response) == VehicleData
    assert response.msisdn == "52435836072"
    assert response.status == InternalStatusType.BADREQUEST
    assert (
        response.responsemessage
        == "SaveVehicleData: Json payload is invalid for msisdn: 52435836072"
    )


def generate_valid_brand_assist_jeep_vehicle_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1606764386353,
        "Data": {
            "callCenterNumber": "+18449232963",
            "bcallType": "BRAND_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "en_US",
            "latitude": 42.6812744140625,
            "longitude": -83.21455383300781,
            "fuelRemaining": 0.0,
            "engineStatus": "STARTED",
            "customExtension": {
                "callCenterNumber": "+18449232963",
                "CallReasonEnum": "DEFAULT",
                "callTriggerEnum": "MANUAL",
                "calltype": "BRAND",
                "daysRemainingForNextService": 0,
                "device": {
                    "deviceType": "ENUM",
                    "deviceOS": "QNX",
                    "headUnitType": "",
                    "manufacturerName": "",
                    "region": "NAFTA",
                    "screenSize": "Five",
                    "tbmSerialNum": "",
                    "tbmPartNum": "",
                    "tbmHardwareVersion": "",
                    "tbmSoftwareVersion": "",
                    "simIccid": "89011704272514889067",
                    "simImsi": "",
                    "simMsisdn": "12482026960",
                    "nadImei": "860871040000484",
                    "nadHardwareVersion": "",
                    "nadSoftwareVersion": "",
                    "nadSerialNum": "",
                    "nadPartNum": "",
                    "wifiMac": "",
                    "huSerialNum": "",
                    "huPartNum": "",
                    "huHardwareVersion": "",
                    "huSoftwareVersion": "",
                    "isHUNavigationPresent": False,
                },
                "distanceRemainingForNextService": 0,
                "errorTellTale": None,
                "fuelRemaining": 0.0,
                "stateofCharge": 0.0,
                "tirePressure": None,
                "vehicleInfo": {
                    "vehicleLocation": {
                        "positionLatitude": 42.6812744140625,
                        "positionLongitude": -83.21455383300781,
                        "estimatedPositionError": 0,
                        "positionAltitude": 0.0,
                        "gpsFixTypeEnum": "ID_FIX_NO_POS",
                        "isGPSFixNotAvailable": False,
                        "estimatedAltitudeError": 0,
                        "positionDirection": 0.0,
                    },
                    "vehicleSpeed": 0.0,
                    "odometer": 0,
                    "engineStatusEnum": "RUN",
                    "language": "en_US",
                    "country": "US",
                    "vehicleType": "PASSENGER_CLASSM1",
                    "vin": "1C4RJKBG4M81030HT",
                    "brand": "JEEP",
                    "model": "",
                    "year": "",
                },
            },
        },
    }


def generate_valid_roadside_assist_jeep_vehicle_data():
    return {
        "EventID": "BcallData",
        "Version": "1.0",
        "Timestamp": 1607067376879,
        "Data": {
            "callCenterNumber": "+18449232963",
            "bcallType": "ROADSIDE_ASSIST",
            "callTrigger": "MANUAL",
            "callReason": "DEFAULT",
            "language": "English",
            "latitude": 42.6812744140625,
            "longitude": -83.21455383300781,
            "fuelRemaining": 11.636523,
            "engineStatus": "CUSTOM_EXTENSION",
            "customExtension": {
                "vehicleDataUpload": {
                    "callCenterNumber": "+18449232963",
                    "CallReasonEnum": "DEFAULT",
                    "callTriggerEnum": "MANUAL",
                    "calltype": "ASSIST3",
                    "daysRemainingForNextService": 0,
                    "device": {
                        "deviceType": "ENUM",
                        "deviceOS": "QNX",
                        "headUnitType": "",
                        "manufacturerName": "",
                        "region": "NAFTA",
                        "screenSize": "Five",
                        "tbmSerialNum": "",
                        "tbmPartNum": "",
                        "tbmHardwareVersion": "",
                        "tbmSoftwareVersion": "",
                        "simIccid": "698987456963",
                        "simImsi": "",
                        "simMsisdn": "9999954321",
                        "nadImei": "84977388935689",
                        "nadHardwareVersion": "",
                        "nadSoftwareVersion": "",
                        "nadSerialNum": "",
                        "nadPartNum": "",
                        "wifiMac": "",
                        "huSerialNum": "",
                        "huPartNum": "",
                        "huHardwareVersion": "",
                        "huSoftwareVersion": "",
                        "isHUNavigationPresent": False,
                    },
                    "distanceRemainingForNextService": 38057,
                    "errorTellTale": {"isOilPressure": True},
                    "fuelRemaining": 11.636523,
                    "stateofCharge": 66.69174194335938,
                    "tirePressure": {
                        "flTirePressure": 17.227015,
                        "flTireSts": "NORMAL",
                        "frTirePressure": 16.568317,
                        "frTireSts": "NORMAL",
                        "rlTirePressure": 39.452736,
                        "rlTireSts": "NORMAL",
                        "rrTirePressure": 30.417278,
                        "rrTireSts": "NORMAL",
                        "rl2TirePressure": 0.0,
                        "rr2TirePressure": 0.0,
                    },
                    "vehicleInfo": {
                        "vehicleLocation": {
                            "positionLatitude": 42.6812744140625,
                            "positionLongitude": -83.21455383300781,
                            "estimatedPositionError": 0,
                            "positionAltitude": 0.0,
                            "gpsFixTypeEnum": "ID_FIX_NO_POS",
                            "isGPSFixNotAvailable": False,
                            "estimatedAltitudeError": 0,
                            "positionDirection": 0.0,
                        },
                        "vehicleSpeed": 0.0,
                        "odometer": 0,
                        "engineStatusEnum": "REQUESTSTART",
                        "language": "English",
                        "country": "GB",
                        "vehicleType": "PASSENGER_CLASSM1",
                        "vin": "3D7KA28CX4G228689",
                        "brand": "JEEP",
                        "model": "",
                        "year": "",
                    },
                }
            },
        },
    }


def test_populate_vehicledata_for_jeep_with_valid_brand_assist_data_populate_as_expected(
    setup_fca_service,
):
    fca_jeep_json = generate_valid_brand_assist_jeep_vehicle_data()
    vehicledata = setup_fca_service.populate_vehicledata(
        "12482026960", "fca", fca_jeep_json
    )
    assert vehicledata.EventID == fca_jeep_json["EventID"]
    assert vehicledata.Data.bcallType == fca_jeep_json["Data"]["bcallType"]
    assert (
        vehicledata.Data.customExtension.device
        == fca_jeep_json["Data"]["customExtension"]["device"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleInfo
        == fca_jeep_json["Data"]["customExtension"]["vehicleInfo"]
    )


def test_populate_vehicledata_for_jeep_with_valid_roadside_assist_data_populate_as_expected(
    setup_fca_service,
):
    fca_jeep_roadside_assist_json = generate_valid_roadside_assist_jeep_vehicle_data()
    vehicledata = setup_fca_service.populate_vehicledata(
        "9999954321", "fca", fca_jeep_roadside_assist_json
    )
    assert vehicledata.EventID == fca_jeep_roadside_assist_json["EventID"]
    assert (
        vehicledata.Data.bcallType == fca_jeep_roadside_assist_json["Data"]["bcallType"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleDataUpload.device
        == fca_jeep_roadside_assist_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["device"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleDataUpload.vehicleInfo
        == fca_jeep_roadside_assist_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["vehicleInfo"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleDataUpload.errorTellTale.isOilPressure
        == fca_jeep_roadside_assist_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["errorTellTale"]["isOilPressure"]
    )
    assert (
        vehicledata.Data.customExtension.vehicleDataUpload.tirePressure.flTirePressure
        == fca_jeep_roadside_assist_json["Data"]["customExtension"][
            "vehicleDataUpload"
        ]["tirePressure"]["flTirePressure"]
    )


@pytest.mark.parametrize(
    "invaliddata,expected",
    [(None, None), ("", None), ({"invalid": "invalid"}, None)],
    ids=[None, "Empty", "Invalidjson"],
)
def test_populate_vehicledata_with_invalid_data_works_as_expected(
    setup_fca_service, invaliddata, expected
):
    vehicledata = setup_fca_service.populate_vehicledata(
        "12345678901", "fca", invaliddata
    )
    assert vehicledata == expected


# private method UTs


def test_fca_service_retrial_request_bcall_get_vehicledata_on_success_should_return_dataresponse_status_success(
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
    patched_rest_client,
):
    mock_dynamo_cv_table.query.return_value = generate_valid_fca_data_singlelist()
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = FcaService(
        config=FcaConfig(
            base_url="https://successjson",
            max_ani_length=11,
            bcall_data_url="/a",
            max_retries=3,
            delay_for_each_retry=1,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    response, validresponsejson, dataresponse = retrial_request_bcall_get_vehicledata(
        fcaservice,
        msisdn="12345678901",
        programcode="fca",
        payload={"msisdn": "12345678901"},
        action="GetVehicleDataTEST",
    )
    responsejson = response.json()
    assert responsejson == successjson
    assert type(dataresponse) == VehicleData
    assert validresponsejson is True
    assert dataresponse.status == InternalStatusType.SUCCESS


def test_fca_service_retrial_request_bcall_get_vehicledata_on_success_should_return_dataresponse_as_none(
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
    patched_rest_client,
):
    mock_dynamo_cv_table.query.return_value = None
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = FcaService(
        config=FcaConfig(
            base_url="https://successjson",
            max_ani_length=11,
            bcall_data_url="/a",
            max_retries=3,
            delay_for_each_retry=1,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    response, validresponsejson, dataresponse = retrial_request_bcall_get_vehicledata(
        fcaservice,
        msisdn="12345678901",
        programcode="fca",
        payload={"msisdn": "12345678901"},
        action="GetVehicleDataTEST",
    )
    responsejson = response.json()
    assert responsejson == successjson
    assert validresponsejson is True
    assert dataresponse is None


def test_fca_service_request_bcall_data_on_success_should_return_200_or_202(
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
    patched_rest_client,
):
    patched_rest_client.post.side_effect = mocked_requests_post
    fcaservice = FcaService(
        config=FcaConfig(
            base_url="https://successjson",
            max_ani_length=11,
            bcall_data_url="/a",
            max_retries=3,
            delay_for_each_retry=1,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    response = request_bcall_data(
        fcaservice,
        msisdn="12345678901",
        programcode="fca",
        payload={"msisdn": "12345678901"},
        action="GetVehicleDataTEST",
    )
    assert response.status_code == 202


def test_fca_service_get_vehicledata_response_on_success_should_return_valid_db_dataresponse(
    mock_dynamo_cv_table, setup_fca_service
):
    mock_dynamo_cv_table.query.return_value = generate_valid_fca_data_singlelist()
    dataresponse = get_vehicledata_response(
        setup_fca_service, msisdn="12345678901", programcode="fca"
    )
    assert type(dataresponse) == ConnectedVehicleTable


def test_fca_service_get_vehicledata_response_on_no_data_found_should_return_dataresponse_as_none(
    mock_dynamo_cv_table, setup_fca_service
):
    mock_dynamo_cv_table.query.return_value = None
    dataresponse = get_vehicledata_response(
        setup_fca_service, msisdn="12345678901", programcode="fca"
    )
    assert dataresponse is None


def test_fca_service_create_vehicledata_response_on_valid_input_response_should_return_valid_db_dataresponse():
    dataresponse = create_vehicledata_response(
        response=generate_valid_fca_cv_data(),
        msisdn="12345678901",
        programcode="fca",
        responsestatus=InternalStatusType.SUCCESS,
        responsemessage="Successfully retrieved",
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS


def test_fca_service_create_vehicledata_response_on_input_response_none_should_return_dataresponse_as_none():
    dataresponse = create_vehicledata_response(
        response=None,
        msisdn="12345678901",
        programcode="fca",
        responsestatus=InternalStatusType.NOTFOUND,
        responsemessage="No data is available for msisdn: 12345678901",
    )
    assert dataresponse is None


# Not implemented abstract method tests
def test_fca_serivce_on_calling_assign_agent_raise_notimplementedexception(
    setup_fca_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_fca_service.assign_agent(any)
    assert execinfo.type == NotImplementedError


def test_fca_serivce_on_calling_health_raise_notimplementedexception(
    setup_fca_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_fca_service.health(ProgramCode.FCA, CtsVersion.ONE_DOT_ZERO)
    assert execinfo.type == NotImplementedError


def generate_valid_fca_cv_data():
    return ConnectedVehicleTable(
        request_key="fca-TESTMSISDN",
        msisdn="TESTMSISDN",
        programcode="fca",
        event_datetime=int(
            datetime.timestamp(datetime.utcnow()) * 1000
        ),  # 1597783540014,
        timestamp=datetime.now(),
        vin="TESTFIRSTVIN",
        brand="vw",
        modelname="Passat",
        modelyear="2008",
        modelcode="A342P6",
        modeldesc="Passat_2008",
        odometer=0,
        odometerscale="Miles",
        latitude="37.532918",
        longitude="-122.272576",
        headingdirection="NORTH EAST",
        countrycode="US",
    )


def generate_valid_fca_data_singlelist():
    data1 = generate_valid_fca_cv_data()
    datalist = [data1]
    return datalist

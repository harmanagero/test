from decimal import Decimal
from unittest.mock import patch

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
from src.config.dynamo_config import DynamoConfig
from src.config.siriusxm_config import SiriusXmConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.dynamodb_tables import get_main_table
from src.siriusxm.models.data.vehicle_data import VehicleData
from src.siriusxm.models.domain.agentassignment import AgentAssignment
from src.siriusxm.models.domain.terminate import Terminate
from src.siriusxm.services.siriusxm_service import SiriusXmService

RAWAPIKEY = "fooRawAPIKEY"
APIKEY = "fooAPIKEY"
URL = "fooURL"
TABLE_NAME = "cv-table"


@pytest.fixture
def setup_siriusxm_service(mock_logger, mock_dynamo_cv_table):
    config = SiriusXmConfig(base_url=URL, api_key=APIKEY, raw_apikey=RAWAPIKEY)
    uut = SiriusXmService(config=config, table=mock_dynamo_cv_table)
    yield uut


@pytest.fixture
def patched_zeep_client():
    with patch(
        "src.siriusxm.services.siriusxm_service.retrieve_zeepclient"
    ) as patched_zeep_client:
        yield patched_zeep_client


@pytest.fixture
def patched_setup_logger():
    with patch("src.siriusxm.services.siriusxm_service.logger") as mocked_setup:
        yield mocked_setup


@pytest.fixture
def patched_rest_client():
    with patch(
        "src.siriusxm.services.siriusxm_service.requests"
    ) as patched_rest_client:
        yield patched_rest_client


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, response_text, status_code):
            self.status_code = status_code
            self.headers = {"content-type": "text/xml;charset=UTF-8"}
            self.text = response_text

    if "success" in args[0]:
        return MockResponse("<xml></xml>", 200)
    elif "badrequest" in args[0]:
        return MockResponse("Bad_Request", 400)
    elif "notfound" in args[0]:
        return MockResponse("File Not Found", 404)
    elif "content_notsupported" in args[0]:
        mock = MockResponse("b'Server Error", 500)
        mock.headers = {"content-type": "text/plain"}
        mock.reason = "Internal Server Error"
        mock.text = "Server Error"
        return mock

    return MockResponse("Error 500", 500)


mockStatusTestData = [
    ("iLlEgAl_ArGuMeNt_ErRoR", InternalStatusType.NOTFOUND),
    ("rEfErEnCe_Id_NoT_fOuNd", InternalStatusType.NOTFOUND),
    ("InVaLiD_sTaTe_ErRoR", InternalStatusType.FORBIDDEN),
    ("InTeRnAl_SeRvEr_ErRoR", InternalStatusType.INTERNALSERVERERROR),
    ("bAd_ReQuEsT", InternalStatusType.BADREQUEST),
    ("ErRoR", InternalStatusType.ERROR),
    ("cAnCeLlEd", InternalStatusType.CANCELED),
    ("fIlE nOt FoUnD", InternalStatusType.NOTFOUND),
    ("SoMeThIng", InternalStatusType.INTERNALSERVERERROR),
]

mockServiceErrorTestData = [
    ("No reference id found", InternalStatusType.NOTFOUND),
    (" ", InternalStatusType.INTERNALSERVERERROR),
]

mockResponseTestData = [
    ({"result-code": "NO_ERROR", "result-msg": ""}),
    ({"reference-id": "someid", "result-msg": "some msg"}),
    ({"reference-id": "someid", "result-code": "NO_ERROR"}),
    (None),
    ({}),
    (
        {
            "reference-id": "",
            "result-code": "INTERNAL_SERVER_ERROR",
            "result-msg": "somemsg",
        }
    ),
    ({"reference-id": "some id", "result-code": "", "result-msg": "somemsg"}),
    ({"reference-id": "some id", "result-code": None, "result-msg": "somemsg"}),
    ({"reference-id": "some id", "result-code": "", "result-msg": None}),
]


mockvalidCVTestData = [
    (
        {
            "request_key": "infiniti-TESTREFERENCE",
            "programcode": "infiniti",
            "language": "en",
            "referenceid": "TESTREFERENCE",
            "geolocation": "42.406~-71.0742~400;enc-param=token",
            "vin": "TESTVIN",
        }
    ),
    (
        {
            "request_key": "nissan-TESTREFERENCE",
            "programcode": "nissan",
            "language": "en",
            "referenceid": "TESTREFERENCE",
            "geolocation": "42.406~-71.0742~400;enc-param=token",
            "vin": "SECONDTESTVIN",
        }
    ),
    (
        {
            "request_key": "toyota-TESTREFERENCE",
            "programcode": "toyota",
            "language": "en",
            "referenceid": "TESTREFERENCE",
            "geolocation": "42.406~-71.0742~400;enc-param=token",
            "vin": "THIRDTESTVIN",
        }
    ),
]


mockInvalidCVTestData = [(None, None), ("", None)]


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "resultcode, expected",
    mockStatusTestData,
    ids=[
        "IllegalArgumentError",
        "ReferenceIdNotFound",
        "InvalidStateError",
        "InternalServerError",
        "BadRequest",
        "Error",
        "Cancelled",
        "FileNotFound",
        "UnknownResultCode",
    ],
)
def test_service_assign_agent_on_different_error_status_should_return_false_and_expected_error(
    setup_siriusxm_service, patched_zeep_client, programcode, resultcode, expected
):
    patched_zeep_client().service.agentAssigned.return_value = {
        "reference-id": "referenceid",
        "result-code": resultcode,
        "result-msg": "",
    }
    agentassignment = AgentAssignment(
        referenceid="TEST", isassigned=True, programcode=programcode
    )
    serviceresponse = setup_siriusxm_service.assign_agent(agentassignment)
    assert not serviceresponse
    assert agentassignment.responsestatus == expected
    assert agentassignment.response_referenceid == "referenceid"
    assert agentassignment.responsemessage == ""


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "resultmessage, expected",
    mockServiceErrorTestData,
    ids=["NotFoundError", "InternalServerError"],
)
def test_service_assign_agent_on_serviceerror_status_should_return_false_and_expected_error(
    setup_siriusxm_service, patched_zeep_client, programcode, resultmessage, expected
):
    patched_zeep_client().service.agentAssigned.return_value = {
        "reference-id": "referenceid",
        "result-code": "SERVICE_ERROR",
        "result-msg": resultmessage,
    }
    agentassignment = AgentAssignment(
        referenceid="TEST", isassigned=True, programcode=programcode
    )
    serviceresponse = setup_siriusxm_service.assign_agent(agentassignment)
    assert not serviceresponse
    assert agentassignment.responsestatus == expected
    assert agentassignment.response_referenceid == "referenceid"
    assert agentassignment.responsemessage == resultmessage


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_assign_agent_on_exception_should_return_false(
    setup_siriusxm_service, patched_zeep_client, programcode
):
    patched_zeep_client().service.agentAssigned.side_effect = Exception
    agentassignment = AgentAssignment(
        referenceid="TEST", isassigned=True, programcode=programcode
    )
    serviceresponse = setup_siriusxm_service.assign_agent(agentassignment)
    assert serviceresponse is False
    assert type(agentassignment.responsemessage) is Exception


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "mockResponseTestData",
    mockResponseTestData,
    ids=[
        "ResponseReferenceIdMissing",
        "ResultCodeMissing",
        "ResultMessageMissing",
        "ResponseNone",
        "ResponseEmpty",
        "ReferenceIdEmpty",
        "ResultCodeEmpty",
        "ResutCodeNone",
        "ResultMessageNone",
    ],
)
def test_service_assign_agent_on_any_response_node_missing_or_empty_should_return_false(
    setup_siriusxm_service, patched_zeep_client, mockResponseTestData, programcode
):
    patched_zeep_client().service.agentAssigned.return_value = mockResponseTestData
    agentassignment = AgentAssignment(
        referenceid="TEST", isassigned=True, programcode=programcode
    )
    serviceresponse = setup_siriusxm_service.assign_agent(agentassignment)
    assert serviceresponse is False


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_assign_agent_on_success_resultmessage_is_empty_should_return_true(
    setup_siriusxm_service, patched_zeep_client, programcode
):
    patched_zeep_client().service.agentAssigned.return_value = {
        "reference-id": "some id",
        "result-code": "NO_ERROR",
        "result-msg": "",
    }
    agentassignment = AgentAssignment(
        referenceid="TEST", isassigned=True, programcode=programcode
    )
    serviceresponse = setup_siriusxm_service.assign_agent(agentassignment)
    assert serviceresponse is True


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_assign_agent_on_success_should_return_true(
    setup_siriusxm_service, patched_zeep_client, programcode
):
    patched_zeep_client().service.agentAssigned.return_value = {
        "reference-id": "TEST",
        "result-code": "NO_ERROR",
        "result-msg": "Service Successful",
    }
    agentassignment = AgentAssignment(
        referenceid="TEST", isassigned=True, programcode=programcode
    )
    serviceresponse = setup_siriusxm_service.assign_agent(agentassignment)
    assert serviceresponse is True


def test_service_assign_agent_should_raise_exception_when_programcode_is_not_passed(
    setup_siriusxm_service,
):
    try:
        agentassignment = AgentAssignment(referenceid="TEST", isassigned=True)
        setup_siriusxm_service.assign_agent(agentassignment)
    except BaseException as e:
        assert e.raw_errors[0].exc.msg_template == "field required"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_assign_agent_should_raise_exception_when_referenceid_is_not_passed(
    setup_siriusxm_service, programcode
):
    try:
        agentassignment = AgentAssignment(programcode=programcode, isassigned=True)
        setup_siriusxm_service.assign_agent(agentassignment)
    except BaseException as e:
        assert e.raw_errors[0].exc.msg_template == "field required"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_assign_agent_should_raise_exception_when_isassigned_is_not_passed(
    setup_siriusxm_service, programcode
):
    try:
        agentassignment = AgentAssignment(programcode=programcode, referenceid="TEST")
        setup_siriusxm_service.assign_agent(agentassignment)
    except BaseException as e:
        assert e.raw_errors[0].exc.msg_template == "field required"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_terminate_on_success_should_return_true(
    setup_siriusxm_service, patched_zeep_client, programcode
):
    patched_zeep_client().service.terminate.return_value = {
        "reference-id": "referenceid",
        "result-code": "nO_eRrOr",
        "result-msg": "",
    }

    terminate = Terminate(referenceid="TEST", programcode=programcode)

    response = setup_siriusxm_service.terminate(terminate)
    assert response
    assert terminate.status == InternalStatusType.SUCCESS
    assert terminate.response_referenceid == "referenceid"
    assert terminate.responsemessage == ""


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "resultcode, expected",
    mockStatusTestData,
    ids=[
        "IllegalArgumentError",
        "ReferenceIdNotFound",
        "InvalidStateError",
        "InternalServerError",
        "BadRequest",
        "Error",
        "Cancelled",
        "FileNotFound",
        "UnknownResultCode",
    ],
)
def test_service_terminate_on_different_error_status_should_return_false_and_expected_error(
    setup_siriusxm_service, patched_zeep_client, programcode, resultcode, expected
):
    patched_zeep_client().service.terminate.return_value = {
        "reference-id": "referenceid",
        "result-code": resultcode,
        "result-msg": "",
    }

    terminate = Terminate(referenceid="TEST", programcode=programcode)

    response = setup_siriusxm_service.terminate(terminate)
    assert not response
    assert terminate.status == expected
    assert terminate.response_referenceid == "referenceid"
    assert terminate.responsemessage == ""


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_terminate_on_exception_should_return_false(
    setup_siriusxm_service, patched_zeep_client, programcode
):
    patched_zeep_client().service.terminate.side_effect = Exception
    terminate = Terminate(referenceid="TEST", programcode=programcode)

    response = setup_siriusxm_service.terminate(terminate)
    assert not response
    assert type(terminate.responsemessage) is Exception


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "mockResponseTestData",
    mockResponseTestData,
    ids=[
        "ResponseReferenceIdMissing",
        "ResultCodeMissing",
        "ResultMessageMissing",
        "ResponseNone",
        "ResponseEmpty",
        "ReferenceIdEmpty",
        "ResultCodeEmpty",
        "ResutCodeNone",
        "ResultMessageNone",
    ],
)
def test_service_terminate_on_any_response_node_missing_or_empty_should_return_false(
    setup_siriusxm_service, patched_zeep_client, mockResponseTestData, programcode
):
    patched_zeep_client().service.terminate.return_value = mockResponseTestData
    terminate = Terminate(referenceid="TEST", programcode=programcode)

    response = setup_siriusxm_service.terminate(terminate)
    assert not response


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_terminate_on_success_resultmessage_is_empty_should_return_true(
    setup_siriusxm_service, patched_zeep_client, programcode
):
    patched_zeep_client().service.terminate.return_value = {
        "reference-id": "some id",
        "result-code": "NO_ERROR",
        "result-msg": "",
    }
    terminate = Terminate(referenceid="TEST", programcode=programcode)

    response = setup_siriusxm_service.terminate(terminate)
    assert response


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_terminate_reasoncode_is_optional_and_should_return_as_expected(
    setup_siriusxm_service, programcode, patched_zeep_client
):
    patched_zeep_client().service.terminate.return_value = {
        "reference-id": "some id",
        "result-code": "NO_ERROR",
        "result-msg": "",
    }

    terminate = Terminate(referenceid="123456", programcode=programcode)

    response = setup_siriusxm_service.terminate(terminate)
    assert response


def test_service_terminate_on_programcode_is_not_passed_should_raise_exception(
    setup_siriusxm_service,
):
    try:
        terminate = Terminate(referenceid="TEST", reasoncode="")

        setup_siriusxm_service.terminate(terminate)
    except BaseException as e:
        assert e.raw_errors[0].exc.msg_template == "field required"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_service_terminate_on_referenceid_is_not_passed_should_raise_exception(
    setup_siriusxm_service, programcode
):
    try:
        terminate = Terminate(programcode=programcode, reasoncode="")

        setup_siriusxm_service.terminate(terminate)
    except BaseException as e:
        assert e.raw_errors[0].exc.msg_template == "field required"


TABLE_NAME = "local-cv"


@pytest.fixture
def mock_dynamodb():
    with mock_dynamodb2() as mock:
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            AttributeDefinitions=[
                {"AttributeName": "request_key", "AttributeType": "S"},
                {"AttributeName": "event_datetime", "AttributeType": "N"},
                {"AttributeName": "programcode", "AttributeType": "S"},
                {"AttributeName": "referenceid", "AttributeType": "S"},
                {"AttributeName": "ani", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "request_key", "KeyType": "HASH"},
                {"AttributeName": "event_datetime", "KeyType": "RANGE"},
            ],
            TableName=TABLE_NAME,
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi-data-index",
                    "KeySchema": [
                        {"AttributeName": "programcode", "KeyType": "HASH"},
                        {"AttributeName": "event_datetime", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                },
                {
                    "IndexName": "gsi-ani-index",
                    "KeySchema": [
                        {"AttributeName": "ani", "KeyType": "HASH"},
                        {"AttributeName": "event_datetime", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                },
                {
                    "IndexName": "gsi-referenceid-index",
                    "KeySchema": [
                        {"AttributeName": "referenceid", "KeyType": "HASH"},
                        {"AttributeName": "event_datetime", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                },
            ],
        )
        yield mock


def test_save_vehicledata_returns_true_if_successful(
    mock_dynamodb, setup_siriusxm_service, mock_logger
):
    cv_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    config = SiriusXmConfig(base_url=URL, api_key=APIKEY, raw_apikey=RAWAPIKEY)
    uut = SiriusXmService(config=config, table=cv_table)
    cv = generate_valid_cv_data()
    assert uut.save_vehicledata(cv)
    conn = boto3.resource("dynamodb", region_name="us-east-1")
    table = conn.Table(TABLE_NAME)
    item = table.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("infiniti-TESTREFERENCE"),
    )

    assert item["Items"][0]["latitude"] == Decimal("42.406")
    assert item["Items"][0]["vin"] == cv["vin"]


def test_save_vehicledata_returns_false_if_unsuccessful(
    mock_dynamo_cv_table, setup_siriusxm_service
):
    exception = Exception("foo")
    mock_dynamo_cv_table.side_effect = exception
    cv = generate_valid_cv_data()
    val = setup_siriusxm_service.save_vehicledata(cv)
    assert val.status == InternalStatusType.INTERNALSERVERERROR


def test_get_vehicledata_returns_200_if_successful(
    mock_dynamo_cv_table, mock_dynamodb, setup_siriusxm_service, mock_logger
):
    cv_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    config = SiriusXmConfig(base_url=URL, api_key=APIKEY, raw_apikey=RAWAPIKEY)
    uut = SiriusXmService(config=config, table=cv_table)
    uut.save_vehicledata(generate_valid_cv_data())
    response = uut.get_vehicledata(id="TESTREFERENCE", programcode="infiniti")
    assert type(response) == VehicleData
    assert response.calldate == response.timestamp.strftime("%Y-%m-%d")
    assert response.calltime == response.timestamp.strftime("%H:%M")
    assert response.status == InternalStatusType.SUCCESS
    assert response.referenceid == "TESTREFERENCE"
    assert response.programcode == "infiniti"


def test_get_vehicledata_returns_200_with_latest_record_if_successful(
    mock_dynamo_cv_table, mock_dynamodb, setup_siriusxm_service, mock_logger
):
    cv_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    config = SiriusXmConfig(base_url=URL, api_key=APIKEY, raw_apikey=RAWAPIKEY)
    uut = SiriusXmService(config=config, table=cv_table)
    uut.save_vehicledata(generate_valid_cv_data())
    uut.save_vehicledata(generate_secondvalid_cv_data())
    response = uut.get_vehicledata(id="TESTREFERENCE", programcode="infiniti")
    assert type(response) == VehicleData
    assert response.calldate == response.timestamp.strftime("%Y-%m-%d")
    assert response.calltime == response.timestamp.strftime("%H:%M")
    assert response.status == InternalStatusType.SUCCESS
    assert response.referenceid == "TESTREFERENCE"
    assert response.programcode == "infiniti"
    assert response.vin == "TESTSECONDVIN"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_get_vehicledata_returns_500_if_unsuccessful(
    mock_dynamo_cv_table,
    mock_dynamodb,
    setup_siriusxm_service,
    patched_setup_logger,
    programcode,
):
    patched_setup_logger.info.side_effect = Exception
    cv_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    config = SiriusXmConfig(base_url=URL, api_key=APIKEY, raw_apikey=RAWAPIKEY)
    uut = SiriusXmService(config=config, table=cv_table)
    response = uut.get_vehicledata(id="TESTREFERENCE", programcode=programcode)
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_get_vehicledata_returns_404_if_recordnotfound(
    mock_dynamo_cv_table, setup_siriusxm_service, programcode
):
    response = setup_siriusxm_service.get_vehicledata(
        id="NORECORD", programcode=programcode
    )
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.NOTFOUND
    assert response.responsemessage == "No data found"


def generate_valid_cv_data():
    return {
        "request_key": "infiniti-TESTREFERENCE",
        "programcode": "infiniti",
        "language": "en",
        "referenceid": "TESTREFERENCE",
        "geolocation": "42.406~-71.0742~400;enc-param=token",
        "vin": "TESTVIN",
    }


def generate_secondvalid_cv_data():
    return {
        "request_key": "infiniti-TESTREFERENCE",
        "programcode": "infiniti",
        "language": "en",
        "referenceid": "TESTREFERENCE",
        "geolocation": "42.406~-71.0742~400;enc-param=token",
        "vin": "TESTSECONDVIN",
    }


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "mockvalidCVTestData", mockvalidCVTestData, ids=["Nissan", "Infiniti", "Toyota"]
)
def test_populate_vehicledata_with_valid_data_populate_as_expected(
    setup_siriusxm_service, mockvalidCVTestData, programcode
):
    data = setup_siriusxm_service.populate_vehicledata(mockvalidCVTestData)
    assert data.referenceid == mockvalidCVTestData["referenceid"]
    assert data.language == mockvalidCVTestData["language"]
    assert data.programcode == mockvalidCVTestData["programcode"]
    assert data.latitude == mockvalidCVTestData["geolocation"].split("~")[0]
    assert data.vin == mockvalidCVTestData["vin"]


@pytest.mark.parametrize(
    "invaliddata,expected", mockInvalidCVTestData, ids=["Nissan", "Infiniti"]
)
def test_populate_vehicledata_with_invalid_data_populate_as_expected(
    setup_siriusxm_service, invaliddata, expected
):
    actual_exception = setup_siriusxm_service.populate_vehicledata(invaliddata)
    assert actual_exception == expected


@pytest.mark.parametrize(
    "programcode",
    [ProgramCode.NISSAN, ProgramCode.INFINITI],
    ids=["Nissan", "Infiniti"],
)
def test_siriusxm_serivce_health_on_success_returns_200(
    programcode, patched_rest_client, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = mocked_requests_get
    siriusxmservice = SiriusXmService(
        config=SiriusXmConfig(base_url="https://success"),
        table=mock_dynamo_cv_table,
    )
    response = siriusxmservice.health(programcode, CtsVersion.TWO_DOT_ZERO)
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.SUCCESS
    assert response.responsemessage == "HealthCheck passed"


@pytest.mark.parametrize(
    "programcode",
    [ProgramCode.NISSAN, ProgramCode.INFINITI],
    ids=["Nissan", "Infiniti"],
)
def test_siriusxm_serivce_health_on_exception_returns_500(
    patched_rest_client, mock_dynamo_cv_table, programcode
):
    patched_rest_client.get.side_effect = Exception
    siriusxm_service = SiriusXmService(
        config=SiriusXmConfig(base_url="https://success"),
        table=mock_dynamo_cv_table,
    )
    response = siriusxm_service.health(programcode, CtsVersion.TWO_DOT_ZERO)
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR


@pytest.mark.parametrize(
    "programcode",
    [ProgramCode.NISSAN, ProgramCode.INFINITI],
    ids=["Nissan", "Infiniti"],
)
@pytest.mark.parametrize(
    "base_url, status, message",
    [
        ("https://badrequest", InternalStatusType.BADREQUEST, "Bad_Request"),
        ("https://notfound", InternalStatusType.NOTFOUND, "File Not Found"),
        ("https://content_notsupported", InternalStatusType.INTERNALSERVERERROR, "Server Error"),
        ("https://invalid", InternalStatusType.INTERNALSERVERERROR, "Error 500"),
    ],
)
def test_siriusxm_serivce_health_on_error_returns_expected_response(
    programcode,
    patched_rest_client,
    mock_dynamo_cv_table,
    base_url,
    status,
    message,
):
    patched_rest_client.get.side_effect = mocked_requests_get
    siriusxmservice = SiriusXmService(
        config=SiriusXmConfig(base_url=base_url),
        table=mock_dynamo_cv_table,
    )
    response = siriusxmservice.health(programcode, CtsVersion.TWO_DOT_ZERO)
    assert type(response) == VehicleData
    assert response.status == status
    assert response.responsemessage == message

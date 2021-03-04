from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
from src.aeris.models.domain.vehicle_data import VehicleData
from src.aeris.services.aeris_service import (
    AerisService,
    get_data_from_database,
    create_vehicledata_response,
)
from src.config.aeris_config import AerisConfig
from src.config.dynamo_config import DynamoConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.odometerscale_type import OdometerScaleType
from src.models.enums.programcode_type import ProgramCode
from src.services.dynamodb_tables import ConnectedVehicleTable, get_main_table

BASE_URL = "fooBaseURL"
ROOT_CERT = "fooCERT"
DYNAMO_TABLE_NAME = "cv-table"
DYNAMODB_CHECK_ENABLE = False
DYNAMODB_CHECK_TIMELIMIT = 2


@pytest.fixture
def setup_aeris_service(mock_logger, mock_dynamo_cv_table):
    uut = AerisService(
        config=AerisConfig(
            base_url=BASE_URL,
            root_cert=ROOT_CERT,
            dynamo_table_name=DYNAMO_TABLE_NAME,
            dynamodb_check_enable=DYNAMODB_CHECK_ENABLE,
            dynamodb_check_timelimit=DYNAMODB_CHECK_TIMELIMIT,
        ),
        table=mock_dynamo_cv_table,
    )
    yield uut


@pytest.fixture
def patched_rest_client():
    with patch("src.aeris.services.aeris_service.requests") as patched_rest_client:
        yield patched_rest_client


successjson = {
    "data": {
        "callDate": "2020-09-25",
        "activationType": 0,
        "callTime": "19:05",
        "vehicle": {
            "vin": "1VWSA7A3XLC011823",
            "brand": "VW",
            "modelName": "Passat",
            "modelYear": "2020",
            "modelCode": "A342P6",
            "modelDesc": "Passat_2020",
            "ocuSim": {"market": "nar-us"},
        },
        "odometer": 16114,
        "odometerScale": 0,
        "location": {
            "latitude": 37.532918,
            "longitude": -122.272576,
            "headingDirection": "NORTH EAST",
        },
    }
}

notfoundjson = {
    "error": {
        "errorCode": "MSISDN_NOT_FOUND",
        "timestamp": 1603453955454,
        "errorDescription": "Unknown Error Situation",
        "requestId": "26ed2578-e2bc-43be-a3da-c6d094b58db8",
        "origin": "VehicleDataService",
        "status": "NOT_FOUND",
        "path": "/csvds",
        "reason": "Unknown Error Situation",
    }
}

badrequestjson = {
    "error": {
        "errorCode": "MSISDN_LENGTH_WRONG",
        "timestamp": 1603454176736,
        "errorDescription": "MSISDN should atleast be 10 digits",
        "requestId": "5a7b4596-4404-4433-a91d-5694e92c248a",
        "origin": "VehicleDataService",
        "status": "BAD_REQUEST",
        "path": "/csvds",
        "reason": "Internal Service validation failure",
    }
}

successmissingparentjson = {
    "callDate": "2020-09-25",
    "activationType": 0,
    "callTime": "19:05",
    "vehicle": {
        "vin": "1VWSA7A3XLC011823",
        "brand": "VW",
        "modelName": "Passat",
        "modelYear": "2020",
        "modelCode": "A342P6",
        "modelDesc": "Passat_2020",
        "ocuSim": {"market": "nar-us"},
    },
    "odometer": 16114,
    "odometerScale": 1,
    "location": {
        "latitude": 37.532918,
        "longitude": -122.272576,
        "headingDirection": "NORTH EAST",
    },
}

badrequestmissingparentnodejson = {
    "errorCode": "MSISDN_LENGTH_WRONG",
    "timestamp": 1603454176736,
    "errorDescription": "MSISDN should atleast be 10 digits",
    "requestId": "5a7b4596-4404-4433-a91d-5694e92c248a",
    "origin": "VehicleDataService",
    "status": "BAD_REQUEST",
    "path": "/csvds",
    "reason": "Internal Service validation failure",
}


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, text="", reason=""):
            self.json_data = json_data
            self.status_code = status_code
            self.headers = {"content-type": "application/json;charset=UTF-8"}
            self.text = text
            self.reason = reason

        def json(self):
            return self.json_data

    if "successjson" in args[0]:
        return MockResponse(successjson, 200)
    elif "badrequestjson" in args[0]:
        return MockResponse(badrequestjson, 400)
    elif "datanode_missing" in args[0]:
        return MockResponse(successmissingparentjson, 200)
    elif "errornode_missing" in args[0]:
        return MockResponse(badrequestmissingparentnodejson, 400)
    elif "content_notsupported" in args[0]:
        mock = MockResponse("b'Server Error", 500, "Content not supported")
        mock.headers = {"content-type": "text/plain"}
        return mock
    elif "server_error" in args[0]:
        mock = MockResponse(
            "b'Server Error", 500, "Server Error", "Internal Server Error"
        )
        mock.headers = {"content-type": "text/plain"}
        return mock

    return MockResponse(notfoundjson, 404, "Not_Found")


def test_aeris_service_get_vehicledata_on_dynamodb_check_true_with_valid_db_response_return_200(
    patched_rest_client, mock_logger, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = mocked_requests_get
    mock_dynamo_cv_table.query.return_value = generate_valid_aeris_dbresponse()
    aerisservice = AerisService(
        config=AerisConfig(
            base_url="https://successjson",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
    )
    response = aerisservice.get_vehicledata("5243583607", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.SUCCESS
    assert response.programcode == "vwcarnet"
    assert response.msisdn == "5243583607"
    assert response.odometerscale == OdometerScaleType.MILES
    assert response.vin == "dbresponse_VIN"


def test_aeris_service_get_vehicledata_on_dynamodb_check_true_with_valid_external_response_return_200(
    patched_rest_client, mock_logger, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = mocked_requests_get
    mock_dynamo_cv_table.query.return_value = [None]
    aerisservice = AerisService(
        config=AerisConfig(
            base_url="https://successjson",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
    )

    response = aerisservice.get_vehicledata("5243583607", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.SUCCESS
    assert response.programcode == "vwcarnet"
    assert response.msisdn == "5243583607"
    assert response.odometerscale == OdometerScaleType.MILES


def test_aeris_service_get_vehicledata_on_dynamodb_check_false_with_valid_external_response_return_200(
    patched_rest_client, mock_logger, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = mocked_requests_get
    aerisservice = AerisService(
        config=AerisConfig(
            base_url="https://successjson",
            dynamodb_check_enable=False,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
    )

    response = aerisservice.get_vehicledata("5243583607", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.SUCCESS
    assert response.programcode == "vwcarnet"
    assert response.msisdn == "5243583607"
    assert response.odometerscale == OdometerScaleType.MILES


def test_aeris_service_get_vehicledata_on_get_success_but_save_fail_returns_getresponse_successfully(
    patched_rest_client, mock_logger
):
    patched_rest_client.get.side_effect = mocked_requests_get
    aerisservice = AerisService(
        config=AerisConfig(base_url="https://successjson"),
        table="exception",
    )
    response = aerisservice.get_vehicledata("5243583607", "vwcarnet")
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.SUCCESS


@mock_dynamodb2
def test_aeris_service_save_vehicledata_should_save_data_as_expected(
    patched_rest_client, mock_logger
):
    TABLE_NAME = "local-cv"
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
    patched_rest_client.get.side_effect = mocked_requests_get
    dynamotable = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    aerisservice = AerisService(
        config=AerisConfig(base_url="https://successjson"),
        table=dynamotable,
    )

    vehicledatajson = generate_valid_aeris_data()
    aerisservice.save_vehicledata(
        "5243583607", "vwcarnet", VehicleData(**vehicledatajson)
    )

    conn = boto3.resource("dynamodb", region_name="us-east-1")
    table = conn.Table(TABLE_NAME)
    result = table.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("vwcarnet-5243583607"),
    )

    assert result["Items"][0]["request_key"] == "vwcarnet-5243583607"
    assert result["Items"][0]["msisdn"] == "5243583607"
    assert result["Items"][0]["vin"] == "1VWSA7A3XLC011823"
    assert result["Items"][0]["latitude"] == Decimal("37.532918")
    assert result["Items"][0]["longitude"] == Decimal("-122.272576")
    assert result["Items"][0]["odometer"] == 16114
    assert result["Items"][0]["odometerscale"] == OdometerScaleType.MILES


def test_aeris_service_get_vehicledata_on_badrequest_should_return_400(
    setup_aeris_service, patched_rest_client
):
    patched_rest_client.get.side_effect = mocked_requests_get
    aerisservice = setup_aeris_service
    aerisservice._config.base_url = "https://badrequestjson/"

    response = aerisservice.get_vehicledata("aaaaa", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.BADREQUEST
    assert (
        response.responsemessage
        == "MSISDN_LENGTH_WRONG, MSISDN should atleast be 10 digits"
    )


def test_aeris_service_get_vehicledata_on_request_not_found_should_return_404(
    setup_aeris_service, patched_rest_client, mock_logger
):
    patched_rest_client.get.side_effect = mocked_requests_get
    setup_aeris_service._logger = mock_logger

    response = setup_aeris_service.get_vehicledata("aaaaa", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.NOTFOUND
    assert response.responsemessage == "MSISDN_NOT_FOUND, Unknown Error Situation"
    assert mock_logger.error.called


def test_aeris_service_get_vehicledata_on_exception_should_return_500(
    setup_aeris_service, patched_rest_client
):
    patched_rest_client.get.side_effect = Exception("something wrong")

    response = setup_aeris_service.get_vehicledata("aaaaa", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "something wrong"


@pytest.mark.parametrize(
    "mockedresponsekey", ["datanode_missing_on_success", "errornode_missing_on_error"]
)
def test_aeris_service_get_vehicledata_on_response_parent_node_missing_should_return_500(
    setup_aeris_service, patched_rest_client, mockedresponsekey
):
    patched_rest_client.get.side_effect = mocked_requests_get
    aerisservice = setup_aeris_service
    aerisservice._config.base_url = "https://" + mockedresponsekey + "/"

    response = aerisservice.get_vehicledata("5243583607", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR


def test_aeris_service_get_vehicledata_on_content_not_supported_should_return_500(
    setup_aeris_service, patched_rest_client
):
    patched_rest_client.get.side_effect = mocked_requests_get
    aerisservice = setup_aeris_service
    aerisservice._config.base_url = "https://content_notsupported/"

    response = aerisservice.get_vehicledata("aaaaa", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "Content not supported"


def test_aeris_service_get_vehicledata_on_server_error_should_return_500(
    setup_aeris_service, patched_rest_client, mock_logger
):
    patched_rest_client.get.side_effect = mocked_requests_get
    aerisservice = setup_aeris_service
    aerisservice._config.base_url = "https://server_error/"
    setup_aeris_service._logger = mock_logger

    response = aerisservice.get_vehicledata("aaaaa", "vwcarnet")

    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "Server Error"
    assert mock_logger.error.called


def test_aeris_service_get_data_from_database_on_valid_input_response_should_return_valid_db_dataresponse(
    mock_dynamo_cv_table,
):
    mock_dynamo_cv_table.query.return_value = generate_valid_aeris_dbresponse()
    aerisservice = AerisService(
        config=AerisConfig(
            base_url="https://successjson",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
    )
    dataresponse = get_data_from_database(
        aerisservice,
        msisdn="5243583607",
        programcode="vwcarnet",
        ctsversion="2.0",
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.msisdn == "5243583607"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.vin == "dbresponse_VIN"


def test_aeris_service_get_data_from_database_on_input_response_none_should_return_dataresponse_as_none(
    mock_dynamo_cv_table,
):
    mock_dynamo_cv_table.query.return_value = None
    aerisservice = AerisService(
        config=AerisConfig(
            base_url="https://successjson",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
    )
    dataresponse = get_data_from_database(
        aerisservice,
        msisdn="5243583607",
        programcode="vwcarnet",
        ctsversion="2.0",
    )
    assert dataresponse is None


def test_aeris_service_create_vehicledata_response_on_valid_input_response_should_return_valid_db_dataresponse():
    dataresponse = create_vehicledata_response(
        response=generate_valid_aeris_dbresponse()[0],
        msisdn="5243583607",
        programcode="vwcarnet",
        responsestatus=InternalStatusType.SUCCESS,
        responsemessage="Successfully retrieved",
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS


def test_aeris_service_create_vehicledata_response_on_input_response_none_should_return_dataresponse_as_none():
    dataresponse = create_vehicledata_response(
        response=None,
        msisdn="5243583607",
        programcode="vwcarnet",
        responsestatus=InternalStatusType.NOTFOUND,
        responsemessage="No data is available for msisdn: 5243583607",
    )
    assert dataresponse is None


def test_aeris_service_populate_vehicledata_with_valid_payload_populate_as_expected(
    setup_aeris_service,
):
    aeris_json = generate_valid_aeris_data()
    vehicledata = setup_aeris_service.populate_vehicledata(
        "5243583607", "vwcarnet", aeris_json
    )
    assert vehicledata.msisdn == aeris_json["msisdn"]
    assert vehicledata.latitude == aeris_json["latitude"]
    assert vehicledata.vin == aeris_json["vin"]


@pytest.mark.parametrize(
    "invaliddata,expected", [(None, None), ("", None)], ids=[None, "Empty"]
)
def test_aeris_service_populate_vehicledata_with_invalid_data_works_as_expected(
    setup_aeris_service, invaliddata, expected
):
    vehicledata = setup_aeris_service.populate_vehicledata(
        "12345678901", "vwcarnet", invaliddata
    )
    assert vehicledata == expected


# Not implemented abstract method tests
def test_aeris_service_on_calling_assign_agent_raise_notimplementedexception(
    setup_aeris_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_aeris_service.assign_agent(any)
    assert execinfo.type == NotImplementedError


def test_aeris_service_on_calling_terminate_raise_notimplementedexception(
    setup_aeris_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_aeris_service.terminate(any)
    assert execinfo.type == NotImplementedError


def test_aeris_serivce_on_calling_health_raise_notimplementedexception(
    setup_aeris_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_aeris_service.health(ProgramCode.VWCARNET, CtsVersion.TWO_DOT_ZERO)
    assert execinfo.type == NotImplementedError


def generate_valid_aeris_data():
    return {
        "msisdn": "5243583607",
        "programcode": "vwcarnet",
        "event_datetime": 1597783540014,
        "timestamp": datetime.strptime(
            "2020-09-25T19:05:15.769000", "%Y-%m-%dT%H:%M:%S.%f"
        ),  # calldate and time
        "calldate": "2020-09-25",
        "activationtype": "0",
        "calltime": "19:05",
        "vin": "1VWSA7A3XLC011823",
        "brand": "vw",
        "modelname": "Passat",
        "modelyear": "2008",
        "modelcode": "A342P6",
        "modeldesc": "Passat_2008",
        "market": "nar-us",
        "odometer": 16114,
        "odometerscale": "Miles",
        "latitude": 37.532918,
        "longitude": -122.272576,
        "headingdirection": "NORTH EAST",
        "countrycode": None,
        "status": "SUCCESS",
        "responsemessage": "response message",
    }


def generate_valid_aeris_dbresponse():
    return [
        ConnectedVehicleTable(
            request_key="vwcarnet-5243583607",
            msisdn="5243583607",
            programcode="vwcarnet",
            event_datetime=int(datetime.timestamp(datetime.utcnow()) * 1000),
            timestamp=datetime.now(),
            activationtype="0",
            vin="dbresponse_VIN",
            brand="vw",
            modelname="Passat",
            modelyear="2008",
            modelcode="A342P6",
            modeldesc="Passat_2008",
            market="nar-us",
            odometer=0,
            odometerscale="Miles",
            latitude="37.532918",
            longitude="-122.272576",
            headingdirection="NORTH EAST",
            countrycode="US",
        )
    ]

from datetime import datetime
from decimal import Decimal
from src.vodafone.models.data.vehicle_info import VehicleInfo

import boto3
import pytest
import json
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
from src.config.dynamo_config import DynamoConfig
from src.config.vodafone_config import VodafoneConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.dynamodb_tables import (
    ConnectedVehicleSupplementTable,
    ConnectedVehicleTable,
    get_main_table,
    get_supplement_table,
)
from src.vodafone.models.data.vehicle_data import VehicleData
from src.vodafone.models.domain.vehicle_data import VehicleDataRequest
from src.vodafone.services.vodafone_service import (
    VodafoneService,
    map_primarytable,
    map_supplementtable,
    save_supplementdata,
)

DYNAMO_TABLE_NAME = "cv-table"
DYNAMO_SUPPLEMENT_TABLE_NAME = "cv-supplement-table"


@pytest.fixture
def setup_vodafone_service(
    mock_logger, mock_dynamo_cv_table, mock_dynamo_supplement_cv_table
):
    uut = VodafoneService(
        config=VodafoneConfig(
            dynamo_table_name=DYNAMO_TABLE_NAME,
            dynamo_supplement_table_name=DYNAMO_SUPPLEMENT_TABLE_NAME,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    yield uut


@mock_dynamodb2
def test_service_save_vehicledata_returns_200_if_success(mock_logger):
    TABLE_NAME = dynamodb_table_setup("local-cv")
    primary_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    SUPPLEMENT_TABLE_NAME = dynamodb_table_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    vodafoneservice = VodafoneService(
        config=VodafoneConfig(),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_vodafone_data()

    response = vodafoneservice.save_vehicledata(
        "12038594938", "porsche", vehicledatajson
    )

    conn = boto3.resource("dynamodb", region_name="us-east-1")
    primarytable = conn.Table(TABLE_NAME)
    result = primarytable.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("porsche-12038594938"),
    )

    supplementtable = conn.Table(SUPPLEMENT_TABLE_NAME)
    supplementtable_result = supplementtable.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("porsche-12038594938"),
    )

    assert type(response) == VehicleData
    assert response.msisdn == "12038594938"
    assert response.status == InternalStatusType.SUCCESS
    assert (
        response.responsemessage
        == "Successfully saved the vehicledata for msisdn: 12038594938"
    )

    assert result["Items"][0]["request_key"] == "porsche-12038594938"
    assert result["Items"][0]["msisdn"] == "12038594938"

    assert result["Items"][0]["vin"] == "WP0BNM97ZAL040111"
    assert result["Items"][0]["latitude"] == Decimal("+42.98665")
    assert result["Items"][0]["longitude"] == Decimal("-80.92240")
    assert result["Items"][0]["brand"] == "PORSCHE"
    assert result["Items"][0]["mileage"] == 0
    assert json.loads(result["Items"][0]["JSONData"]) == vehicledatajson

    assert supplementtable_result["Items"][0]["ignitionkey"] == "OFF"
    assert supplementtable_result["Items"][0]["range"] == 0
    assert supplementtable_result["Items"][0]["crankinhibition"] == Decimal("0")
    assert supplementtable_result["Items"][0]["fuellevelpercentage"] == Decimal("0")
    assert supplementtable_result["Items"][0]["tirepressurefrontleft"] == Decimal(
        "-6.3"
    )
    assert supplementtable_result["Items"][0]["tirepressurefrontright"] == Decimal(
        "-6.3"
    )

    assert supplementtable_result["Items"][0]["tirepressurerearleft"] == Decimal("-6.3")
    assert supplementtable_result["Items"][0]["tirepressurerearright"] == Decimal(
        "-6.3"
    )


@mock_dynamodb2
def test_save_vehicledata_returns_success_even_if_secondary_data_save_is_unsuccessful(
    mock_logger,
):

    TABLE_NAME = dynamodb_table_setup("local-cv")
    primary_table = get_main_table(DynamoConfig(table_name=TABLE_NAME))
    supplement_table = "invalid"

    vodafoneservice = VodafoneService(
        config=VodafoneConfig(),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_vodafone_data()
    response = vodafoneservice.save_vehicledata(
        "12038594938", "porsche", vehicledatajson
    )
    assert type(response) == VehicleData
    assert response.msisdn == "12038594938"
    assert response.status == InternalStatusType.SUCCESS
    assert (
        response.responsemessage
        == "Successfully saved the vehicledata for msisdn: 12038594938"
    )


@mock_dynamodb2
def test_save_vehicledata_returns_500_if_primary_data_save_is_unsuccessful(mock_logger):
    primary_table = "invalid"
    SUPPLEMENT_TABLE_NAME = dynamodb_table_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    vodafoneservice = VodafoneService(
        config=VodafoneConfig(),
        table=primary_table,
        supplementtable=supplement_table,
    )

    vehicledatajson = generate_valid_vodafone_data()
    response = vodafoneservice.save_vehicledata(
        "13234826699", "porsche", vehicledatajson
    )
    assert type(response) == VehicleData
    assert response.msisdn == "13234826699"
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert (
        response.responsemessage
        == "Unable to save the vehicledata for msisdn: 13234826699"
    )


@mock_dynamodb2
def test_save_vehicledata_on_populate_vehicle_data_error_returns_500(
    setup_vodafone_service,
):
    response = setup_vodafone_service.save_vehicledata(
        "1234567890",
        "porsche",
        {
            "gpsData": {"some": "some"},
            "vehicleData": {"some": "some"},
            "userData": {"some": "some"},
        },
    )
    assert type(response) == VehicleData
    assert response.msisdn == "1234567890"
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert (
        response.responsemessage
        == "Unable to save the vehicledata for msisdn: 1234567890"
    )


@pytest.mark.parametrize(
    "invalid_json",
    [
        (None),
        ({"vehicleData": {"some": "some"}, "userData": {"some": "some"}}),
        ({"gpsData": {"some": "some"}, "userData": {"some": "some"}}),
        ({"gpsData": {"some": "some"}, "vehicleData": {"some": "some"}}),
    ],
    ids=[
        "None",
        "Missing_gpsData_Node",
        "Missing_vehicleData_Node",
        "Missing_userData_Node",
    ],
)
def test_save_vehicledata_on_bad_request_returns_400(
    setup_vodafone_service, invalid_json
):
    response = setup_vodafone_service.save_vehicledata(
        "1234567890", "porsche", invalid_json
    )
    assert type(response) == VehicleData
    assert response.msisdn == "1234567890"
    assert response.status == InternalStatusType.BADREQUEST
    assert (
        response.responsemessage
        == "SaveVehicleData: Json payload is invalid for msisdn: 1234567890"
    )


def test_populate_vehicledata_with_valid_payload_populate_as_expected(
    setup_vodafone_service,
):
    vodafone_json = generate_valid_vodafone_data()
    vehicledata = setup_vodafone_service.populate_vehicledata(
        "12345678901", "porsche", vodafone_json
    )
    assert vehicledata.countryCode == vodafone_json["countryCode"]
    assert vehicledata.gpsData.latitude == vodafone_json["gpsData"]["latitude"]
    assert vehicledata.vehicleData.vin == vodafone_json["vehicleData"]["vin"]
    assert (
        vehicledata.userData.phoneContact == vodafone_json["userData"]["phoneContact"]
    )


@pytest.mark.parametrize(
    "invaliddata,expected", [(None, None), ("", None)], ids=[None, "Empty"]
)
def test_populate_vehicledata_with_invalid_data_works_as_expected(
    setup_vodafone_service, invaliddata, expected
):
    vehicledata = setup_vodafone_service.populate_vehicledata(
        "12345678901", "porsche", invaliddata
    )
    assert vehicledata == expected


@mock_dynamodb2
def test_save_supplementdata_saves_data_on_success(mock_dynamo_cv_table, mock_logger):
    SUPPLEMENT_TABLE_NAME = dynamodb_table_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    vodafoneservice = VodafoneService(
        config=VodafoneConfig(),
        table=mock_dynamo_cv_table,
        supplementtable=supplement_table,
    )

    save_supplementdata(
        vodafoneservice,
        "12038594938",
        "porsche",
        VehicleDataRequest(**generate_valid_vodafone_data()),
    )

    conn = boto3.resource("dynamodb", region_name="us-east-1")

    supplementtable = conn.Table(SUPPLEMENT_TABLE_NAME)
    supplementtable_result = supplementtable.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("porsche-12038594938"),
    )

    assert supplementtable_result["Items"][0]["msisdn"] == "12038594938"
    assert supplementtable_result["Items"][0]["ignitionkey"] == "OFF"
    assert supplementtable_result["Items"][0]["range"] == 0
    assert supplementtable_result["Items"][0]["tirepressurerearleft"] == Decimal("-6.3")
    assert supplementtable_result["Items"][0]["tirepressurerearright"] == Decimal(
        "-6.3"
    )


@mock_dynamodb2
def test_save_supplementdata_stores_no_data_on_exception(
    mock_dynamo_cv_table, mock_logger
):
    SUPPLEMENT_TABLE_NAME = dynamodb_table_setup("local-supplement-cv")
    supplement_table = get_supplement_table(
        DynamoConfig(supplement_table_name=SUPPLEMENT_TABLE_NAME)
    )

    vodafoneservice = VodafoneService(
        config=VodafoneConfig(),
        table=mock_dynamo_cv_table,
        supplementtable=supplement_table,
    )

    save_supplementdata(
        vodafoneservice,
        "12038594938",
        "porsche",
        "invalid",
    )

    conn = boto3.resource("dynamodb", region_name="us-east-1")

    supplementtable = conn.Table(SUPPLEMENT_TABLE_NAME)
    supplementtable_result = supplementtable.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("porsche-12038594938"),
    )

    assert supplementtable_result["Count"] == 0


def test_map_primarytable_maps_data_as_expected():
    tbl = ConnectedVehicleTable
    input_payload = generate_valid_vodafone_data()
    tblprimary = map_primarytable(
        "1234567890",
        "porsche",
        VehicleDataRequest(**input_payload),
        tbl,
        input_payload,
    )

    assert tblprimary.msisdn == "1234567890"
    assert tblprimary.brand == "PORSCHE"
    assert tblprimary.countrycode == "US"
    assert tblprimary.JSONData == input_payload


def test_map_secondarytable_maps_data_as_expected():
    tbl = ConnectedVehicleSupplementTable
    tblsupplemnt = map_supplementtable(
        "1234567890",
        "porsche",
        VehicleDataRequest(**generate_valid_vodafone_data()),
        tbl,
    )

    assert tblsupplemnt.msisdn == "1234567890"
    assert tblsupplemnt.range == 0
    assert tblsupplemnt.registrationnumber == "PCC-US-03"


def dynamodb_table_setup(tblname):
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


def generate_valid_vodafone_data(vin="WP0BNM97ZAL040111"):
    return {
        "countryCode": "US",
        "timestamp": "1486741602",
        "gpsData": {"latitude": "+42.98665", "longitude": "-80.92240"},
        "vehicleData": {
            "vin": vin,
            "registration": {
                "number": "PCC-US-03",
                "stateCode": "RI",
                "countryCode": "US",
            },
            "crankInhibition": "0",
            "ignitionKey": "OFF",
            "mileage": {"value": "0", "unit": "mi"},
            "fuelLevelPercentage": "0",
            "evBatteryPercentage": "0",
            "range": {"value": "0", "unit": "mi"},
            "tyrePressureDelta": {
                "unit": "bar",
                "frontLeft": "-6.3",
                "frontRight": "-6.3",
                "rearLeft": "-6.3",
                "rearRight": "-6.3",
            },
        },
        "userData": {"phoneContact": "+12038594938"},
    }


def test_vodafone_service_get_vehicledata_on_success_return_200(
    mock_dynamo_cv_table, setup_vodafone_service
):
    mock_dynamo_cv_table.query.return_value = generate_valid_vodafone_data_singlelist()
    dataresponse = setup_vodafone_service.get_vehicledata(
        msisdn="12345678901", programcode="porsche"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "porsche"
    assert dataresponse.vin == "TESTFIRSTVIN"
    assert dataresponse.calldate == dataresponse.timestamp.strftime("%Y-%m-%d")
    assert dataresponse.calltime == dataresponse.timestamp.strftime("%H:%M")
    assert dataresponse.mileage == 0
    assert dataresponse.mileageunit == "Miles"


@pytest.mark.parametrize("msisdn", [("2345678901"), ("12345678901")])
def test_vodafone_service_get_vehicledata_format_msisdn_prefix_countrycode_if_missing(
    mock_dynamo_cv_table, setup_vodafone_service, msisdn
):
    mock_dynamo_cv_table.query.return_value = generate_valid_vodafone_data_singlelist()
    dataresponse = setup_vodafone_service.get_vehicledata(
        msisdn=msisdn, programcode="porsche"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"


def test_vodafone_service_get_vehicledata_on_multiple_records_returns_the_latest(
    mock_dynamo_cv_table, setup_vodafone_service
):
    mock_dynamo_cv_table.query.return_value = (
        generate_valid_vodafone_data_multiplelist()
    )
    dataresponse = setup_vodafone_service.get_vehicledata(
        msisdn="12345678901", programcode="porsche"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.vin == "TESTFIRSTVIN"


def test_vodafone_service_get_vehicledata_on_no_data_returns_not_found(
    mock_dynamo_cv_table, setup_vodafone_service
):
    mock_dynamo_cv_table.query.return_value = []
    dataresponse = setup_vodafone_service.get_vehicledata(
        msisdn="12345678901", programcode="porsche"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.NOTFOUND
    assert dataresponse.responsemessage == "No data found"


def test_vodafone_service_get_vehicledata_on_exception_returns_internalservererror(
    mock_dynamo_cv_table, setup_vodafone_service
):
    mock_dynamo_cv_table.query.return_value = Exception
    dataresponse = setup_vodafone_service.get_vehicledata(
        msisdn="12345678901", programcode="porsche"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.INTERNALSERVERERROR



def test_vodafone_service_get_vehicleinfo_on_success_return_200(
    mock_dynamo_cv_table, setup_vodafone_service
):
    input_json = generate_valid_vodafone_data("TESTFIRSTVIN")
    mock_dynamo_cv_table.query.return_value = [generate_valid_vodafone_cv_data("TESTFIRSTVIN", input_json)]
    dataresponse = setup_vodafone_service.get_vehicleinfo(
        msisdn="12345678901"
    )
    assert type(dataresponse) == VehicleInfo
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "porsche"
    assert dataresponse.JSONData == input_json
    assert dataresponse.JSONData["vehicleData"]["vin"] == "TESTFIRSTVIN"


@pytest.mark.parametrize("msisdn", [("2345678901"), ("12345678901")])
def test_vodafone_service_get_vehicleinfo_format_msisdn_prefix_countrycode_if_missing(
    mock_dynamo_cv_table, setup_vodafone_service, msisdn
):
    mock_dynamo_cv_table.query.return_value = [generate_valid_vodafone_cv_data("TESTFIRSTVIN", generate_valid_vodafone_data("TESTFIRSTVIN"))]
    dataresponse = setup_vodafone_service.get_vehicleinfo(
        msisdn=msisdn
    )
    assert type(dataresponse) == VehicleInfo
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"


def test_vodafone_service_get_vehicleinfo_on_multiple_records_returns_the_latest(
    mock_dynamo_cv_table, setup_vodafone_service
):
    latest_payload = generate_valid_vodafone_data("TESTLATESTVIN")
    mock_dynamo_cv_table.query.return_value = (
        [
        generate_valid_vodafone_cv_data("TESTLATESTVIN", latest_payload),
        generate_valid_vodafone_cv_data("TESTSECONDVIN", generate_valid_vodafone_data("TESTSECONDVIN")),
        generate_valid_vodafone_cv_data("TESTFIRSTVIN", generate_valid_vodafone_data("TESTFIRSTVIN")),
    ]
    )
    dataresponse = setup_vodafone_service.get_vehicleinfo(
        msisdn="12345678901"
    )
    assert type(dataresponse) == VehicleInfo
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.JSONData == latest_payload
    assert dataresponse.JSONData["vehicleData"]["vin"] == "TESTLATESTVIN"


def test_vodafone_service_get_vehicleinfo_on_no_data_returns_not_found(
    mock_dynamo_cv_table, setup_vodafone_service
):
    mock_dynamo_cv_table.query.return_value = []
    dataresponse = setup_vodafone_service.get_vehicleinfo(
        msisdn="12345678901"
    )
    assert type(dataresponse) == VehicleInfo
    assert dataresponse.status == InternalStatusType.NOTFOUND
    assert dataresponse.responsemessage == "No data found"


def test_vodafone_service_get_vehicleinfo_on_exception_returns_internalservererror(
    mock_dynamo_cv_table, setup_vodafone_service
):
    mock_dynamo_cv_table.query.return_value = Exception
    dataresponse = setup_vodafone_service.get_vehicleinfo(
        msisdn="12345678901"
    )
    assert type(dataresponse) == VehicleInfo
    assert dataresponse.status == InternalStatusType.INTERNALSERVERERROR


def generate_valid_vodafone_data_singlelist():
    datalist = [generate_valid_vodafone_cv_data("TESTFIRSTVIN")]
    return datalist


def generate_valid_vodafone_data_multiplelist():
    datalist = [
        generate_valid_vodafone_cv_data("TESTFIRSTVIN"),
        generate_valid_vodafone_cv_data("TESTSECONDVIN"),
        generate_valid_vodafone_cv_data("TESTLATESTVIN"),
    ]
    return datalist


def generate_valid_vodafone_cv_data(vin, input_payload=None):
    return ConnectedVehicleTable(
        request_key="porsche-TESTMSISDN",
        msisdn="TESTMSISDN",
        programcode="porsche",
        event_datetime=int(
            datetime.timestamp(datetime.utcnow()) * 1000
        ),  # 1597783540014,
        timestamp=datetime.now(),
        vin=vin,
        brand="PORSCHE",
        mileage=0,
        mileageunit="mi",
        latitude="37.532918",
        longitude="-122.272576",
        countrycode="US",
        JSONData=input_payload,
    )


# Not implemented abstract method tests


def test_vodafone_serivce_on_calling_assign_agent_raise_notimplementedexception(
    setup_vodafone_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_vodafone_service.assign_agent(any)
    assert execinfo.type == NotImplementedError


def test_vodafone_serivce_on_calling_terminate_raise_notimplementedexception(
    setup_vodafone_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_vodafone_service.terminate(any)
    assert execinfo.type == NotImplementedError


def test_vodafone_serivce_on_calling_health_raise_notimplementedexception(
    setup_vodafone_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_vodafone_service.health(ProgramCode.PORSCHE, CtsVersion.ONE_DOT_ZERO)
    assert execinfo.type == NotImplementedError

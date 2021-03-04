from unittest.mock import patch
from datetime import datetime
import pytest

from src.config.aeris_config import AerisConfig
from src.aeris.services.aeris_service import AerisService
from src.config.verizon_config import VerizonConfig
from src.verizon.services.verizon_service import VerizonService
from src.services.dynamodb_helper import get_vehicledata_for_config_enabled_client_only
from src.services.dynamodb_tables import ConnectedVehicleTable

BASE_URL = "fooBaseURL"
ROOT_CERT = "fooCERT"
WSDL = "fooWSDL"
DYNAMO_TABLE_NAME = "fooTable"
DYNAMO_SUPPLEMENT_TABLE_NAME = "fooSupplementTable"
DYNAMODB_CHECK_ENABLE = True
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
def setup_verizon_service(
    mock_logger,
    mock_dynamo_cv_table,
    mock_dynamo_supplement_cv_table,
):
    config = VerizonConfig(
        base_url=BASE_URL,
        root_cert=ROOT_CERT,
        wsdl=WSDL,
        dynamo_table_name=DYNAMO_TABLE_NAME,
        dynamo_supplement_table_name=DYNAMO_SUPPLEMENT_TABLE_NAME,
        dynamodb_check_enable=DYNAMODB_CHECK_ENABLE,
        dynamodb_check_timelimit=DYNAMODB_CHECK_TIMELIMIT,
    )
    uut = VerizonService(
        config=config,
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_supplement_cv_table,
    )
    yield uut


def test_dynamodb_helper_get_vehicledata_for_config_enabled_client_only_for_aeris_on_success_should_return_valid_db_dataresponse(
    mock_dynamo_cv_table, setup_aeris_service
):
    mock_dynamo_cv_table.query.return_value = generate_valid_aeris_data()
    dataresponse = get_vehicledata_for_config_enabled_client_only(
        setup_aeris_service, id="12345678901", programcode="vwcarnet", ctsversion="2.0"
    )
    assert type(dataresponse) == ConnectedVehicleTable
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.vin == "VIN_AERIS"


def test_dynamodb_helper_get_vehicledata_for_config_enabled_client_only_for_aeris_on_no_data_found_should_return_dataresponse_as_none(
    mock_dynamo_cv_table, setup_aeris_service
):
    mock_dynamo_cv_table.query.return_value = None
    dataresponse = get_vehicledata_for_config_enabled_client_only(
        setup_aeris_service, id="12345678901", programcode="vwcarnet", ctsversion="2.0"
    )
    assert dataresponse is None


def test_dynamodb_helper_get_vehicledata_for_config_enabled_client_only_for_aeris_on_exception_should_return_dataresponse_as_none(
    mock_dynamo_cv_table, setup_aeris_service
):
    mock_dynamo_cv_table.query.side_effect = Exception()
    dataresponse = get_vehicledata_for_config_enabled_client_only(
        setup_aeris_service, id="12345678901", programcode="vwcarnet", ctsversion="2.0"
    )
    assert dataresponse is None


def test_dynamodb_helper_get_vehicledata_for_config_enabled_client_only_for_verizon_on_success_should_return_valid_db_dataresponse(
    mock_dynamo_cv_table, setup_verizon_service
):
    mock_dynamo_cv_table.query.return_value = generate_valid_verizon_dbresponse()
    dataresponse = get_vehicledata_for_config_enabled_client_only(
        setup_verizon_service,
        id="12345678901",
        programcode="vwcarnet",
        ctsversion="1.0",
    )
    assert type(dataresponse) == ConnectedVehicleTable
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.customerfirstname == "JUSTINE"
    assert dataresponse.vin == "VIN_VERIZON"


def test_dynamodb_helper_get_vehicledata_for_config_enabled_client_only_for_verizon_on_no_data_found_should_return_dataresponse_as_none(
    mock_dynamo_cv_table, setup_verizon_service
):
    mock_dynamo_cv_table.query.return_value = None
    dataresponse = get_vehicledata_for_config_enabled_client_only(
        setup_verizon_service,
        id="12345678901",
        programcode="vwcarnet",
        ctsversion="1.0",
    )
    assert dataresponse is None


def test_dynamodb_helper_get_vehicledata_for_config_enabled_client_only_for_verizon_on_exception_should_return_dataresponse_as_none(
    mock_dynamo_cv_table, setup_verizon_service
):
    mock_dynamo_cv_table.query.side_effect = Exception()
    dataresponse = get_vehicledata_for_config_enabled_client_only(
        setup_verizon_service,
        id="12345678901",
        programcode="vwcarnet",
        ctsversion="1.0",
    )
    assert dataresponse is None


def generate_valid_aeris_data():
    return [
        ConnectedVehicleTable(
            request_key="vwcarnet-12345678901",
            msisdn="12345678901",
            programcode="vwcarnet",
            event_datetime=1597783540014,
            timestamp=datetime.strptime(
                "2020-09-25T19:05:15.769000", "%Y-%m-%dT%H:%M:%S.%f"
            ),  # calldate and time
            activationtype="0",
            vin="VIN_AERIS",
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


def generate_valid_verizon_dbresponse():
    return [
        ConnectedVehicleTable(
            request_key="vwcarnet-12345678901",
            msisdn="12345678901",
            programcode="vwcarnet",
            event_datetime=1610529816192,
            timestamp=datetime.strptime("01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"),
            calldate="01/07/2021",
            activationtype=None,
            calltime="13:44:32",
            vin="VIN_VERIZON",
            brand="vw",
            modelname="Passat",
            modelyear="2008",
            modelcode="vw",
            modeldesc=None,
            market=None,
            odometer=None,
            odometerscale=None,
            latitude=0,  # 37.532918
            longitude=-122.272576,
            headingdirection="NONE",
            countrycode="US",
            mileage=None,
            mileageunit=None,
            customerfirstname="JUSTINE",
            customerlastname="EHLERS",
            modelcolor="Pure White",
            srnumber="1-13220115574",
            ismoving=False,
            cruisingrange="385.25 Miles",
            locationtrueness="weak",
            locationconfidence=2,
            locationaddress="12345 TE 123th Way",
            locationcity="Redmond",
            locationstate="WA",
            locationpostalcode="98052-1019",
            phonenumber="4258811803",
            altitude="0",
            language="English",
        )
    ]

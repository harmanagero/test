from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
from requests.models import Response
from src.config.dynamo_config import DynamoConfig
from src.config.verizon_config import VerizonConfig
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.dynamodb_tables import (
    ConnectedVehicleTable,
    get_main_table,
)
from src.verizon.models.data.vehicle_data import VehicleData
from src.verizon.services.verizon_service import (
    VerizonService,
    get_additionaldata_from_header,
    get_timestamp_from_calldate,
    get_data_from_database,
    create_vehicledata_response,
    map_vehicledata_response,
)

BASE_URL = "fooBaseURL"
ROOT_CERT = "fooCERT"
WSDL = "fooWSDL"
DYNAMO_TABLE_NAME = "fooTable"
DYNAMO_SUPPLEMENT_TABLE_NAME = "fooSupplementTable"
DYNAMODB_CHECK_ENABLE = False
DYNAMODB_CHECK_TIMELIMIT = 2


@pytest.fixture
def patched_setup_logger():
    with patch("src.verizon.services.verizon_service.logger") as mocked_setup:
        yield mocked_setup


@pytest.fixture
def setup_verizon_service(
    mock_logger, mock_dynamo_cv_table, mock_dynamo_supplement_cv_table
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


@pytest.fixture
def patched_zeep_client():
    with patch(
        "src.verizon.services.verizon_service.retrieve_zeepclient"
    ) as patched_zeep_client:
        yield patched_zeep_client


@pytest.fixture
def patched_rest_client():
    with patch("src.verizon.services.verizon_service.requests") as patched_rest_client:
        yield patched_rest_client


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, response_text, status_code):
            self.status_code = status_code
            self.headers = {"content-type": "text/xml;charset=UTF-8"}
            self.text = response_text

    if "success" in args[0]:
        return MockResponse("<xml></xml>", 200)
    elif "notfound" in args[0]:
        return MockResponse("File Not Found", 404)
    elif "content_notsupported" in args[0]:
        mock = MockResponse("b'Server Error", 500)
        mock.headers = {"content-type": "text/plain"}
        mock.reason = "Internal Server Error"
        mock.text = "Server Error"
        return mock

    return MockResponse("Error 500", 500)


mockServiceErrorTestData = [
    ("No Data Found", InternalStatusType.NOTFOUND),
    (" ", InternalStatusType.INTERNALSERVERERROR),
]


def test_verizon_service_get_vehicledata_on_dynamodb_check_true_with_valid_db_response_return_200(
    patched_zeep_client, setup_verizon_service, mock_logger, mock_dynamo_cv_table
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    verizonservice = VerizonService(
        config=VerizonConfig(
            base_url="https://success",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = (
        generete_valid_verizon_external_response()
    )
    mock_dynamo_cv_table.query.return_value = generate_valid_verizon_dbresponse()
    dataresponse = verizonservice.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.phonenumber == "4258811803"
    assert dataresponse.timestamp == datetime.strptime(
        "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
    )
    assert dataresponse.vin == "dbresponse_VIN"


def test_verizon_service_get_vehicledata_on_dynamodb_check_true_with_valid_external_response_return_200(
    patched_zeep_client, setup_verizon_service, mock_logger, mock_dynamo_cv_table
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    verizonservice = VerizonService(
        config=VerizonConfig(
            base_url="https://success",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = (
        generete_valid_verizon_external_response()
    )
    mock_dynamo_cv_table.query.return_value = [None]
    dataresponse = verizonservice.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.phonenumber == "4258811803"
    assert dataresponse.timestamp == datetime.strptime(
        "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
    )


def test_verizon_service_get_vehicledata_on_dynamodb_check_false_with_valid_external_response_return_200(
    patched_zeep_client, setup_verizon_service, mock_logger, mock_dynamo_cv_table
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    verizonservice = VerizonService(
        config=VerizonConfig(
            base_url="https://success",
            dynamodb_check_enable=False,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = (
        generete_valid_verizon_external_response()
    )
    dataresponse = verizonservice.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.phonenumber == "4258811803"
    assert dataresponse.timestamp == datetime.strptime(
        "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
    )


def test_verizon_service_get_vehicledata_on_success_status_with_few_response_fields_should_return_200(
    setup_verizon_service, patched_zeep_client
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = {
        "CallDate": "01/07/2021",
        "CallTime": "13:44:32",
        "VIN": "1VWSA7A3XLC011823",
        "Make": "vw",
        "Model": "Passat",
        "VehicleYear": None,
        "CustomerFirstName": "JUSTINE",
        "CustomerLastName": "EHLERS",
        "ExteriorColor": "Pure White",
        "SRNumber": "1-13220115574",
        "FromLocationLatitude": "",
        "FromLocationLongitude": None,
        "FromLocationPhoneNo": "4258811803",
        "Response": {
            "ResponseCode": "00",
            "ResponseStatus": "Successful Execution",
            "ResponseDescription": "Data Found",
        },
    }

    dataresponse = setup_verizon_service.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.phonenumber == "4258811803"
    assert dataresponse.timestamp == datetime.strptime(
        "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
    )
    assert dataresponse.latitude == Decimal(0)
    assert dataresponse.longitude == Decimal(0)
    assert dataresponse.modelyear == "NONE"


def test_verizon_service_get_vehicledata_on_success_status_with_different_response_value_fields_should_return_200(
    setup_verizon_service, patched_zeep_client
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = {
        "CallDate": "01/07/2021",
        "CallTime": "13:44:32",
        "VIN": "1VWSA7A3XLC011823",
        "Make": "vw",
        "Model": "Passat",
        "VehicleYear": None,
        "CustomerFirstName": "JUSTINE",
        "CustomerLastName": "EHLERS",
        "ExteriorColor": "Pure White",
        "SRNumber": "1-13220115574",
        "FromLocationLatitude": "",
        "FromLocationLongitude": None,
        "FromLocationPhoneNo": "4258811803",
        "Location_confidence": "2 meters",
        "Altitude": "200 ft",
        "Response": {
            "ResponseCode": "00",
            "ResponseStatus": "Successful Execution",
            "ResponseDescription": "Data Found",
        },
    }

    dataresponse = setup_verizon_service.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.phonenumber == "4258811803"
    assert dataresponse.timestamp == datetime.strptime(
        "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
    )
    assert dataresponse.latitude == Decimal(0)
    assert dataresponse.longitude == Decimal(0)
    assert dataresponse.modelyear == "NONE"
    assert dataresponse.altitude == "200 ft"
    assert dataresponse.locationconfidence == "2 meters"


def test_verizon_service_get_vehicledata_success_status_with_invalid_calldate_should_return_200_with_current_timestamp(
    setup_verizon_service, patched_zeep_client
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = {
        "CallDate": "",
        "CallTime": "1",
        "VIN": "1VWSA7A3XLC011823",
        "Make": "vw",
        "Model": "Passat",
        "VehicleYear": "2008",
        "FromLocationLatitude": None,
        "FromLocationLongitude": -122.272576,
        "Direction_heading": None,
        "FromLocationCountry": "",
        "CustomerFirstName": "JUSTINE",
        "CustomerLastName": "EHLERS",
        "ExteriorColor": "Pure White",
        "SRNumber": "1-13220115574",
        "Is_moving": False,
        "Cruising_range": "385.25 Miles",
        "Location_trueness": "weak",
        "Location_confidence": 2,
        "FromLocationAddress": "12345 TE 123th Way",
        "FromLocationCity": "Redmond",
        "FromLocationState": "WA",
        "FromLocationZip": "98052-1019",
        "FromLocationPhoneNo": "4258811803",
        "Altitude": 542,
        "Hmi_language": "English",
        "Response": {
            "ResponseCode": "00",
            "ResponseStatus": "Successful Execution",
            "ResponseDescription": "Data Found",
        },
    }

    dataresponse = setup_verizon_service.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.phonenumber == "4258811803"
    assert dataresponse.timestamp.strftime("%d/%m/%Y %H") == datetime.now().strftime(
        "%d/%m/%Y %H"
    )


def test_verizon_service_get_vehicledata_on_exception_should_return_500(
    patched_setup_logger, setup_verizon_service
):
    patched_setup_logger.info.side_effect = Exception
    dataresponse = setup_verizon_service.get_vehicledata(
        msisdn="12345678901", programcode="vwcarnet"
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.INTERNALSERVERERROR


@pytest.mark.parametrize(
    "resultmessage, expected",
    mockServiceErrorTestData,
    ids=["NotFoundError", "InternalServerError"],
)
def test_verizon_service_get_vehicledata_on_serviceerror_status_should_return_expected_error(
    setup_verizon_service, patched_zeep_client, resultmessage, expected
):

    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = {
        "Response": {
            "ResponseCode": "01",
            "ResponseStatus": "Failed Execution",
            "ResponseDescription": resultmessage,
        }
    }

    dataresponse = setup_verizon_service.get_vehicledata("12345678901", "vwcarnet")
    assert type(dataresponse) == VehicleData
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.status == expected


def test_verizon_service_get_vehicledata_should_raise_exception_when_msisdn_is_not_passed(
    setup_verizon_service,
):
    try:
        dataresponse = setup_verizon_service.get_vehicledata(programcode="vwcarnet")
    except BaseException as e:
        assert (
            e.args[0]
            == "get_vehicledata() missing 1 required positional argument: 'msisdn'"
        )


def test_verizon_service_get_vehicledata_should_raise_exception_when_programcode_is_not_passed(
    setup_verizon_service,
):
    try:
        dataresponse = setup_verizon_service.get_vehicledata(msisdn="12345678901")
    except BaseException as e:
        assert (
            e.args[0]
            == "get_vehicledata() missing 1 required positional argument: 'programcode'"
        )


@mock_dynamodb2
def test_verizon_service_save_vehicledata_on_valid_inputdata_should_save_data_as_expected(
    setup_verizon_service, patched_zeep_client, mock_logger
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
    dynamotable = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    verizonservice = VerizonService(
        config=VerizonConfig(wdsl="fooWSDL", base_url="fooBaseURL"),
        table=dynamotable,
        supplementtable="fooSupplementTable",
    )
    vehicledatajson = generate_valid_verizon_data()
    headerresponse = {
        "floweventid": "7918148",
        "flowid": "528070",
        "correlationflowid": "0000NT300^E4AxwpGCl3if1VfVBt0007Zu",
    }
    verizonservice.save_vehicledata(
        "5243583607", "vwcarnet", VehicleData(**vehicledatajson), headerresponse
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
    assert result["Items"][0]["latitude"] == Decimal(0)
    assert result["Items"][0]["longitude"] == Decimal("-122.272576")
    assert result["Items"][0]["locationconfidence"] == "2"
    assert result["Items"][0]["altitude"] == "0"
    assert result["Items"][0]["timestamp"] == "2021-01-07T13:44:32.000000+0000"
    assert result["Items"][0]["headingdirection"] == "NONE"
    assert result["Items"][0]["eventid"] == "7918148"


@mock_dynamodb2
def test_verizon_service_save_vehicledata_on_different_valid_inputdata_should_save_data_as_expected(
    setup_verizon_service, patched_zeep_client, mock_logger
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
    dynamotable = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    verizonservice = VerizonService(
        config=VerizonConfig(wdsl="fooWSDL", base_url="fooBaseURL"),
        table=dynamotable,
        supplementtable="fooSupplementTable",
    )
    vehicledatajson = generate_different_valid_verizon_data()
    headerresponse = {
        "floweventid": "7918148",
        "flowid": "528070",
        "correlationflowid": "0000NT300^E4AxwpGCl3if1VfVBt0007Zu",
    }
    verizonservice.save_vehicledata(
        "5243583607", "vwcarnet", VehicleData(**vehicledatajson), headerresponse
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
    assert result["Items"][0]["latitude"] == Decimal(0)
    assert result["Items"][0]["longitude"] == Decimal("-122.272576")
    assert result["Items"][0]["locationconfidence"] == "2 meters"
    assert result["Items"][0]["altitude"] == "200 ft"
    assert result["Items"][0]["timestamp"] == "2021-01-07T13:44:32.000000+0000"
    assert result["Items"][0]["headingdirection"] == "NONE"
    assert result["Items"][0]["eventid"] == "7918148"


@mock_dynamodb2
def test_verizon_service_save_vehicledata_on_valid_input_without_headerresponse_payload_should_save_data_as_expected(
    setup_verizon_service, patched_zeep_client, mock_logger
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
    dynamotable = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    verizonservice = VerizonService(
        config=VerizonConfig(wdsl="fooWSDL", base_url="fooBaseURL"),
        table=dynamotable,
        supplementtable="fooSupplementTable",
    )
    vehicledatajson = generate_valid_verizon_data()
    verizonservice.save_vehicledata(
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
    assert result["Items"][0]["latitude"] == Decimal(0)
    assert result["Items"][0]["longitude"] == Decimal("-122.272576")
    assert result["Items"][0]["locationconfidence"] == "2"
    assert result["Items"][0]["altitude"] == "0"
    assert result["Items"][0]["timestamp"] == "2021-01-07T13:44:32.000000+0000"
    assert result["Items"][0]["headingdirection"] == "NONE"
    assert result["Items"][0]["eventid"] == "NONE"


@mock_dynamodb2
def test_verizon_service_save_vehicledata_on_invalid_inputdata_should_not_save_data_as_expected(
    mock_logger,
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
    dynamotable = get_main_table(DynamoConfig(table_name=TABLE_NAME))

    verizonservice = VerizonService(
        config=VerizonConfig(wdsl="fooWSDL", base_url="fooBaseURL"),
        table=dynamotable,
        supplementtable="fooSupplementTable",
    )

    vehicledatajson = {"any": "any"}
    headerresponse = {"any": "any"}
    verizonservice.save_vehicledata(
        "5243583607", "vwcarnet", VehicleData(**vehicledatajson), headerresponse
    )
    conn = boto3.resource("dynamodb", region_name="us-east-1")
    table = conn.Table(TABLE_NAME)
    result = table.query(
        Limit=1,
        ScanIndexForward=False,
        KeyConditionExpression=Key("request_key").eq("vwcarnet-5243583607"),
    )
    assert result["Count"] == 0


def test_verizon_service_get_vehicledata_on_exception_should_return_500(
    setup_verizon_service, patched_zeep_client
):
    patched_zeep_client.side_effect = Exception("something wrong")
    response = setup_verizon_service.get_vehicledata("5243583607", "vwcarnet")
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR
    assert response.responsemessage == "something wrong"


def test_verizon_service_get_timestamp_from_calldate_on_valid_request_should_return_calldate_timestamp():
    response = get_timestamp_from_calldate("01/07/2021", "13:44:32")
    assert response == datetime.strptime("01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S")


def test_verizon_service_get_timestamp_from_calldate_on_invalid_request_should_return_current_timestamp():
    response = get_timestamp_from_calldate("07-2021", "13:44:32")
    assert response.strftime("%d/%m/%Y %H:%M") == datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )


def test_verizon_service_get_additionaldata_from_header_on_valid_outputresponse_should_return_valid_headerresponse(
    setup_verizon_service, patched_zeep_client
):
    outputresponse = Mock(spec=Response)
    outputresponse.status_code = 200
    outputresponse.headers = {}
    outputresponse.content = b'<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    outputresponse.text = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><env:Header xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><wsa:Action>http://xmlns.hughestelematics.com/VehicleLocateEBSV1/RequestVehicleLocation</wsa:Action><wsa:MessageID>urn:44edc912-607b-11eb-a7c8-0050568556a3</wsa:MessageID><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address><wsa:ReferenceParameters><instra:tracking.ecid xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">c55c130e-b18a-41eb-a65b-f87dce76194e-00cfe0db</instra:tracking.ecid><instra:tracking.FlowEventId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">7918148</instra:tracking.FlowEventId><instra:tracking.FlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">528070</instra:tracking.FlowId><instra:tracking.CorrelationFlowId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">0000NT300^E4AxwpGCl3if1VfVBt0007Zu</instra:tracking.CorrelationFlowId><instra:tracking.quiescing.SCAEntityId xmlns:instra="http://xmlns.oracle.com/sca/tracking/1.0">832</instra:tracking.quiescing.SCAEntityId></wsa:ReferenceParameters></wsa:ReplyTo><wsa:FaultTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:FaultTo></env:Header><soap-env:Body xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><ns0:VehicleLocationResponse xmlns:ns0="http://xmlns.hughestelematics.com/VehicleLocation"><ns0:Response><ns0:ResponseCode>01</ns0:ResponseCode><ns0:ResponseStatus>Failed Execution</ns0:ResponseStatus><ns0:ResponseDescription>No data found</ns0:ResponseDescription></ns0:Response></ns0:VehicleLocationResponse></soap-env:Body></soapenv:Envelope>'
    patched_zeep_client().service.RequestVehicleLocation.return_value = outputresponse
    patched_zeep_client().service._binding.process_reply.return_value = {
        "CallDate": "01/07/2021",
        "CallTime": "13:44:32",
        "VIN": "1VWSA7A3XLC011823",
        "Make": "vw",
        "Model": "Passat",
        "VehicleYear": None,
        "CustomerFirstName": "JUSTINE",
        "CustomerLastName": "EHLERS",
        "ExteriorColor": "Pure White",
        "SRNumber": "1-13220115574",
        "FromLocationLatitude": "",
        "FromLocationLongitude": None,
        "FromLocationPhoneNo": "4258811803",
        "Response": {
            "ResponseCode": "00",
            "ResponseStatus": "Successful Execution",
            "ResponseDescription": "Data Found",
        },
    }
    response = get_additionaldata_from_header(
        setup_verizon_service, outputresponse, "5243583607", "vwcarnet"
    )
    assert response is not None
    assert response["floweventid"] == "7918148"
    assert response["flowid"] == "528070"
    assert response["correlationflowid"] == "0000NT300^E4AxwpGCl3if1VfVBt0007Zu"


def test_verizon_service_get_additionaldata_from_header_on_none_as_outputresponse_should_return_valid_headerresponse_with_none_as_string(
    setup_verizon_service, patched_zeep_client
):
    response = get_additionaldata_from_header(
        setup_verizon_service, None, "5243583607", "vwcarnet"
    )
    assert response is not None
    assert response["floweventid"] == "NONE"
    assert response["flowid"] == "NONE"
    assert response["correlationflowid"] == "NONE"


def test_verizon_serivce_health_on_success_returns_200(
    patched_rest_client, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = mocked_requests_get
    verizonservice = VerizonService(
        config=VerizonConfig(base_url="https://success"),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    response = verizonservice.health(ProgramCode.VWCARNET, CtsVersion.ONE_DOT_ZERO)
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.SUCCESS
    assert response.responsemessage == "HealthCheck passed"


def test_verizon_serivce_health_on_exception_returns_500(
    patched_rest_client, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = Exception
    verizonservice = VerizonService(
        config=VerizonConfig(base_url="https://success"),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    response = verizonservice.health(ProgramCode.VWCARNET, CtsVersion.ONE_DOT_ZERO)
    assert type(response) == VehicleData
    assert response.status == InternalStatusType.INTERNALSERVERERROR


@pytest.mark.parametrize(
    "base_url, status, message",
    [
        ("https://notfound", InternalStatusType.NOTFOUND, "File Not Found"),
        (
            "https://content_notsupported",
            InternalStatusType.INTERNALSERVERERROR,
            "Server Error",
        ),
        ("https://invalid", InternalStatusType.INTERNALSERVERERROR, "Error 500"),
    ],
)
def test_verizon_serivce_health_on_error_returns_expected_response(
    patched_rest_client,
    mock_dynamo_cv_table,
    base_url,
    status,
    message,
):
    patched_rest_client.get.side_effect = mocked_requests_get
    verizonservice = VerizonService(
        config=VerizonConfig(base_url=base_url),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    response = verizonservice.health(ProgramCode.VWCARNET, CtsVersion.ONE_DOT_ZERO)
    assert type(response) == VehicleData
    assert response.status == status
    assert response.responsemessage == message


def test_verizon_service_get_data_from_database_on_valid_input_response_should_return_valid_db_dataresponse(
    patched_rest_client, mock_dynamo_cv_table
):
    patched_rest_client.get.side_effect = mocked_requests_get
    verizonservice = VerizonService(
        config=VerizonConfig(
            base_url="https://success",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    mock_dynamo_cv_table.query.return_value = generate_valid_verizon_dbresponse()
    dataresponse = get_data_from_database(
        verizonservice,
        msisdn="12345678901",
        programcode="vwcarnet",
        ctsversion="2.0",
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.programcode == "vwcarnet"
    assert dataresponse.vin == "dbresponse_VIN"


def test_verizon_service_get_data_from_database_on_input_response_none_should_return_dataresponse_as_none(
    patched_rest_client,
    mock_dynamo_cv_table,
):
    patched_rest_client.get.side_effect = mocked_requests_get
    verizonservice = VerizonService(
        config=VerizonConfig(
            base_url="https://success",
            dynamodb_check_enable=True,
            dynamodb_check_timelimit=2,
        ),
        table=mock_dynamo_cv_table,
        supplementtable=mock_dynamo_cv_table,
    )
    mock_dynamo_cv_table.query.return_value = None
    dataresponse = get_data_from_database(
        verizonservice,
        msisdn="12345678901",
        programcode="vwcarnet",
        ctsversion="2.0",
    )
    assert dataresponse is None


def test_verizon_service_create_vehicledata_response_on_valid_input_response_should_return_valid_db_dataresponse():
    dataresponse = create_vehicledata_response(
        response=generate_valid_verizon_dbresponse()[0],
        msisdn="12345678901",
        programcode="vwcarnet",
        responsestatus=InternalStatusType.SUCCESS,
        responsemessage="Successfully retrieved",
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS


def test_verizon_service_create_vehicledata_response_on_input_response_none_should_return_dataresponse_as_none():
    dataresponse = create_vehicledata_response(
        response=None,
        msisdn="12345678901",
        programcode="vwcarnet",
        responsestatus=InternalStatusType.NOTFOUND,
        responsemessage="No data is available for msisdn: 12345678901",
    )
    assert dataresponse is None


def test_verizon_service_map_vehicledata_response_on_external_success_response_should_return_success_vehicledata_response():
    dataresponse = map_vehicledata_response(
        msisdn="12345678901",
        programcode="vwcarnet",
        response_status=InternalStatusType.SUCCESS,
        response=generete_valid_verizon_external_response(),
    )
    assert type(dataresponse) == VehicleData
    assert dataresponse.status == InternalStatusType.SUCCESS
    assert dataresponse.msisdn == "12345678901"
    assert dataresponse.calldate == "01/07/2021"
    assert dataresponse.calltime == "13:44:32"


def test_verizon_service_populate_vehicledata_with_valid_payload_populate_as_expected(
    setup_verizon_service,
):
    verizon_json = generate_valid_verizon_data()
    vehicledata = setup_verizon_service.populate_vehicledata(
        "5243583607", "vwcarnet", verizon_json
    )
    assert vehicledata.msisdn == verizon_json["msisdn"]
    assert vehicledata.latitude == verizon_json["latitude"]
    assert vehicledata.vin == verizon_json["vin"]


def test_verizon_service_populate_vehicledata_with_different_valid_payload_populate_as_expected(
    setup_verizon_service,
):
    verizon_json = generate_different_valid_verizon_data()
    vehicledata = setup_verizon_service.populate_vehicledata(
        "5243583607", "vwcarnet", verizon_json
    )
    assert vehicledata.msisdn == verizon_json["msisdn"]
    assert vehicledata.latitude == verizon_json["latitude"]
    assert vehicledata.vin == verizon_json["vin"]


@pytest.mark.parametrize(
    "invaliddata,expected", [(None, None), ("", None)], ids=[None, "Empty"]
)
def test_verizon_service_populate_vehicledata_with_invalid_data_works_as_expected(
    setup_verizon_service, invaliddata, expected
):
    vehicledata = setup_verizon_service.populate_vehicledata(
        "12345678901", "vwcarnet", invaliddata
    )
    assert vehicledata == expected


def generate_valid_verizon_data():
    return {
        "msisdn": "5243583607",
        "programcode": "vwcarnet",
        "event_datetime": 1610529816192,  # datetime.utcnow timestamp*1000
        "timestamp": datetime.strptime(
            "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
        ),  # calldate and time
        "calldate": "01/07/2021",
        "activationtype": None,
        "calltime": "13:44:32",
        "vin": "1VWSA7A3XLC011823",
        "brand": "vw",
        "modelname": "Passat",
        "modelyear": "2008",
        "modelcode": "vw",
        "modeldesc": None,
        "market": None,
        "odometer": None,
        "odometerscale": None,
        "latitude": 0,  # 37.532918
        "longitude": -122.272576,
        "headingdirection": "NONE",
        "countrycode": "US",
        "mileage": None,
        "mileageunit": None,
        "customerfirstname": "JUSTINE",
        "customerlastname": "EHLERS",
        "modelcolor": "Pure White",
        "srnumber": "1-13220115574",
        "ismoving": False,
        "cruisingrange": "385.25 Miles",
        "locationtrueness": "weak",
        "locationconfidence": 2,
        "locationaddress": "12345 TE 123th Way",
        "locationcity": "Redmond",
        "locationstate": "WA",
        "locationpostalcode": "98052-1019",
        "phonenumber": "4258811803",
        "altitude": 0,
        "language": "English",
        "status": "SUCCESS",
        "responsemessage": "response message",
    }


def generate_different_valid_verizon_data():
    return {
        "msisdn": "5243583607",
        "programcode": "vwcarnet",
        "event_datetime": 1610529816192,  # datetime.utcnow timestamp*1000
        "timestamp": datetime.strptime(
            "01/07/2021 13:44:32", "%m/%d/%Y %H:%M:%S"
        ),  # calldate and time
        "calldate": "01/07/2021",
        "activationtype": None,
        "calltime": "13:44:32",
        "vin": "1VWSA7A3XLC011823",
        "brand": "vw",
        "modelname": "Passat",
        "modelyear": "2008",
        "modelcode": "vw",
        "modeldesc": None,
        "market": None,
        "odometer": None,
        "odometerscale": None,
        "latitude": 0,  # 37.532918
        "longitude": -122.272576,
        "headingdirection": "NONE",
        "countrycode": "US",
        "mileage": None,
        "mileageunit": None,
        "customerfirstname": "JUSTINE",
        "customerlastname": "EHLERS",
        "modelcolor": "Pure White",
        "srnumber": "1-13220115574",
        "ismoving": False,
        "cruisingrange": "385.25 Miles",
        "locationtrueness": "weak",
        "locationconfidence": "2 meters",
        "locationaddress": "12345 TE 123th Way",
        "locationcity": "Redmond",
        "locationstate": "WA",
        "locationpostalcode": "98052-1019",
        "phonenumber": "4258811803",
        "altitude": "200 ft",
        "language": "English",
        "status": "SUCCESS",
        "responsemessage": "response message",
    }


def generete_valid_verizon_external_response():
    return {
        "CallDate": "01/07/2021",
        "CallTime": "13:44:32",
        "VIN": "1VWSA7A3XLC011823",
        "Make": "vw",
        "Model": "Passat",
        "VehicleYear": "2008",
        "FromLocationLatitude": "37.532918",
        "FromLocationLongitude": -122.272576,
        "Direction_heading": "North",
        "FromLocationCountry": "US",
        "CustomerFirstName": "JUSTINE",
        "CustomerLastName": "EHLERS",
        "ExteriorColor": "Pure White",
        "SRNumber": "1-13220115574",
        "Is_moving": False,
        "Cruising_range": "385.25 Miles",
        "Location_trueness": "weak",
        "Location_confidence": 2,
        "FromLocationAddress": "12345 TE 123th Way",
        "FromLocationCity": "Redmond",
        "FromLocationState": "WA",
        "FromLocationZip": "98052-1019",
        "FromLocationPhoneNo": "4258811803",
        "Altitude": 542,
        "Hmi_language": "English",
        "Response": {
            "ResponseCode": "00",
            "ResponseStatus": "Successful Execution",
            "ResponseDescription": "Data Found",
        },
    }


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
            vin="dbresponse_VIN",
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
            locationconfidence="2",
            locationaddress="12345 TE 123th Way",
            locationcity="Redmond",
            locationstate="WA",
            locationpostalcode="98052-1019",
            phonenumber="4258811803",
            altitude="0",
            language="English",
        )
    ]

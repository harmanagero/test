from unittest.mock import patch

import pytest
from src.aeris.models.domain.vehicle_data import VehicleData as AerisVehicleData
from src.api.api import app, save_msisdn_error
from src.fca.models.data.vehicle_data import VehicleData as FcaVehicleData
from src.fca.models.domain.terminate import Terminate
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.odometerscale_type import OdometerScaleType
from src.models.enums.programcode_type import ProgramCode
from src.siriusxm.models.data.vehicle_data import VehicleData as SiriusXmVehicleData
from src.verizon.models.data.vehicle_data import VehicleData as VerizonVehicleData
from src.vodafone.models.data.vehicle_data import VehicleData as VodafoneVehicleData
from src.vodafone.models.data.vehicle_info import VehicleInfo
from starlette.testclient import TestClient


@pytest.fixture
def patched_setupservicemanager():
    with patch("src.api.api.setup_service_manager") as patched_service:
        yield patched_service


@pytest.fixture
def patched_setuplogger():
    with patch("src.api.api.logger") as patched_logger:
        yield patched_logger


@pytest.fixture
def patched_agentassignment_response():
    with patch("src.api.api.AgentAssignment") as agentassignment_response:
        yield agentassignment_response


@pytest.fixture
def patched_terminate_response():
    with patch("src.api.api.Terminate") as mocked_response:
        yield mocked_response


@pytest.fixture
def patched_getvehicledata_response():
    with patch("src.api.api.GetVehicleDataResponse") as mocked_response:
        yield mocked_response


internalservererrorjson = {
    "code": "InternalServerError",
    "detail": "something wrong",
    "status": "500",
    "title": "Internal Server Error",
}
badrequestjson = {
    "code": "BadRequest",
    "detail": "something wrong",
    "status": "400",
    "title": "Bad Request",
}
badrequestdetailjson = {
    "code": "BadRequest",
    "status": "400",
    "title": "Bad Request",
    "detail": {
        "location": ["body", "referenceid"],
        "message": "ReferenceId cannot be null or empty",
        "type": "value_error",
    },
}
notfoundexceptionjson = {
    "code": "NotFound",
    "detail": "something wrong",
    "status": "404",
    "title": "Not Found",
}
forbiddenerrorjson = {
    "code": "ForbiddenError",
    "detail": "something wrong",
    "status": "403",
    "title": "Forbidden Error",
}

testerrorstatus = [
    (InternalStatusType.FORBIDDEN, forbiddenerrorjson),
    (InternalStatusType.NOTFOUND, notfoundexceptionjson),
    (InternalStatusType.BADREQUEST, badrequestjson),
    (InternalStatusType.INTERNALSERVERERROR, internalservererrorjson),
    (InternalStatusType.UNKNOWN, internalservererrorjson),
]


testbadrequestdata = [(InternalStatusType.BADREQUEST, badrequestdetailjson)]


@pytest.fixture
def client():
    # extremely basic but this is a good place
    # to stage / setup a database for a test run.
    client = TestClient(app)
    yield client


def test_ping(client):
    response = client.get("/health")
    assert response.status_code == 200
    parsed = response.json()
    assert parsed["data"]["success"]
    assert parsed["data"]["responsemessage"] == "HealthCheck passed"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_create_agentassignment_on_success_should_return_201(
    client, patched_setupservicemanager, programcode, patched_agentassignment_response
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    patched_agentassignment_response().response_referenceid = "TESTREFERENCEID"
    patched_agentassignment_response().isassigned = True
    patched_agentassignment_response().responsestatus = "SUCCESS"
    response = client.post(
        "/agentassignment",
        json=dict(
            referenceid="TESTREFERENCEID", isassigned=True, programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["data"]["agent_assigned"]
    assert parsed["data"]["status"] == "201"
    assert parsed["data"]["reference_id"] == "TESTREFERENCEID"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize("statustype, expected", testbadrequestdata, ids=["BadRequest"])
def test_create_agentassignment_on_badrequest_error_status_should_return_expected_error(
    client,
    programcode,
    statustype,
    expected,
    patched_setupservicemanager,
    patched_agentassignment_response,
):
    patched_setupservicemanager().client_service.assign_agent.return_value = False
    patched_agentassignment_response().referenceid = ""
    patched_agentassignment_response().programcode = programcode
    patched_agentassignment_response().response_referenceid = "TESTREFERENCEID"
    patched_agentassignment_response().isassigned = True
    patched_agentassignment_response().responsestatus = statustype
    patched_agentassignment_response().responsemessage = "something wrong"
    response = client.post(
        "/agentassignment",
        json=dict(referenceid="", isassigned=True, programcode=programcode),
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=["ForbiddenError", "NotFound", "BadRequest", "InternalServerError", "Unknown"],
)
def test_create_agentassignment_on_different_error_status_should_return_expected_error(
    client,
    programcode,
    statustype,
    expected,
    patched_setupservicemanager,
    patched_agentassignment_response,
):
    patched_setupservicemanager().client_service.assign_agent.return_value = False
    patched_agentassignment_response().referenceid = "TESTREFERENCEID"
    patched_agentassignment_response().programcode = programcode
    patched_agentassignment_response().response_referenceid = "TESTREFERENCEID"
    patched_agentassignment_response().isassigned = True
    patched_agentassignment_response().responsestatus = statustype
    patched_agentassignment_response().responsemessage = "something wrong"
    response = client.post(
        "/agentassignment",
        json=dict(
            referenceid="TESTREFERENCEID", isassigned=True, programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "programcode", ["nissannn", "infinitiii"], ids=["Nissan", "Infiniti"]
)
def test_create_agentassignment_with_invalid_program_code_should_return_400(
    client, patched_setupservicemanager, patched_agentassignment_response, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = False
    response = client.post(
        "/agentassignment",
        json=dict(
            referenceid="TESTREFERENCEID", isassigned=False, programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize("isassigned", ["", "3"])
def test_create_agentassignment_with_invalid_isassigned_should_return_400(
    client, patched_setupservicemanager, isassigned, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = False
    response = client.post(
        "/agentassignment",
        json=dict(
            referenceid="TESTREFERENCEID",
            isassigned=isassigned,
            programcode=programcode,
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_create_agentassignment_with_missing_referenceid_should_return_400(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/agentassignment", json=dict(isassigned=True, programcode=programcode)
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_create_agentassignment_with_missing_isassigned_should_return_400(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/agentassignment",
        json=dict(referenceid="TESTREFERENCEID", programcode=programcode),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


def test_create_agentassignment_with_missing_programcode_should_return_400(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/agentassignment", json=dict(referenceid="TESTREFERENCEID", isassigned=True)
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize("reference_id", [None, ""])
def test_create_agentassignment_on_referenceid_null_or_empty_should_return_400(
    client, patched_setupservicemanager, reference_id, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/agentassignment",
        json=dict(referenceid=reference_id, isassigned=True, programcode=programcode),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_create_agentassignment_with_empty_isassigned_should_return_400(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/agentassignment",
        json=dict(
            referenceid="TESTREFERENCEID", isassigned="", programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize("programcode", ["", ""], ids=["Nissan", "Infiniti"])
def test_create_agentassignment_with_empty_programcode_should_return_400(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/agentassignment",
        json=dict(
            referenceid="TESTREFERENCEID", isassigned=True, programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_create_terminate_on_success_should_return_201(
    client, programcode, patched_setupservicemanager, patched_terminate_response
):
    patched_setupservicemanager().client_service.terminate.return_value = True
    patched_terminate_response().response_referenceid = "TESTREFERENCEID"
    patched_terminate_response().status = "SUCCESS"
    response = client.post(
        "/terminate",
        json=dict(
            referenceid="TESTREFERENCEID", reasoncode="", programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "201"
    assert parsed["data"]["reference_id"] == "TESTREFERENCEID"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_create_terminate_on_different_error_status_should_return_expected_error(
    client,
    programcode,
    statustype,
    expected,
    patched_setupservicemanager,
    patched_terminate_response,
):
    patched_setupservicemanager().client_service.terminate.return_value = False
    patched_terminate_response().referenceid = "TESTREFERENCEID"
    patched_terminate_response().responsemessage = "something wrong"
    patched_terminate_response().status = statustype
    response = client.post(
        "/terminate",
        json=dict(
            referenceid="TESTREFERENCEID", reasoncode="", programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "programcode", ["nissann", "infinityi"], ids=["Nissan", "Infiniti"]
)
def test_create_terminate_invalid_program_code_should_return_400(client, programcode):
    response = client.post(
        "/terminate",
        json=dict(
            referenceid="TESTREFERENCEID", reasoncode="", programcode=programcode
        ),
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


def test_create_terminate_with_missing_programcode_should_return_400(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.assign_agent.return_value = True
    response = client.post(
        "/terminate", json=dict(referenceid="TESTREFERENCEID", reasoncode="abc")
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_create_terminate_missing_referenceid_should_return_400(client, programcode):
    response = client.post("/terminate", json=dict(programcode=programcode))
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize("reference_id", [None, ""])
def test_create_terminate_on_referenceid_null_or_empty_should_return_400(
    client, programcode, patched_setupservicemanager, reference_id
):
    patched_setupservicemanager().client_service.terminate.return_value = False
    response = client.post(
        "/terminate", json=dict(referenceid=reference_id, programcode=programcode)
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


def test_save_vehicledata_on_json_body_none_should_return_400_badrequest(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = False
    response = client.post("/data", json=None)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize("empty_payload", ["{}", "[]"])
def test_save_vehicledata_on_json_body_different_empty_values_should_return_400(
    client, empty_payload, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = False
    response = client.post("/data", empty_payload)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert (
        "SaveVehicleData: Json payload is invalid. Payload requires programcode and referenceid"
        in parsed["errors"][0]["detail"]
    )


def test_save_vehicledata_with_proper_data_should_return_status_201_created(
    client, patched_setupservicemanager
):
    vehicledata = generate_valid_cv_data()
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        generate_hex_data()
    )

    response = client.post("/data", json=vehicledata)
    parsed = response.json()
    assert parsed[0]["VarName"] == "User-to-User"
    assert (
        parsed[0]["Value"]
        == "00524f4144534944457e34333534333534337e34322e3430367e2d37312e303734327e313233343536373839307e656e"
    )


def test_get_vehicledata_with_invalid_input_data_should_return_400_badrequest(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.get_vehicledata.return_value = False
    response = client.get("/data/TESTREFERENCEID/programcode/infinitt", json=None)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_get_vehicledata_with_proper_data_should_return_status_200_success(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.get_vehicledata.return_value = (
        generate_get_vehicledata(programcode)
    )
    response = client.get("/data/TESTREFERENCE/programcode/" + programcode)
    parsed = response.json()
    assert parsed["data"]["status"] == "200"
    assert parsed["data"]["header"]["referenceid"] == "TESTREFERENCE"
    assert parsed["data"]["header"]["calldate"] == "2020-10-28"
    assert parsed["data"]["header"]["calltime"] == "18:54"
    assert parsed["data"]["header"]["timestamp"] == "2020-10-28T18:54:00"
    assert parsed["data"]["header"]["programcode"] == programcode


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_get_vehicledata_on_different_error_status_should_return_expected_error(
    client, patched_setupservicemanager, statustype, expected, programcode
):
    vehicle_model = SiriusXmVehicleData(
        status=statustype, responsemessage="something wrong"
    )
    patched_setupservicemanager().client_service.get_vehicledata.return_value = (
        vehicle_model
    )
    response = client.get("/data/TESTREFERENCEID/programcode/" + programcode)

    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_get_vehicledata_with_no_referenceid_or_invalid_path_should_return_404(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.get_vehicledata.return_value = (
        generate_get_vehicledata(programcode)
    )
    response = client.get("/data//programcode/" + programcode)

    parsed = response.json()
    assert parsed["errors"][0]["status"] == "404"
    assert parsed["errors"][0]["detail"] == "Missing Resource URI"
    assert parsed["errors"][0]["code"] == "NotFound"
    assert parsed["errors"][0]["title"] == "Not Found"


@pytest.mark.parametrize(
    "msisdn,expectedmsg",
    [
        ("None", "Msisdn cannot be null or empty"),
        (None, "Msisdn cannot be null or empty"),
        ("-", "Msisdn cannot be null or empty"),
        ("123456789", "Msisdn character length should be minimum 10 digit numbers"),
        ("1a2B3c4D5f6", "Msisdn has non numeric characters"),
    ],
    ids=[
        "NoneString",
        "None",
        "HypenReplacedAsEmpty",
        "NineDigitNumbers",
        "NonNumeric",
    ],
)
@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("vwcarnet", "1.0"), ("porsche", "1.0")],
    ids=["Aeris", "FCA", "Verizon", "Vodafone"],
)
def test_getvehicledata_with_invalid_msisdn_input_should_return_400_badrequest(
    client, msisdn, programcode, ctsversion, expectedmsg
):
    response = client.get(
        "/data/{}/programcode/{}/ctsversion/{}".format(msisdn, programcode, ctsversion),
        json=None,
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert expectedmsg in parsed["errors"][0]["detail"]["message"]


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnett", "2.0"), ("fcaa", "1.0"), ("vwcarnett", "1.0"), ("poorsche", "1.0")],
    ids=["Aeris", "FCA", "Verizon", "Vodafone"],
)
def test_getvehicledata_with_invalid_programcode_input_should_return_400_badrequest_with_permitted_values(
    client, programcode, ctsversion
):
    response = client.get(
        "/data/TESTREFERENCEID/programcode/{}/ctsversion/{}".format(
            programcode, ctsversion
        ),
        json=None,
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert (
        "value is not a valid enumeration member; permitted: 'nissan', 'infiniti', 'fca', 'vwcarnet'"
        in parsed["errors"][0]["detail"]["message"]
    )


@pytest.mark.parametrize(
    "ctsversion",
    [None, " ", "1_0", "2", "3.0", "one"],
    ids=["None", "Empty", "1_0", "2", "3.0", "One"],
)
@pytest.mark.parametrize("programcode", ["vwcarnet", "fca", "porsche"])
def test_getvehicledata_with_invalid_ctsversion_input_should_return_400_badrequest_with_permitted_values(
    client, programcode, ctsversion
):
    response = client.get(
        "/data/TESTREFERENCEID/programcode/{}/ctsversion/{}".format(
            programcode, ctsversion
        ),
        json=None,
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert (
        "value is not a valid enumeration member; permitted: '1.0', '2.0'"
        in parsed["errors"][0]["detail"]["message"]
    )


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("porsche", "1.0")],
    ids=["Aeris", "FCA", "Vodafone"],
)
def test_getvehicledata_with_valid_input_should_return_status_200_success(
    client, patched_setupservicemanager, programcode, ctsversion
):
    patched_setupservicemanager().client_service.get_vehicledata.return_value = (
        mock_valid_dataresponse(programcode, ctsversion)
    )
    response = client.get(
        "/data/5243583607/programcode/{}/ctsversion/{}".format(programcode, ctsversion),
        json=None,
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "200"
    assert parsed["data"]["responsemessage"] == "Successfully retrieved"
    assert parsed["data"]["header"]["msisdn"] == "5243583607"
    assert parsed["data"]["header"]["programcode"] == programcode
    assert parsed["data"]["header"]["timestamp"] == "2020-09-25T19:05:00"
    assert parsed["data"]["header"]["version"] == ctsversion
    assert parsed["data"]["header"]["calldate"] == "2020-09-25"
    assert parsed["data"]["location"]["latitude"] == 37.532918
    assert parsed["data"]["location"]["longitude"] == -122.272576
    assert parsed["data"]["vehicle"]["vin"] == "1VWSA7A3XLC011823"
    if programcode == "porsche":
        assert parsed["data"]["vehicle"]["mileage"] == 0
        assert parsed["data"]["vehicle"]["mileageunit"] == "Miles"
        assert parsed["data"]["vehicle"]["brand"]["brandname"] == "PORSCHE"
    else:
        assert parsed["data"]["header"]["odometer"] == 16114
        assert parsed["data"]["header"]["odometerscale"] == OdometerScaleType.KILOMETERS
        assert parsed["data"]["vehicle"]["brand"]["brandname"] == "VW"
        assert parsed["data"]["vehicle"]["brand"]["modelname"] == "Passat"
        assert parsed["data"]["vehicle"]["mileage"] == None
        assert parsed["data"]["vehicle"]["mileageunit"] == None


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("vwcarnet", "1.0"), ("porsche", "1.0")],
    ids=["Aeris", "FCA", "Verizon", "Vodafone"],
)
@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_get_vehicledata_on_different_error_status_should_return_expected_exception(
    client,
    patched_setupservicemanager,
    statustype,
    expected,
    programcode,
    ctsversion,
    patched_setuplogger,
):
    mockdata = None
    if programcode == ProgramCode.FCA:
        mockdata = FcaVehicleData(status=statustype, responsemessage="something wrong")
    if programcode == ProgramCode.VWCARNET and ctsversion == CtsVersion.ONE_DOT_ZERO:
        mockdata = VerizonVehicleData(
            status=statustype, responsemessage="something wrong"
        )
    if programcode == ProgramCode.VWCARNET and ctsversion == CtsVersion.TWO_DOT_ZERO:
        mockdata = AerisVehicleData(
            status=statustype, responsemessage="something wrong"
        )
    else:
        mockdata = SiriusXmVehicleData(
            status=statustype, responsemessage="something wrong"
        )
    if programcode == ProgramCode.PORSCHE and ctsversion == CtsVersion.ONE_DOT_ZERO:
        mockdata = VodafoneVehicleData(
            status=statustype, responsemessage="something wrong"
        )
    patched_setupservicemanager().client_service.get_vehicledata.return_value = mockdata
    response = client.get(
        "/data/5243583607/programcode/{}/ctsversion/{}".format(programcode, ctsversion)
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected
    assert patched_setuplogger.error.called


@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_save_vehicledata_on_different_error_status_should_return_expected_exception(
    client, patched_setupservicemanager, statustype, expected
):
    vehicledata = generate_valid_cv_data()
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        SiriusXmVehicleData(
            referenceid="TESTREFERENCEID",
            status=statustype,
            responsemessage="something wrong",
            programcode="nissan",
        )
    )
    response = client.post("/data", json=vehicledata)
    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("vwcarnet", "1.0"), ("porsche", "1.0")],
    ids=["Aeris", "FCA", "Verizon", "Vodafone"],
)
def test_getvehicledata_with_no_msisdn_or_invalid_path_should_return_404(
    client, patched_setupservicemanager, programcode, ctsversion
):
    patched_setupservicemanager().client_service.get_vehicledata.return_value = (
        mock_valid_dataresponse(programcode, ctsversion)
    )
    response = client.get(
        "/data//programcode/{}/ctsversion/{}".format(programcode, ctsversion), json=None
    )
    parsed = response.json()
    assert parsed["errors"][0]["status"] == "404"
    assert parsed["errors"][0]["detail"] == "Missing Resource URI"
    assert parsed["errors"][0]["code"] == "NotFound"
    assert parsed["errors"][0]["title"] == "Not Found"


@pytest.mark.parametrize("programcode", ["fca", "toyota"])
def test_terminate_with_ctsversion_on_success_should_return_201(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.terminate.return_value = Terminate(
        msisdn="TESTMSISDN", status="SUCCESS"
    )
    response = client.post(
        "/terminate/TESTMSISDN/programcode/{}/ctsversion/1.0".format(programcode),
        json={"payload": "any"},
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "201"
    assert parsed["data"]["msisdn"] == "TESTMSISDN"


@pytest.mark.parametrize("empty_payload", ["{}", "[]"])
@pytest.mark.parametrize("programcode", ["fca", "toyota"])
def test_terminate_with_ctsversion_on_json_body_different_empty_values_should_return_400(
    client, empty_payload, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.terminate.return_value = Terminate(
        msisdn="TESTMSISDN", status="BAD_REQUEST"
    )

    response = client.post(
        "/terminate/TESTMSISDN/programcode/{}/ctsversion/1.0".format(programcode),
        empty_payload,
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


def test_terminate_with_ctsversion_on_invalid_program_code_should_return_400(client):
    response = client.post(
        "/terminate/msisdn/programcode/fcaa/ctsversion/1.0", json=None
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize("programcode", ["fca", "toyota"])
def test_terminate_with_ctsversion_on_invalid_version_should_return_400(
    client, programcode
):
    response = client.post(
        "/terminate/msisdn/programcode/{}/ctsversion/3".format(programcode), json=None
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize("programcode", ["fca", "toyota"])
def test_terminate_with_ctsversion_on_msisdn_missing_should_return_404(
    client, programcode
):
    response = client.post(
        "/terminate//programcode/{}/ctsversion/1.0".format(programcode), json=None
    )
    parsed = response.json()
    # path param none won't hit the resource itself
    assert parsed["errors"][0]["code"] == "NotFound"
    assert parsed["errors"][0]["status"] == "404"
    assert parsed["errors"][0]["detail"] == "Missing Resource URI"


@pytest.mark.parametrize("programcode", ["fca", "toyota"])
@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_terminate_with_ctsversion_on_different_error_status_should_return_expected_error(
    client, statustype, expected, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.terminate.return_value = Terminate(
        msisdn="TESTMSISDN", status=statustype, responsemessage="something wrong"
    )

    response = client.post(
        "/terminate/TESTMSISDN/programcode/{}/ctsversion/1.0".format(programcode),
        json={"payload": "any"},
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


def test_save_vehicledata_fca_with_ctsversion_on_success_should_return_201(
    client, patched_setupservicemanager
):
    # Input Request json includes None, False, ''
    vehicledata = save_data_request_json()
    patched_setupservicemanager().client_service.save_vehicledata.return_value = FcaVehicleData(
        msisdn="12345678901",
        status="SUCCESS",
        responsemessage="Successfully saved the vehicledata for msisdn: 12345678901",
    )
    response = client.post(
        "/data/12345678901/programcode/fca/ctsversion/1.0",
        json=vehicledata,
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "201"
    assert parsed["data"]["msisdn"] == "12345678901"
    assert (
        parsed["data"]["responsemessage"]
        == "Successfully saved the vehicledata for msisdn: 12345678901"
    )


def test_save_vehicledata_fca_with_ctsversion_on_json_body_none_should_return_400(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        FcaVehicleData(msisdn="TESTMSISDN", status="SUCCESS")
    )
    response = client.post("/data/TESTMSISDN/programcode/fca/ctsversion/1.0", json=None)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert "field required" in parsed["errors"][0]["detail"]["message"]


@pytest.mark.parametrize("empty_payload", ["{}", "[]"])
def test_save_vehicledata_fca_with_ctsversion_on_json_body_different_empty_values_should_return_400(
    client, empty_payload, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = FcaVehicleData(
        msisdn="TESTMSISDN",
        status="BAD_REQUEST",
        responsemessage="SaveVehicleData: Json payload is invalid for msisdn: TESTMSISDN",
    )
    response = client.post(
        "/data/TESTMSISDN/programcode/fca/ctsversion/1.0", empty_payload
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert (
        "SaveVehicleData: Json payload is invalid for msisdn: TESTMSISDN"
        in parsed["errors"][0]["detail"]
    )


@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_save_vehicledata_fca_with_ctsversion_on_different_error_status_should_return_expected_error(
    client,
    statustype,
    expected,
    patched_setupservicemanager,
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        FcaVehicleData(
            msisdn="TESTMSISDN",
            status=statustype,
            responsemessage="something wrong",
        )
    )
    response = client.post(
        "/data/TESTMSISDN/programcode/fca/ctsversion/1.0",
        json={"some": "any"},
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


def test_save_vehicledata_porsche_with_ctsversion_on_success_should_return_201(
    client, patched_setupservicemanager
):
    vehicledata = porsche_valid_json()
    patched_setupservicemanager().client_service.save_vehicledata.return_value = VodafoneVehicleData(
        msisdn="12345678901",
        status="SUCCESS",
        responsemessage="Successfully saved the vehicledata for msisdn: 12345678901",
    )

    response = client.post(
        "/data/12345678901/programcode/porsche/ctsversion/1.0",
        json=vehicledata,
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "201"
    assert parsed["data"]["msisdn"] == "12345678901"
    assert (
        parsed["data"]["responsemessage"]
        == "Successfully saved the vehicledata for msisdn: 12345678901"
    )


def test_save_vehicledata_porsche_with_ctsversion_on_json_body_none_should_return_400(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(msisdn="TESTMSISDN", status="SUCCESS")
    )
    response = client.post(
        "/data/TESTMSISDN/programcode/porsche/ctsversion/1.0", json=None
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert "field required" in parsed["errors"][0]["detail"]["message"]


@pytest.mark.parametrize("empty_payload", ["{}", "[]"])
def test_save_vehicledata_porsche_with_ctsversion_on_json_body_different_empty_values_should_return_400(
    client, empty_payload, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = VodafoneVehicleData(
        msisdn="TESTMSISDN",
        status="BAD_REQUEST",
        responsemessage="SaveVehicleData: Json payload is invalid for msisdn: TESTMSISDN",
    )
    response = client.post(
        "/data/TESTMSISDN/programcode/porsche/ctsversion/1.0", empty_payload
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert (
        "SaveVehicleData: Json payload is invalid for msisdn: TESTMSISDN"
        in parsed["errors"][0]["detail"]
    )


@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_save_vehicledata_porsche_with_ctsversion_on_different_error_status_should_return_expected_error(
    client,
    statustype,
    expected,
    patched_setupservicemanager,
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(
            msisdn="TESTMSISDN",
            status=statustype,
            responsemessage="something wrong",
        )
    )
    response = client.post(
        "/data/TESTMSISDN/programcode/porsche/ctsversion/1.0",
        json={"some": "any"},
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize("programcode", ["fca", "porsche"])
def test_save_vehicledata_with_ctsversion_on_invalid_program_code_should_return_400(
    client, programcode
):
    response = client.post(
        "/data/msisdn/programcode/invalidprogram/ctsversion/1.0", json=None
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize("programcode", ["fca", "porsche"])
def test_save_vehicledata_with_ctsversion_on_invalid_version_should_return_400(
    client, programcode
):
    response = client.post(
        "/data/msisdn/programcode/{}/ctsversion/3".format(programcode), json=None
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize("programcode", ["fca", "porsche"])
def test_save_vehicledata_with_ctsversion_on_msisdn_missing_should_return_404(
    client, programcode
):
    response = client.post(
        "/data//programcode/{}/ctsversion/1.0".format(programcode), json=None
    )
    parsed = response.json()
    # path param none won't hit the resource itself
    assert parsed["errors"][0]["code"] == "NotFound"
    assert parsed["errors"][0]["status"] == "404"
    assert parsed["errors"][0]["detail"] == "Missing Resource URI"


def test_save_vehicleinfo_porsche_on_success_should_return_200(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = VodafoneVehicleData(
        msisdn="12345678901",
        status="SUCCESS",
        responsemessage="Successfully saved the vehicledata for msisdn: 12345678901",
    )
    response = client.post(
        "/vehicleinfo",
        json=porsche_valid_json(),
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "200"
    assert parsed["data"]["msisdn"] == "12345678901"
    assert (
        parsed["data"]["responsemessage"]
        == "Successfully saved the vehicledata for msisdn: 12345678901"
    )


@pytest.mark.parametrize(
    "input_msisdn",
    [
        "2345678901",
        "+12345678901",
        "+1234-567-8901",
        "+2345678901",
        "+234-567-8901",
    ],
)
def test_save_vehicleinfo_porsche_format_msisdn_as_expected(
    client, patched_setupservicemanager, input_msisdn
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(
            status="SUCCESS",
        )
    )
    payload = {"userData": {"phoneContact": ""}}
    payload["userData"]["phoneContact"] = input_msisdn
    response = client.post(
        "/vehicleinfo",
        json=payload,
    )
    parsed = response.json()
    assert parsed["data"]["status"] == "200"
    assert parsed["data"]["msisdn"] == "12345678901"


def test_save_vehicleinfo_porsche_on_json_body_none_should_return_400(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(msisdn="TESTMSISDN", status="SUCCESS")
    )
    response = client.post("/vehicleinfo", json=None)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert "field required" in parsed["errors"][0]["detail"]["message"]


@pytest.mark.parametrize("empty_payload", ["{}", "[]"])
def test_save_vehicleinfo_porsche_on_json_body_different_empty_values_should_return_400(
    client, empty_payload, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(msisdn="TESTMSISDN", status="BAD_REQUEST")
    )
    response = client.post("/vehicleinfo", empty_payload)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


@pytest.mark.parametrize(
    "payload", [{}, {"userData": {}}, {"userData": {"phoneContact": None}}]
)
def test_save_vehicleinfo_porsche_on_invalid_payload_should_return_404(client, payload):
    response = client.post("/vehicleinfo", json=payload)
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert parsed["errors"][0]["detail"] == "Missing PhoneContact/Msisdn"


@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_save_vehicleinfo_porsche_on_different_error_status_should_return_expected_error(
    client, statustype, expected, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(
            msisdn="TESTMSISDN", status=statustype, responsemessage="something wrong"
        )
    )

    response = client.post(
        "/vehicleinfo",
        json=porsche_valid_json(),
    )
    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "statustype, expected_errorcode",
    (
        [
            (InternalStatusType.FORBIDDEN, 403),
            (InternalStatusType.NOTFOUND, 404),
            (InternalStatusType.BADREQUEST, 400),
            (InternalStatusType.INTERNALSERVERERROR, 500),
            (InternalStatusType.UNKNOWN, 500),
        ]
    ),
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_save_msisdn_error_porsche_on_different_error_status_should_return_expected_error(
    statustype, expected_errorcode, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.save_vehicledata.return_value = (
        VodafoneVehicleData(
            msisdn="TESTMSISDN", status=statustype, responsemessage="something wrong"
        )
    )

    exceptiontype = save_msisdn_error(
        statustype, "something wrong", "TESTMSISDN", "porsche", "1.0"
    )
    assert exceptiontype.status_code == expected_errorcode
    assert exceptiontype.detail == "something wrong"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_health_on_success_should_return_200(
    client, patched_setupservicemanager, programcode
):
    patched_setupservicemanager().client_service.health.return_value = (
        SiriusXmVehicleData(
            status=InternalStatusType.SUCCESS, responsemessage="HealthCheck passed"
        )
    )
    response = client.get(
        "/health/programcode/{programcode}/ctsversion/1.0".format(
            programcode=programcode
        )
    )
    parsed = response.json()
    assert parsed["data"]["success"]
    assert parsed["data"]["responsemessage"] == "HealthCheck passed"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_health_on_different_error_status_should_return_expected_error(
    client, patched_setupservicemanager, statustype, expected, programcode
):
    vehicle_model = SiriusXmVehicleData(
        status=statustype, responsemessage="something wrong"
    )
    patched_setupservicemanager().client_service.health.return_value = vehicle_model
    response = client.get(
        "/health/programcode/{programcode}/ctsversion/1.0".format(
            programcode=programcode
        )
    )

    parsed = response.json()
    assert parsed["errors"][0] == expected


@pytest.mark.parametrize(
    "request_suffix",
    [
        "/health/programcode/invalid/ctsversion/1.0",
        "/health/programcode/nissan/ctsversion/1*0",
    ],
)
def test_health_with_invalid_programcode_or_ctsversion_should_return_400(
    client, patched_setupservicemanager, request_suffix
):
    response = client.get(request_suffix)

    parsed = response.json()
    assert parsed["errors"][0]["status"] == "400"
    assert parsed["errors"][0]["code"] == "BadRequest"


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti", "toyota"], ids=["Nissan", "Infiniti", "Toyota"]
)
def test_health_with_invalid_path_should_return_404(
    client, patched_setupservicemanager, programcode
):
    response = client.get("/health/programcode/" + programcode)

    parsed = response.json()
    assert parsed["errors"][0]["status"] == "404"
    assert parsed["errors"][0]["detail"] == "Missing Resource URI"
    assert parsed["errors"][0]["code"] == "NotFound"
    assert parsed["errors"][0]["title"] == "Not Found"



def test_get_vehicleinfo_with_invalid_input_data_should_return_400_badrequest(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.get_vehicleinfo.return_value = False
    response = client.get("/vehicleinfo?phnecontact=123")
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"


def test_get_vehicleinfo_with_proper_data_should_return_status_200_success(
    client, patched_setupservicemanager
):
    patched_setupservicemanager().client_service.get_vehicleinfo.return_value = (
        generate_get_vehicleinfo("porsche")
    )
    response = client.get("/vehicleinfo?phonecontact=+12345678901")
    assert response.json() == porsche_valid_json()


@pytest.mark.parametrize(
    "statustype, expected",
    testerrorstatus,
    ids=[
        "ForbiddenError",
        "NotFound",
        "BadRequest",
        "InternalServerError",
        "UnknownStatus",
    ],
)
def test_get_vehicleinfo_on_different_error_status_should_return_expected_error(
    client, patched_setupservicemanager, statustype, expected
):
    vehicle_model = VehicleInfo(
        status=statustype, responsemessage="something wrong"
    )
    patched_setupservicemanager().client_service.get_vehicleinfo.return_value = (
        vehicle_model
    )
    response = client.get("/vehicleinfo?phonecontact=+12345678901")

    parsed = response.json()
    assert parsed["errors"][0] == expected


def test_get_vehicleinfo_with_invalid_path_should_return_404(
    client, patched_setupservicemanager
):
    
    response = client.get("/vehicleinf")

    parsed = response.json()
    assert parsed["errors"][0]["status"] == "404"
    assert parsed["errors"][0]["detail"] == "Missing Resource URI"
    assert parsed["errors"][0]["code"] == "NotFound"
    assert parsed["errors"][0]["title"] == "Not Found"


@pytest.mark.parametrize(
    "msisdn,expectedmsg",
    [
        ("None", "Msisdn cannot be null or empty"),
        (None, "Msisdn cannot be null or empty"),
        ("-", "Msisdn cannot be null or empty"),
        ("123456789", "Msisdn character length should be minimum 10 digit numbers"),
        ("1a2B3c4D5f6", "Msisdn has non numeric characters"),
    ],
    ids=[
        "NoneString",
        "None",
        "HypenReplacedAsEmpty",
        "NineDigitNumbers",
        "NonNumeric",
    ],
)
def test_getvehicleinfo_with_invalid_msisdn_should_return_400_badrequest(
    client, msisdn, expectedmsg
):
    response = client.get(
        "/vehicleinfo?phonecontact={}".format(msisdn)
    )
    parsed = response.json()
    assert parsed["errors"][0]["code"] == "BadRequest"
    assert parsed["errors"][0]["status"] == "400"
    assert expectedmsg in parsed["errors"][0]["detail"]["message"]





def generate_hex_data():
    return SiriusXmVehicleData(
        status=InternalStatusType.SUCCESS,
        programcode="nissan",
        referenceid="TESTREFERENCE",
        hexvehicledata={
            "VarName": "User-to-User",
            "Value": "00524f4144534944457e34333534333534337e34322e3430367e2d37312e303734327e313233343536373839307e656e",
        },
        language=None,
        longitude="-71.0742",
        latitude="42.406",
        vin="TESTVIN",
    )


def generate_valid_cv_data():
    return {
        "request_key": "nissan-TESTREFERENCE",
        "programcode": "nissan",
        "language": None,
        "referenceid": "TESTREFERENCE",
        "geolocation": "42.406~-71.0742~400;enc-param=token",
        "vin": "TESTVIN",
    }


def generate_get_vehicledata(programcode):
    return SiriusXmVehicleData(
        status=InternalStatusType.SUCCESS,
        programcode=programcode,
        language="en",
        referenceid="TESTREFERENCE",
        latitude="42.406",
        longitude="-71.0742",
        vin="TESTVIN",
        timestamp="2020-10-28T18:54:00.000000",
        event_datetime="1603911241022",  # 2020-10-28 18:54
        calldate="2020-10-28",
        calltime="18:54",
    )


def generate_get_vehicleinfo(programcode):
    return VehicleInfo(
        status=InternalStatusType.SUCCESS,
        programcode=programcode,
        responsemessage="retrieved successfully",
        JSONData=porsche_valid_json(),
    )


def mock_valid_dataresponse(programcode, ctsversion):
    if (
        programcode
        and programcode.lower() == ProgramCode.FCA.name.lower()
        and ctsversion == CtsVersion.ONE_DOT_ZERO
    ):
        return FcaVehicleData(
            msisdn="5243583607",
            programcode=programcode,
            calldate="2020-09-25",
            calltime="19:05",
            timestamp="2020-09-25T19:05:00.000000",
            event_datetime="1603911241022",
            countrycode="US",
            vin="1VWSA7A3XLC011823",
            brand="VW",
            modelname="Passat",
            modelyear="2008",
            modelcode="A342P6",
            modeldesc="Passat_2008",
            odometer=16114,
            odometerscale=OdometerScaleType.KILOMETERS,
            latitude=37.532918,
            longitude=-122.272576,
            headingdirection="NORTH EAST",
            status="SUCCESS",
            responsemessage="Successfully retrieved",
        )

    if (
        programcode
        and programcode.lower() == ProgramCode.VWCARNET.name.lower()
        and ctsversion == CtsVersion.TWO_DOT_ZERO
    ):
        return VerizonVehicleData(
            msisdn="5243583607",
            programcode=programcode,
            calldate="2020-09-25",
            activationtype="0",
            calltime="19:05",
            timestamp="2020-09-25T19:05:00.000000",
            event_datetime="1603911241022",
            vin="1VWSA7A3XLC011823",
            brand="VW",
            modelname="Passat",
            modelyear="2008",
            modelcode="A342P6",
            modeldesc="Passat_2008",
            market="nar-us",
            odometer=16114,
            odometerscale=OdometerScaleType.KILOMETERS,
            latitude=37.532918,
            longitude=-122.272576,
            headingdirection="NORTH EAST",
            status="SUCCESS",
            responsemessage="Successfully retrieved",
        )
    if (
        programcode
        and programcode.lower() == ProgramCode.PORSCHE.name.lower()
        and ctsversion == CtsVersion.ONE_DOT_ZERO
    ):
        return VodafoneVehicleData(
            msisdn="5243583607",
            programcode=programcode,
            calldate="2020-09-25",
            activationtype=None,
            calltime="19:05",
            timestamp="2020-09-25T19:05:00.000000",
            event_datetime="1603911241022",
            vin="1VWSA7A3XLC011823",
            brand="PORSCHE",
            modelname=None,
            modelyear=None,
            modelcode=None,
            modeldesc=None,
            market=None,
            odometer=None,
            odometerscale=None,
            latitude=37.532918,
            longitude=-122.272576,
            headingdirection=None,
            mileage=0,
            mileageunit="Miles",
            status="SUCCESS",
            responsemessage="Successfully retrieved",
        )
    return AerisVehicleData(
        msisdn="5243583607",
        programcode=programcode,
        calldate="2020-09-25",
        activationtype="0",
        calltime="19:05",
        timestamp="2020-09-25T19:05:00.000000",
        event_datetime="1603911241022",
        vin="1VWSA7A3XLC011823",
        brand="VW",
        modelname="Passat",
        modelyear="2008",
        modelcode="A342P6",
        modeldesc="Passat_2008",
        market="nar-us",
        odometer=16114,
        odometerscale=OdometerScaleType.KILOMETERS,
        latitude=37.532918,
        longitude=-122.272576,
        headingdirection="NORTH EAST",
        status="SUCCESS",
        responsemessage="Successfully retrieved",
    )


def porsche_valid_json():
    return {
        "countryCode": "US",
        "timestamp": "1536575714",
        "gpsData": {"latitude": "+40.67623", "longitude": "-074.00076"},
        "vehicleData": {
            "vin": "WP1AA2A24JKA06336",
            "registration": {
                "number": "GVW1649",
                "stateCode": "NY",
                "countryCode": "US",
            },
            "crankInhibition": "",
            "ignitionKey": "OFF",
            "mileage": {"value": "3194", "unit": "mi"},
            "fuelLevelPercentage": "98",
            "evBatteryPercentage": None,
            "range": {"value": "419", "unit": "mi"},
            "tyrePressureDelta": {
                "unit": "bar",
                "frontLeft": "-1.4",
                "frontRight": "+0",
                "rearLeft": "+0.1",
                "rearRight": "+0.1",
            },
        },
        "userData": {"phoneContact": "+12345678901"},
    }


def save_data_request_json():
    return {
        "programcode": "fca",
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
                        "positionLatitude": 30.6812744140625,
                        "positionLongitude": -20.21455383300781,
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

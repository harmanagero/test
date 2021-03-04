from src.models.enums.status_type import Status
from src.models.responses.create_save_vehicledata_response import CreateSaveVehicleDataResponse

def test_create_save_vehicledata_response_has_correct_values():
    dict = {
        "msisdn": "testmsisdn",
        "status": "200",
        "responsemessage": "some message",
    }
    save_vehicledata = CreateSaveVehicleDataResponse(**dict)
    assert save_vehicledata.msisdn == "testmsisdn"
    assert save_vehicledata.status == Status.SUCCESS
    assert save_vehicledata.responsemessage == "some message"

def test_create_save_vehicledata_response_has_optional_values_as_expected():
    save_vehicledata = CreateSaveVehicleDataResponse()
    assert save_vehicledata.msisdn is None
    assert save_vehicledata.status == Status.UNKNOWN
    assert save_vehicledata.responsemessage is None
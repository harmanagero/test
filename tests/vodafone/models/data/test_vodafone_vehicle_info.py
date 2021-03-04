from src.vodafone.models.data.vehicle_info import VehicleInfo


def test_vodafone_vehicle_info_should_populate_all_fields():

    vehicle_data_json = generate_valid_vodafone_data()
    data = VehicleInfo(**vehicle_data_json)
    assert data == vehicle_data_json


def generate_valid_vodafone_data():
    return {
        "msisdn": "5243583607",
        "programcode": "porsche",
        "status": "SUCCESS",
        "responsemessage": "response message",
        "JSONData": {"some": "data"},
    }

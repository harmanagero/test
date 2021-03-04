from datetime import datetime
from src.vodafone.models.data.vehicle_data import VehicleData


def test_vodafone_vehicle_data_should_populate_all_fields():

    vehicle_data_json = generate_valid_vodafone_data()
    data = VehicleData(**vehicle_data_json)
    assert data == vehicle_data_json


def generate_valid_vodafone_data():
    return {
        "msisdn": "5243583607",
        "programcode": "porsche",
        "event_datetime": 1597783540014,  # datetime.utcnow timestamp*1000
        "timestamp": datetime.strptime(
            "2020-09-25T19:05:15.769000", "%Y-%m-%dT%H:%M:%S.%f"
        ),  # calldate and time
        "calldate": "2020-09-25",
        "activationtype": None,
        "calltime": "19:05",
        "vin": "1VWSA7A3XLC011823",
        "brand": "porsche",
        "modelname": None,
        "modelyear": None,
        "modelcode": None,
        "modeldesc": None,
        "market": None,
        "odometer": None,
        "odometerscale": None,
        "latitude": 37.532918,
        "longitude": -122.272576,
        "headingdirection": None,
        "countrycode": "US",
        "mileage": 0,
        "mileageunit": "Miles",
        "status": "SUCCESS",
        "responsemessage": "response message",
    }

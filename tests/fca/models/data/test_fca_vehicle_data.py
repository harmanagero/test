from datetime import datetime

from src.fca.models.data.vehicle_data import VehicleData


def test_vehicle_data_for_fca_should_populate_all_fields():

    vehicle_data_json = generate_valid_fca_data()
    data = VehicleData(**vehicle_data_json)
    assert data == vehicle_data_json


def generate_valid_fca_data():
    return {
        "msisdn": "5243583607",
        "programcode": "fca",
        "event_datetime": 1597783540014,  # datetime.utcnow timestamp*1000
        "timestamp": datetime.strptime(
            "2020-09-25T19:05:15.769000", "%Y-%m-%dT%H:%M:%S.%f"
        ),  # calldate and time
        "countrycode": "US",
        "calldate": "2020-09-25",
        "calltime": "19:05",
        "vin": "1VWSA7A3XLC011823",
        "brand": "vw",
        "modelname": "Passat",
        "modelyear": "2008",
        "modelcode": "A342P6",
        "modeldesc": "Passat_2008",
        "odometer": 16114,
        "odometerscale": "Kilometers",
        "latitude": 37.532918,
        "longitude": -122.272576,
        "headingdirection": "NORTH EAST",
        "activationtype": "bcall",
        "market": "nar-us",
        "mileage": None,
        "mileageunit": None,
        "status": "SUCCESS",
        "responsemessage": "response message",
    }

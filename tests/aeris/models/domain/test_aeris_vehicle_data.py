from datetime import datetime

from src.aeris.models.domain.vehicle_data import VehicleData


def test_vehicle_data_for_aeris_should_populate_all_fields():

    vehicle_data_json = generate_valid_aeris_data()

    data = VehicleData(**vehicle_data_json)

    assert data == vehicle_data_json


def generate_valid_aeris_data():
    return {
        "msisdn": "5243583607",
        "programcode": "vwcarnet",
        "event_datetime": 1597783540014,  # datetime.utcnow timestamp*1000
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
        "odometerscale": "Kilometers",
        "latitude": 37.532918,
        "longitude": -122.272576,
        "headingdirection": "NORTH EAST",
        "countrycode": None,
        "mileage": None,
        "mileageunit":None,
        "status": "SUCCESS",
        "responsemessage": "response message",
    }

from datetime import datetime

from src.verizon.models.data.vehicle_data import VehicleData


def test_vehicle_data_for_verizon_should_populate_all_fields():
    vehicle_data_json = generate_valid_verizon_data()
    data = VehicleData(**vehicle_data_json)
    assert data == vehicle_data_json


def generate_valid_verizon_data():
    return {
        "msisdn": "5243583607",
        "programcode": "vwcarnet",
        "event_datetime": 1597783540014,  # datetime.utcnow timestamp*1000
        "timestamp": datetime.strptime(
            "2021-01-07T13:44:32.769000", "%Y-%m-%dT%H:%M:%S.%f"
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
        "latitude": 37.532918,
        "longitude": -122.272576,
        "headingdirection": "North",
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
        "altitude": "542 ft",
        "language": "English",
        "status": "SUCCESS",
        "responsemessage": "response message",
    }

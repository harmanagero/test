from src.vodafone.models.domain.vehicle_data import VehicleDataRequest


def test_vodafone_vehicle_data_should_populate_all_fields():

    vehicle_data_json = generate_valid_vodafone_data()
    data = VehicleDataRequest(**vehicle_data_json)
    assert data == vehicle_data_json


def generate_valid_vodafone_data():
    return {
        "countryCode": "US",
        "timestamp": "1486741602",
        "gpsData": {"latitude": "+42.98665", "longitude": "+42.98665"},
        "vehicleData": {
            "vin": "WP0BNM97ZAL040111",
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

from datetime import datetime

import pytest
from src.siriusxm.models.data.vehicle_data import VehicleData


mockvalidCVTestData = [
    (
        {
            "request_key": "nissan-TESTREFERENCE",
            "programcode": "nissan",
            "language": "en",
            "referenceid": "TESTREFERENCE",
            "geolocation": "42.406~-71.0742~400;enc-param=token",
            "vin": "TESTVIN",
            "timestamp": datetime.strptime(
                "2020-10-28T18:54:00.000000", "%Y-%m-%dT%H:%M:%S.%f"
            ),
            "event_datetime": "1603911241022",  # 2020-10-28 18:54
            "calldate": "2020-10-28",
            "calltime": "18:54",
            "hexvehicledata": {
                "VarName": "User-to-User",
                "Value": "00524f4144534944457e34333534333534337e34322e3430367e2d37312e303734327e313233343536373839307e656e",
            },
        }
    ),
    (
        {
            "request_key": "infiniti-TESTREFERENCE",
            "programcode": "infiniti",
            "language": "en",
            "referenceid": "TESTREFERENCE",
            "geolocation": "42.406~-71.0742~400;enc-param=token",
            "vin": "TESTVIN",
            "timestamp": datetime.strptime(
                "2020-10-28T18:54:00.000000", "%Y-%m-%dT%H:%M:%S.%f"
            ),
            "event_datetime": "1603911241022",  # 2020-10-28 18:54
            "calldate": "2020-10-28",
            "calltime": "18:54",
            "hexvehicledata": {
                "VarName": "User-to-User",
                "Value": "00524f4144534944457e34333534333534337e34322e3430367e2d37312e303734327e313233343536373839307e656e",
            },
        }
    ),
]


@pytest.mark.parametrize(
    "mockvalidCVTestData", mockvalidCVTestData, ids=["Nissan", "Infiniti"]
)
def test_vehicle_data_for_siriusxm_should_populate_all_fields(mockvalidCVTestData):

    data = VehicleData(**mockvalidCVTestData)
    assert data.referenceid == mockvalidCVTestData["referenceid"]
    assert data.language == mockvalidCVTestData["language"]
    assert data.programcode == mockvalidCVTestData["programcode"]
    assert data.latitude == mockvalidCVTestData["geolocation"].split("~")[0]
    assert data.longitude == mockvalidCVTestData["geolocation"].split("~")[1]
    assert data.vin == mockvalidCVTestData["vin"]
    assert data.timestamp == mockvalidCVTestData["timestamp"]
    assert data.calldate == mockvalidCVTestData["calldate"]
    assert data.calltime == mockvalidCVTestData["calltime"]
    assert (
        data.hexvehicledata.VarName == mockvalidCVTestData["hexvehicledata"]["VarName"]
    )
    assert data.hexvehicledata.Value == mockvalidCVTestData["hexvehicledata"]["Value"]

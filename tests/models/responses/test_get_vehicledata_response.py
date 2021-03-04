import pytest
from src.models.enums.status_type import Status
from src.models.responses.get_vehicledata_response import (
    Brand,
    GetVehicleDataResponse,
    Header,
    Location,
    Vehicle,
)

mockResponseTestData = [
    (
        {
            "status": Status.SUCCESS,
            "responsemessage": "Successfully retrieved",
            "language": "en",
            "referenceid": "someid",
            "latitude": "42.406",
            "longitude": "71.074",
            "vin": "TESTVIN",
        },
        Status.SUCCESS,
    ),
    (
        {
            "status": Status.NOT_FOUND,
            "responsemessage": "No data found",
            "language": "en",
            "referenceid": "someid",
            "latitude": "42.406",
            "longitude": "71.074",
            "vin": "TESTVIN",
        },
        Status.NOT_FOUND,
    ),
    (
        {
            "status": Status.INTERNAL_SERVER_ERROR,
            "responsemessage": "Internal server error",
            "language": "en",
            "referenceid": "someid",
            "latitude": "42.406",
            "longitude": "71.074",
            "vin": "TESTVIN",
        },
        Status.INTERNAL_SERVER_ERROR,
    ),
]


@pytest.mark.parametrize(
    "programcode",
    ["nissan", "infiniti", "porsche"],
    ids=["Nissan", "Infiniti", "vodafone"],
)
@pytest.mark.parametrize(
    "mockResponseTestData,expected",
    mockResponseTestData,
    ids=["SuccessResponse", "NotFoundReponse", "InternalServerErrorResponse"],
)
def test_get_vehicledata_response_has_expected_responses(
    mockResponseTestData, expected, programcode
):
    vehicle_model = GetVehicleDataResponse(
        status=mockResponseTestData["status"],
        responsemessage=mockResponseTestData["responsemessage"],
        header=Header(
            programcode=programcode,
            language=mockResponseTestData["language"],
            referenceid=mockResponseTestData["referenceid"],
        ),
        location=Location(
            latitude=mockResponseTestData["latitude"],
            longitude=mockResponseTestData["longitude"],
        ),
        vehicle=Vehicle(
            vin=mockResponseTestData["vin"],
            mileage=None,
            MileageUnit=None,
        ),
    )
    assert vehicle_model.status == expected
    assert vehicle_model.header.programcode == programcode

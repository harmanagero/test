from src.models.responses.health_check_response import HealthCheckResponse


def test_health_check_response_has_correct_values():
    dict = {
        "success": True,
        "responsemessage": "some message",
    }
    healthcheck_response = HealthCheckResponse(**dict)
    assert healthcheck_response.success
    assert healthcheck_response.responsemessage == "some message"


def test_health_check_response_has_optional_values_as_expected():
    healthcheck_response = HealthCheckResponse(success=False)
    assert healthcheck_response.success == False
    assert healthcheck_response.responsemessage is None
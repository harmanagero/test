from src.models.enums.status_type import Status
from enum import Enum
import pytest


mockStatusTestData = [
    ("200",Status.SUCCESS),
    ("201", Status.CREATED),
    ("404", Status.NOT_FOUND),
    ("500", Status.INTERNAL_SERVER_ERROR),
    ("0", Status.UNKNOWN),
    ("403", Status.INVALID_STATE_ERROR),
    ("400", Status.BAD_REQUEST),
]

@pytest.mark.parametrize(
    "statuscode, expected",
    mockStatusTestData,
    ids=[
        "Success",
        "Created",
        "NotFound",
        "InternalServerError",
        "Unknown",        
        "InvalidStateError",
        "BadRequest",
    ],
)
def test_enum_status_has_correct_values(statuscode,expected):
    status_enum = Status(statuscode)
    assert status_enum == expected

@pytest.mark.parametrize("statuscode", ["TeSt"])
def test_enum_status_fail_with_incorrect_values(statuscode):
    try:
        status_enum = Status(statuscode)
    except Exception as e:
        assert e.args[0]=="'{}' is not a valid Status".format(statuscode)

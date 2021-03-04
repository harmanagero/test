import pytest

from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.exceptions.application_exception import ApplicationException
from src.models.exceptions.badrequest_exception import BadRequestException
from src.models.exceptions.forbidden_exception import ForbiddenException
from src.models.exceptions.notfound_exception import NotFoundException
from src.utilities.errorhandlers.error_responsestatus import handle_error_responsestatus

testdata = [
    ("BaD_ReQuEsT", BadRequestException),
    ("fOrBiDdEn", ForbiddenException),
    ("NoT_fOuNd", NotFoundException),
    ("iNtErNaL_sErVeR_eRroR", ApplicationException),
    ("SoMeStAtUs", ApplicationException),
    ("", ApplicationException),
]

testinternalstatus = [
    (InternalStatusType.BADREQUEST, BadRequestException),
    (InternalStatusType.FORBIDDEN, ForbiddenException),
    (InternalStatusType.NOTFOUND, NotFoundException),
    (InternalStatusType.INTERNALSERVERERROR, ApplicationException),
    (InternalStatusType.ERROR, ApplicationException),
    (InternalStatusType.CANCELED, ApplicationException),
    (InternalStatusType.UNKNOWN, ApplicationException),
    ("", ApplicationException),
]


@pytest.mark.parametrize("status_input, expected_exception", testdata)
def test_error_responsestatus_on_different_response_raise_expected_exception(
    status_input, expected_exception
):
    actual_exception = handle_error_responsestatus(status_input)
    assert actual_exception == expected_exception


@pytest.mark.parametrize(
    "internalstatustype_input, expected_exception", testinternalstatus
)
def test_error_responsestatus_on_various_internalstatustype_error_should_raise_expected_exception(
    internalstatustype_input, expected_exception
):
    actual_exception = handle_error_responsestatus(internalstatustype_input)
    assert actual_exception == expected_exception

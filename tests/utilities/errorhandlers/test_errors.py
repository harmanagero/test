from src.utilities.errorhandlers.errors import create_bad_request_error
from src.utilities.errorhandlers.errors import create_forbidden_server_error
from src.utilities.errorhandlers.errors import create_internal_server_error
from src.utilities.errorhandlers.errors import create_notallowed_server_error
from src.utilities.errorhandlers.errors import create_notfound_server_error


def test_create_bad_request_error_creates_as_expected():
    loc_contents = ["foo", "bar", "baz"]
    msg_contents = "fooMessage"
    type_contents = "fooType"

    error = create_bad_request_error(
        {"loc": loc_contents, "msg": msg_contents, "type": type_contents}
    )
    assert error.status == "400"
    assert error.code == "BadRequest"
    assert error.title == "Bad Request"
    assert error.detail.location == loc_contents
    assert error.detail.message == msg_contents
    assert error.detail.type == type_contents


def test_create_bad_request_error_creates_as_expected_with_empty_dict():
    error = create_bad_request_error({})

    assert error.detail.location == []
    assert error.detail.message == ""
    assert error.detail.type == ""


def test_create_forbidden_server_error_creates_as_expected():
    detail = "Detail"
    error = create_forbidden_server_error(detail)
    assert error.status == "403"
    assert error.code == "ForbiddenError"
    assert error.title == "Forbidden Error"
    assert error.detail == detail


def test_create_notfound_server_error_creates_as_expected():
    detail = "Detail"
    error = create_notfound_server_error(detail)
    assert error.status == "404"
    assert error.code == "NotFound"
    assert error.title == "Not Found"
    assert error.detail == detail

def test_create_method_notallowed_server_error_creates_as_expected():
    detail = "Detail"
    error = create_notallowed_server_error(detail)
    assert error.status == "405"
    assert error.code == "MethodNotAllowed"
    assert error.title == "Method Not Allowed"
    assert error.detail == detail


def test_create_internal_server_error_creates_as_expected():
    detail = "fooDetail"
    error = create_internal_server_error(detail)
    assert error.status == "500"
    assert error.code == "InternalServerError"
    assert error.title == "Internal Server Error"
    assert error.detail == detail

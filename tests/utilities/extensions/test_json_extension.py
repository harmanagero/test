import pytest

from src.utilities.extensions.json_extension import checkjsonnode
from src.utilities.extensions.json_extension import seterrorjson


@pytest.mark.parametrize("jsonnode, expected", [("nodea", True), ("nodeb", False)])
def test_checkjsonnode_returns_as_expected(jsonnode, expected):
    jsonstr = {"nodea": "value", "nodec": "value"}
    returnvalue = checkjsonnode(jsonnode, jsonstr)
    assert returnvalue == expected


def test_seterrorjson_returns_as_expected():
    returnvalue = seterrorjson("code", "message")
    assert returnvalue["status"] == "code"
    assert returnvalue["errorCode"] == "message"

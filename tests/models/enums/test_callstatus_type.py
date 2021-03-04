from src.models.enums.callstatus_type import CallStatus

import pytest

@pytest.mark.parametrize("callstatustype,expected", [("TERMINATED",CallStatus.TERMINATED)], ids = ["TERMINATED"])
def test_enum_assignmenttype_has_correct_values(callstatustype,expected):
    callstatus_enum = CallStatus(callstatustype)
    assert callstatus_enum == expected


@pytest.mark.parametrize("callstatustype", [""," ","tErMiNaTeD","any"])
def test_enum_assignmenttype_fail_with_incorrect_values(callstatustype):
    try:
        callstatus_enum = CallStatus(callstatustype)
    except Exception as e:
        assert e.args[0]=="'{}' is not a valid CallStatus".format(callstatustype)

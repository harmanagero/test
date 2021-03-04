from src.models.enums.ctsversion_type import CtsVersion

import pytest

@pytest.mark.parametrize("ctsversion,expected", [("1.0",CtsVersion.ONE_DOT_ZERO), ("2.0", CtsVersion.TWO_DOT_ZERO)], ids = ["1.0","2.0"])
def test_enum_assignmenttype_has_correct_values(ctsversion,expected):
    ctsversion_enum = CtsVersion(ctsversion)
    assert ctsversion_enum == expected


@pytest.mark.parametrize("ctsversion", [""," ","1","3.0"])
def test_enum_assignmenttype_fail_with_incorrect_values(ctsversion):
    try:
        ctsversion_enum = CtsVersion(ctsversion)
    except Exception as e:
        assert e.args[0]=="'{}' is not a valid CtsVersion".format(ctsversion)

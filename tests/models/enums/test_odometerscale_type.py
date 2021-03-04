from src.models.enums.odometerscale_type import OdometerScaleType

import pytest

@pytest.mark.parametrize("odometerscale,expected", [("Kilometers",OdometerScaleType.KILOMETERS),("Miles",OdometerScaleType.MILES)], ids = ["Kilometers","Miles"])
def test_enum_odometerscaletype_has_correct_values(odometerscale,expected):
    odometerscale_enum = OdometerScaleType(odometerscale)
    assert odometerscale_enum == expected


@pytest.mark.parametrize("odometerscale", ["TeSt"])
def test_enum_assignmenttype_fail_with_incorrect_values(odometerscale):
    try:
        assignment_enum = OdometerScaleType(odometerscale)
    except Exception as e:
        assert e.args[0]=="'{}' is not a valid OdometerScaleType".format(odometerscale)

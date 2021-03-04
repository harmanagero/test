import pytest
from src.models.enums.odometerscale_type import OdometerScaleType
from src.utilities.metric_scale import MileageUnit, OdometerScale


@pytest.mark.parametrize(
    "odometerscaleintvalue,expected",
    [(0, OdometerScaleType.MILES), (1, OdometerScaleType.KILOMETERS)],
    ids=["Miles", "Kilometers"],
)
def test_odometerscale_on_valid_input_returns_expected_values(
    odometerscaleintvalue, expected
):
    odometerscale_enum = OdometerScale(odometerscaleintvalue)
    assert odometerscale_enum == expected


def test_odometerscale_on_unlisted_param_returns_None():
    odometerscale_enum = OdometerScale(2)
    assert odometerscale_enum is None


@pytest.mark.parametrize(
    "mileageunit,expected",
    [
        ("mI", OdometerScaleType.MILES),
        ("Km", OdometerScaleType.KILOMETERS),
        ("Mi", OdometerScaleType.MILES),
        ("kM", OdometerScaleType.KILOMETERS),
        ("MI", OdometerScaleType.MILES),
        ("KM", OdometerScaleType.KILOMETERS),
        ("mi", OdometerScaleType.MILES),
        ("km", OdometerScaleType.KILOMETERS),
        ("mIlEs", OdometerScaleType.MILES),
        ("KiLoMeTeRs", OdometerScaleType.KILOMETERS),
    ],
)
def test_mileageunit_on_valid_input_returns_expected_values(mileageunit, expected):
    mileageunit_enum = MileageUnit(mileageunit)
    assert mileageunit_enum == expected


def test_mileageunit_on_unlisted_param_returns_None():
    mileageunit_enum = OdometerScale("invalid")
    assert mileageunit_enum is None

from src.models.enums.odometerscale_type import OdometerScaleType


def OdometerScale(odometerscale: int):
    switcher = {0: OdometerScaleType.MILES, 1: OdometerScaleType.KILOMETERS}
    return switcher.get(odometerscale)


def MileageUnit(mileageunit: str):
    mileageunit = mileageunit.casefold()
    switcher = {
        "MI".casefold(): OdometerScaleType.MILES,
        "KM".casefold(): OdometerScaleType.KILOMETERS,
        "Miles".casefold(): OdometerScaleType.MILES,
        "Kilometers".casefold(): OdometerScaleType.KILOMETERS,
    }
    return switcher.get(mileageunit)

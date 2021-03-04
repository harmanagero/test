from logging import exception
from pydantic.error_wrappers import ValidationError
import pytest

from src.models.commands.get_vehicledata_command import GetVehicleDataCommand


@pytest.mark.parametrize(
    "msisdn",
    ["1234567890", "12345678901"],
    ids=["TenDigitNumbers", "ElevenDigitNumbers"],
)
@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("vwcarnet", "1.0")],
    ids=["Aeris", "FCA", "Verizon"],
)
def test_client_get_vehicledata_has_correct_values(msisdn, programcode, ctsversion):
    dict = {"msisdn": msisdn, "programcode": programcode, "ctsversion": ctsversion}
    vehicle_model = GetVehicleDataCommand(**dict)
    assert vehicle_model.msisdn == msisdn
    assert vehicle_model.programcode == programcode
    assert vehicle_model.ctsversion == ctsversion


@pytest.mark.parametrize(
    "msisdn,expectedmsisdn",
    [
        ("1234567890-", "1234567890"),
        ("12345678901--", "12345678901"),
        ("1234567890----", "1234567890"),
        ("12345678901----", "12345678901"),
        ("+1234567890", "1234567890"),
        ("+12345678901", "12345678901"),
        ("208-098-6765", "2080986765"),
        ("+128-098-6765", "1280986765"),
        ("'+128-098-6765'", "1280986765"),
        ('"+128-098-6765"', "1280986765"),
        ('" 128-098-6765"', "1280986765"),
        ('"128-098-6765 "', "1280986765"),
    ],
    ids=[
        "TenDigitNumbersWithHypen",
        "ElevenDigitNumbersWithHypen",
        "TenDigitNumbersWithMultipleHypen",
        "ElevenDigitNumbersWithMultipleHypen",
        "TenDigitNumbersWithPlus",
        "ElevenDigitNumberWithPlus",
        "PhoneNumberFormatWithHyphen",
        "PhoneNumberFormatWithHyphenAndPlus",
        "PhoneNumberFormatWithSingleQuote",
        "PhoneNumbeFormatrWithDoubleQuotes",
        "PhoneNumberFormatWithLeadingSpace",
        "PhoneNumberFormatWithTrailingSpace",
    ],
)
@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("vwcarnet", "1.0"), ("porsche", "1.0")],
    ids=["Aeris", "FCA", "Verizon", "Vodafone"],
)
def test_getvehicledata_with_hypen_minimum_tendigitnumbers_msisdn_should_return_valid_msisdn_with_removed_hypen_value(
    msisdn, programcode, ctsversion, expectedmsisdn
):
    dict = {"msisdn": msisdn, "programcode": programcode, "ctsversion": ctsversion}
    vehicle_model = GetVehicleDataCommand(**dict)
    assert vehicle_model.msisdn == expectedmsisdn
    assert vehicle_model.programcode == programcode
    assert vehicle_model.ctsversion == ctsversion


@pytest.mark.parametrize(
    "msisdn",
    ["", "None", None, "0", "-", "123456789"],
    ids=[
        "EmptyString",
        "NoneString",
        "None",
        "Zero",
        "HypenString",
        "NineDigitNumbers",
    ],
)
@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", "2.0"), ("fca", "1.0"), ("vwcarnet", "1.0")],
    ids=["Aeris", "FCA", "Verizon"],
)
def test_client_get_vehicledata_has_invalid_values(msisdn, programcode, ctsversion):
    with pytest.raises(Exception) as execinfo:
        dict = {"msisdn": msisdn, "programcode": programcode, "ctsversion": ctsversion}
        vehicle_model = GetVehicleDataCommand(**dict)
    assert execinfo.type == ValidationError
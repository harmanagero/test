from src.models.enums.programcode_type import ProgramCode

import pytest

mockProgramCodeTestData = [
    ("nissan", ProgramCode.NISSAN),
    ("infiniti", ProgramCode.INFINITI),
    ("fca", ProgramCode.FCA),
    ("vwcarnet", ProgramCode.VWCARNET),
    ("porsche", ProgramCode.PORSCHE),
    ("toyota", ProgramCode.TOYOTA),
    ("subaru", ProgramCode.SUBARU),
]


@pytest.mark.parametrize(
    "programcode,expected",
    mockProgramCodeTestData,
    ids=["Nissan", "Infiniti", "Fca", "VWCarnet", "Porsche", "Toyota", "Subaru"],
)
def test_enum_programcode_has_correct_values(programcode, expected):
    programcode_enum = ProgramCode(programcode)
    assert programcode_enum == expected


@pytest.mark.parametrize("programcode", ["TeSt"])
def test_enum_programcode_fail_with_incorrect_values(programcode):
    try:
        programcode_enum = ProgramCode(programcode)
    except Exception as e:
        assert e.args[0] == "'{}' is not a valid ProgramCode".format(programcode)

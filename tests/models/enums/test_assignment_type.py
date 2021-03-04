from src.models.enums.assignment_type import AssignmentType

import pytest

@pytest.mark.parametrize("assignmenttype,expected", [("TLMTCS",AssignmentType.TLMTCS),("TLMMNS",AssignmentType.TLMMNS)], ids = ["Tlmtcs","Tlmmns"])
def test_enum_assignmenttype_has_correct_values(assignmenttype,expected):
    assignment_enum = AssignmentType(assignmenttype)
    assert assignment_enum == expected


@pytest.mark.parametrize("assignmenttype", ["TeSt"])
def test_enum_assignmenttype_fail_with_incorrect_values(assignmenttype):
    try:
        assignment_enum = AssignmentType(assignmenttype)
    except Exception as e:
        assert e.args[0]=="'{}' is not a valid AssignmentType".format(assignmenttype)

import pytest

from src.models.commands.create_agentassignment import CreateAgentAssignmentCommand


@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti"], ids=["Nissan", "Infiniti"]
)
def test_create_agentassignment_has_correct_values(programcode):

    dict = {
        "referenceid": "testreferenceid",
        "isassigned": False,
        "programcode": programcode,
    }
    agentassignment_model = CreateAgentAssignmentCommand(**dict)
    assert agentassignment_model.referenceid == "testreferenceid"
    assert not agentassignment_model.isassigned
    assert agentassignment_model.programcode == programcode

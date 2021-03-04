import pytest
from src.models.commands.create_terminate import CreateTerminateCommand

@pytest.mark.parametrize("programcode", ["nissan","infiniti"], ids = ["Nissan","Infiniti"])
def test_client_create_terminate_without_reasoncode_has_correct_values(programcode):

    dict =  {"referenceid":"testreferenceid", "programcode": programcode }
    terminate_model = CreateTerminateCommand(**dict)
    assert terminate_model.referenceid == "testreferenceid"
    assert terminate_model.programcode == programcode

@pytest.mark.parametrize("programcode", ["nissan","infiniti"], ids = ["Nissan","Infiniti"])
def test_client_create_terminate_with_reasoncode_has_correct_values(programcode):

    dict =  {"referenceid":"testreferenceid", "reasoncode":"connectedvehicle", "programcode": programcode}
    terminate_model = CreateTerminateCommand(**dict)
    assert terminate_model.referenceid == "testreferenceid"
    assert terminate_model.reasoncode == "connectedvehicle"
    assert terminate_model.programcode == programcode
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.tmna.models.data.terminate import Terminate


def test_terminate_tmna_should_populate_all_fields():

    tmna_terminate_json = generate_valid_tmna_data()

    data = Terminate(**tmna_terminate_json)

    assert data == tmna_terminate_json


def generate_valid_tmna_data():
    return {
        "eventid": "1234565",
        "status": InternalStatusType.SUCCESS,
        "responsemessage": "message",
    }

from src.fca.models.domain.terminate import Terminate
from src.models.domain.enums.internal_status_type import InternalStatusType


def test_terminate_for_fca_should_populate_all_fields():

    fca_terminate_json = generate_valid_fca_data()

    data = Terminate(**fca_terminate_json)

    assert data == fca_terminate_json


def generate_valid_fca_data():
    return {
        "msisdn": "1234565",
        "callstatus": "TERMINATED",
        "status": InternalStatusType.SUCCESS,
        "responsemessage": "message",
    }

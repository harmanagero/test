from unittest import TestCase
from unittest.mock import patch

from src.aeris.models.domain.vehicle_data import VehicleData
from src.models.domain.enums.internal_status_type import InternalStatusType
from src.services.client_service import ClientService
from src.siriusxm.models.domain.agentassignment import AgentAssignment
from src.siriusxm.models.domain.terminate import Terminate


def generate_valid_cv_data():
    return {
        "request_key": "nissan-TESTREFERENCE",
        "programcode": "nissan",
        "language": "en",
        "referenceid": "TESTREFERENCE",
        "geolocation": "42.406~-71.0742~400;enc-param=token",
        "vin": "TESTVIN",
    }


def generate_get_vehicledata():
    return VehicleData(
        status=InternalStatusType.SUCCESS,
        programcode="nissan",
        language="en",
        referenceid="TESTREFERENCE",
        latitude="42.406",
        longitude="-71.0742",
        vin="TESTVIN",
        timestamp="2020-10-28T18:54:00.000000",
        event_datetime="1603911241022",  # 2020-10-28 18:54
        calldate="2020-10-28",
        calltime="18:54",
    )


class test_client_service(TestCase):
    def test_cannot_instantiate(self):
        # """showing we normally can't instantiate an abstract class"""
        with self.assertRaises(TypeError):
            ClientService()

    @patch.multiple(ClientService, __abstractmethods__=set())
    def test_abstract_method_declaration(self):
        # """patch abstract class and its abstract methods for duration of the test"""
        my_abstract = ClientService()

        agentassignment = AgentAssignment(
            referenceid="TESTREFERENCE", isassigned=True, programcode="nissan"
        )
        terminate = Terminate(referenceid="TESTREFERENCE", programcode="nissan")

        assign_agent_method = my_abstract.assign_agent(agentassignment)
        terminate_method = my_abstract.terminate(terminate)
        get_vehicledata_method = my_abstract.get_vehicledata(
            id="TESTREFERENCE", programcode="nissan"
        )
        save_vehicledata_method = my_abstract.save_vehicledata(generate_valid_cv_data())
        populate_vehicledata_method = my_abstract.populate_vehicledata(
            generate_valid_cv_data()
        )

        assert assign_agent_method is None
        assert terminate_method is None
        assert get_vehicledata_method is None
        assert save_vehicledata_method is None
        assert populate_vehicledata_method is None

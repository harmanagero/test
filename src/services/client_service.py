from abc import ABC, abstractmethod

from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.siriusxm.models.data.vehicle_data import VehicleData
from src.siriusxm.models.domain.agentassignment import AgentAssignment
from src.siriusxm.models.domain.terminate import Terminate


# abstract base class work
class ClientService(ABC):
    _localstore = {}

    # abstract method
    @abstractmethod
    def assign_agent(self, agentassignment: AgentAssignment):
        pass

    # abstract method
    @abstractmethod
    def terminate(self, terminate: Terminate):
        pass

    # abstract method
    @abstractmethod
    def get_vehicledata(self, id: str, programcode: ProgramCode):
        pass

    # abstract method
    @abstractmethod
    def save_vehicledata(self, vehicledata: VehicleData):
        pass

    @abstractmethod
    def populate_vehicledata(self, data):
        pass

    @abstractmethod
    def health(self, programcode: ProgramCode, ctsversion: CtsVersion):
        pass

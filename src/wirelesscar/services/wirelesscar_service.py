import logging

from src.config.wirelesscar_config import WirelessCarConfig
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.client_service import ClientService

logger = logging.getLogger(__name__)


class WirelessCarService(ClientService):
    def __init__(
        self,
        config: WirelessCarConfig,
    ):
        self._logger = logger
        self._config = config

    def save_vehicledata(self, any):
        raise NotImplementedError

    def get_vehicledata(self, id: str, programcode: ProgramCode):
        raise NotImplementedError

    def assign_agent(self, any):
        raise NotImplementedError

    def terminate(self, any):
        raise NotImplementedError

    def populate_vehicledata(self, any):
        raise NotImplementedError

    def health(self, programcode: ProgramCode, ctsversion: CtsVersion):
        raise NotImplementedError

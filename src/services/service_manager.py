from typing import Optional

from pydantic import BaseModel
from src.aeris.services.aeris_service import AerisService
from src.config.aeris_config import AerisConfig
from src.config.configuration_manager import setup_config_manager
from src.config.dynamo_config import DynamoConfig
from src.config.fca_config import FcaConfig
from src.config.siriusxm_config import SiriusXmConfig
from src.config.tmna_config import TmnaConfig
from src.config.verizon_config import VerizonConfig
from src.config.vodafone_config import VodafoneConfig
from src.config.wirelesscar_config import WirelessCarConfig
from src.fca.services.fca_service import FcaService
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.client_service import ClientService
from src.services.dynamodb_tables import get_main_table, get_supplement_table
from src.siriusxm.services.siriusxm_service import SiriusXmService
from src.tmna.services.tmna_service import TmnaService
from src.utilities.extensions.string_extension import isnull_whitespaceorempty
from src.verizon.services.verizon_service import VerizonService
from src.vodafone.services.vodafone_service import VodafoneService
from src.wirelesscar.services.wirelesscar_service import WirelessCarService


class ServiceManager(BaseModel):
    client_service: Optional[ClientService]

    class Config:
        arbitrary_types_allowed = True


# use program code to decide right service.
def setup_service_manager(
    programcode, version: Optional[str] = CtsVersion.ONE_DOT_ZERO
) -> ServiceManager:
    config_manager = setup_config_manager()
    version = CtsVersion.ONE_DOT_ZERO if isnull_whitespaceorempty(version) else version
    service = None

    if (
        programcode
        and programcode.lower() == ProgramCode.NISSAN.name.lower()
        or programcode
        and programcode.lower() == ProgramCode.INFINITI.name.lower()
        or (
            programcode
            and programcode.lower() == ProgramCode.TOYOTA.name.lower()
            and version == CtsVersion.ONE_DOT_ZERO
        )
    ):
        service = SiriusXmService(
            config=config_manager.retrieve_config(SiriusXmConfig),
            table=get_main_table(config_manager.retrieve_config(DynamoConfig)),
        )
    elif (
        programcode
        and programcode.lower() == ProgramCode.FCA.name.lower()
        and version == CtsVersion.ONE_DOT_ZERO
    ):
        service = FcaService(
            config=config_manager.retrieve_config(FcaConfig),
            table=get_main_table(config_manager.retrieve_config(DynamoConfig)),
            supplementtable=get_supplement_table(
                config_manager.retrieve_config(DynamoConfig)
            ),
        )
    elif (
        programcode
        and programcode.lower() == ProgramCode.VWCARNET.name.lower()
        and version == CtsVersion.ONE_DOT_ZERO
    ):
        service = VerizonService(
            config=config_manager.retrieve_config(VerizonConfig),
            table=get_main_table(config_manager.retrieve_config(DynamoConfig)),
            supplementtable=get_supplement_table(
                config_manager.retrieve_config(DynamoConfig)
            ),
        )
    elif (
        programcode
        and programcode.lower() == ProgramCode.VWCARNET.name.lower()
        and version == CtsVersion.TWO_DOT_ZERO
    ):
        service = AerisService(
            config=config_manager.retrieve_config(AerisConfig),
            table=get_main_table(config_manager.retrieve_config(DynamoConfig)),
        )
    elif (
        programcode
        and programcode.lower() == ProgramCode.PORSCHE.name.lower()
        and version == CtsVersion.ONE_DOT_ZERO
    ):
        service = VodafoneService(
            config=config_manager.retrieve_config(VodafoneConfig),
            table=get_main_table(config_manager.retrieve_config(DynamoConfig)),
            supplementtable=get_supplement_table(
                config_manager.retrieve_config(DynamoConfig)
            ),
        )
    elif (
        programcode
        and programcode.lower() == ProgramCode.TOYOTA.name.lower()
        and version == CtsVersion.TWO_DOT_ZERO
    ):
        service = TmnaService(
            config=config_manager.retrieve_config(TmnaConfig),
        )
    elif (
        programcode
        and programcode.lower() == ProgramCode.SUBARU.name.lower()
        and version == CtsVersion.TWO_DOT_ZERO
    ):
        service = WirelessCarService(
            config=config_manager.retrieve_config(WirelessCarConfig),
        )
    return ServiceManager(client_service=service)

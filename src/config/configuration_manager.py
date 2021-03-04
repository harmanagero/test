from os import getenv

from agero_python_configuration import ConfigManager
from src.config.aeris_config import AerisConfig
from src.config.dynamo_config import DynamoConfig
from src.config.echo_config import EchoConfig
from src.config.fca_config import FcaConfig
from src.config.logger_config import LoggerConfig
from src.config.siriusxm_config import SiriusXmConfig
from src.config.tmna_config import TmnaConfig
from src.config.verizon_config import VerizonConfig
from src.config.vodafone_config import VodafoneConfig
from src.config.wirelesscar_config import WirelessCarConfig


def setup_config_manager() -> ConfigManager:
    config_manager = ConfigManager(config_environment=getenv("logging__environment"))
    config_manager.register_config(config_class=LoggerConfig, key="logging")
    config_manager.register_config(config_class=EchoConfig, key="echo")
    config_manager.register_config(config_class=DynamoConfig, key="dynamo")
    config_manager.register_config(config_class=SiriusXmConfig, key="siriusxm")
    config_manager.register_config(config_class=VerizonConfig, key="verizon")
    config_manager.register_config(config_class=FcaConfig, key="fca")
    config_manager.register_config(config_class=AerisConfig, key="aeris")
    config_manager.register_config(config_class=VodafoneConfig, key="vodafone")
    config_manager.register_config(config_class=TmnaConfig, key="tmna")
    config_manager.register_config(config_class=WirelessCarConfig, key="wirelesscar")
    return config_manager

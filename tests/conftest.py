from logging import Logger
from unittest.mock import MagicMock, create_autospec

from agero_python_configuration import ConfigManager
from pytest import fixture
from src.aeris.services.aeris_service import AerisService
from src.fca.services.fca_service import FcaService
from src.services.client_service import ClientService
from src.services.dynamodb_tables import (
    ConnectedVehicleSupplementTable,
    ConnectedVehicleTable,
)
from src.services.echo_service import EchoService
from src.siriusxm.services.siriusxm_service import SiriusXmService
from src.tmna.services.tmna_service import TmnaService
from src.utilities.logging import LoggerFactory
from src.verizon.services.verizon_service import VerizonService
from src.vodafone.services.vodafone_service import VodafoneService
from src.wirelesscar.services.wirelesscar_service import WirelessCarService


@fixture
def mock_logger():
    mocked_logger = create_autospec(spec=Logger)
    yield mocked_logger


@fixture
def mock_dynamo_cv_table():
    mocked_table = create_autospec(spec=ConnectedVehicleTable)
    yield mocked_table


@fixture
def mock_dynamo_supplement_cv_table():
    mocked_table = create_autospec(spec=ConnectedVehicleSupplementTable)
    yield mocked_table


@fixture
def mock_config_manager():
    mocked_manager = create_autospec(spec=ConfigManager)
    yield mocked_manager


@fixture
def mock_client_service():
    mocked_service = create_autospec(spec=ClientService)
    yield mocked_service


@fixture
def mock_siriusxm_client_service():
    mocked_siriusxm_service = create_autospec(spec=SiriusXmService)
    yield mocked_siriusxm_service


@fixture
def mock_fca_client_service():
    mocked_fca_service = create_autospec(spec=FcaService)
    yield mocked_fca_service


@fixture
def mock_verizon_client_service():
    mocked_verizon_service = create_autospec(spec=VerizonService)
    yield mocked_verizon_service


@fixture
def mock_aeris_client_service():
    mocked_aeris_service = create_autospec(spec=AerisService)
    yield mocked_aeris_service


@fixture
def mock_vodafone_client_service():
    mocked_vodafone_service = create_autospec(spec=VodafoneService)
    yield mocked_vodafone_service


@fixture
def mock_echo_service():
    mocked_service = create_autospec(spec=EchoService)
    yield mocked_service


@fixture
def mock_logger_factory(mock_logger):
    mocked_factory = create_autospec(spec=LoggerFactory)
    mocked_factory.setup_logger.return_value = mock_logger
    yield mocked_factory


@fixture
def mock_http_requester():
    # Using MagicMock instead of create_autospec as partial_func confuses autospec
    mocked_requester = MagicMock()
    yield mocked_requester


@fixture
def mock_kms_client():
    mocked_client = MagicMock()
    yield mocked_client


@fixture
def mock_tmna_client_service():
    mocked_tmna_service = create_autospec(spec=TmnaService)
    yield mocked_tmna_service


@fixture
def mock_wirelesscar_client_service():
    mocked_wirelesscar_service = create_autospec(spec=WirelessCarService)
    yield mocked_wirelesscar_service

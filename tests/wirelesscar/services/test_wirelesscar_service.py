from unittest.mock import patch

import pytest
from src.config.wirelesscar_config import WirelessCarConfig
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.wirelesscar.services.wirelesscar_service import WirelessCarService

BASE_URL = "fooBaseURL"
API_KEY = "fooAPIKEY"
CALLCENTERID = "1000"
PROGRAMID = "2142"


@pytest.fixture
def setup_wirelesscar_service():
    uut = WirelessCarService(
        config=WirelessCarConfig(
            base_url=BASE_URL,
            wirelesscar_api_key=API_KEY,
            wirelesscar_raw_api_key=API_KEY,
            callcenter_id=CALLCENTERID,
            program_id=PROGRAMID,
        ),
    )
    yield uut


# Not implemented abstract method tests
def test_wirelesscar_serivce_on_calling_save_vehicledata_raise_notimplementedexception(
    setup_wirelesscar_service, mock_logger
):
    with pytest.raises(Exception) as execinfo:
        setup_wirelesscar_service.save_vehicledata(any)
    assert execinfo.type == NotImplementedError


def test_wirelesscar_serivce_on_calling_get_vehicledata_raise_notimplementedexception(
    setup_wirelesscar_service, mock_logger
):
    with pytest.raises(Exception) as execinfo:
        setup_wirelesscar_service.get_vehicledata("1234567890", ProgramCode.SUBARU)
    assert execinfo.type == NotImplementedError


def test_wirelesscar_serivce_on_calling_assign_agent_raise_notimplementedexception(
    setup_wirelesscar_service, mock_logger
):
    with pytest.raises(Exception) as execinfo:
        setup_wirelesscar_service.assign_agent(any)
    assert execinfo.type == NotImplementedError


def test_wirelesscar_serivce_on_calling_terminate_raise_notimplementedexception(
    setup_wirelesscar_service, mock_logger
):
    with pytest.raises(Exception) as execinfo:
        setup_wirelesscar_service.terminate(any)
    assert execinfo.type == NotImplementedError


def test_wirelesscar_serivce_on_calling_populate_vehicledata_raise_notimplementedexception(
    setup_wirelesscar_service, mock_logger
):
    with pytest.raises(Exception) as execinfo:
        setup_wirelesscar_service.populate_vehicledata(any)
    assert execinfo.type == NotImplementedError


def test_wirelesscar_serivce_on_calling_health_raise_notimplementedexception(
    setup_wirelesscar_service,
):
    with pytest.raises(Exception) as execinfo:
        setup_wirelesscar_service.health(ProgramCode.SUBARU, CtsVersion.TWO_DOT_ZERO)
    assert execinfo.type == NotImplementedError

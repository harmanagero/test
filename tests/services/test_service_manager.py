from unittest.mock import call, patch

import pytest
from pytest import fixture
from src.config.aeris_config import AerisConfig
from src.config.fca_config import FcaConfig
from src.config.siriusxm_config import SiriusXmConfig
from src.config.tmna_config import TmnaConfig
from src.config.verizon_config import VerizonConfig
from src.config.vodafone_config import VodafoneConfig
from src.config.wirelesscar_config import WirelessCarConfig
from src.models.enums.ctsversion_type import CtsVersion
from src.models.enums.programcode_type import ProgramCode
from src.services.service_manager import setup_service_manager


@fixture
def patched_setup_config_manager(mock_config_manager):
    with patch(
        "src.services.service_manager.setup_config_manager", autospec=True
    ) as mocked_setup:
        mocked_setup.return_value = mock_config_manager
        yield mocked_setup


@fixture
def patched_get_main_table():
    with patch(
        "src.services.service_manager.get_main_table", autospec=True
    ) as mocked_get_main_table:
        yield mocked_get_main_table


@fixture
def patched_get_supplement_table():
    with patch(
        "src.services.service_manager.get_supplement_table", autospec=True
    ) as mocked_get_supplement_table:
        yield mocked_get_supplement_table


@fixture
def patched_siriusxm_client_service_class(mock_siriusxm_client_service):
    with patch(
        "src.services.service_manager.SiriusXmService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_siriusxm_client_service
        yield mock_client_service


@fixture
def patched_fca_client_service_class(mock_fca_client_service):
    with patch(
        "src.services.service_manager.FcaService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_fca_client_service
        yield mock_client_service


@fixture
def patched_verizon_client_service_class(mock_verizon_client_service):
    with patch(
        "src.services.service_manager.VerizonService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_verizon_client_service
        yield mock_client_service


@fixture
def patched_aeris_client_service_class(mock_aeris_client_service):
    with patch(
        "src.services.service_manager.AerisService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_aeris_client_service
        yield mock_client_service


@fixture
def patched_vodafone_client_service_class(mock_vodafone_client_service):
    with patch(
        "src.services.service_manager.VodafoneService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_vodafone_client_service
        yield mock_client_service


@fixture
def patched_tmna_client_service_class(mock_tmna_client_service):
    with patch(
        "src.services.service_manager.TmnaService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_tmna_client_service
        yield mock_client_service


@fixture
def patched_wirelesscar_client_service_class(mock_wirelesscar_client_service):
    with patch(
        "src.services.service_manager.WirelessCarService", autospec=True
    ) as mock_client_service:
        mock_client_service.return_value = mock_wirelesscar_client_service
        yield mock_client_service


@fixture
def service_manager_mock_setup(
    patched_setup_config_manager,
    patched_get_main_table,
    patched_get_supplement_table,
    patched_siriusxm_client_service_class,
    patched_fca_client_service_class,
    patched_verizon_client_service_class,
    patched_aeris_client_service_class,
    patched_vodafone_client_service_class,
    patched_tmna_client_service_class,
    patched_wirelesscar_client_service_class,
):
    yield


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [
        ("nissan", None),
        ("infiniti", None),
        ("fca", None),
        ("vwcarnet", CtsVersion.ONE_DOT_ZERO),
        ("vwcarnet", CtsVersion.TWO_DOT_ZERO),
        ("porsche", CtsVersion.ONE_DOT_ZERO),
        ("toyota", CtsVersion.ONE_DOT_ZERO),
        ("toyota", CtsVersion.TWO_DOT_ZERO),
        ("subaru", CtsVersion.TWO_DOT_ZERO),
    ],
    ids=[
        "Nissan",
        "Infiniti",
        "Fca",
        "Verizon",
        "Aeris",
        "Porsche",
        "Siriusxm",
        "Tmna",
        "Subaru",
    ],
)
def test_setup_service_manager_calls_setup_config_manager_as_expected(
    service_manager_mock_setup, patched_setup_config_manager, programcode, ctsversion
):
    setup_service_manager(programcode, ctsversion)
    patched_setup_config_manager.assert_called_once_with()


### Retrieve Config - Block Start
@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti"], ids=["Nissan", "Infiniti"]
)
def test_setup_service_manager_calls_config_manager_retrieve_siriusxm_config_as_expected(
    service_manager_mock_setup, mock_config_manager, programcode
):
    setup_service_manager(programcode)
    mock_config_manager.retrieve_config.assert_has_calls([call(SiriusXmConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_fca_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("fca")
    mock_config_manager.retrieve_config.assert_has_calls([call(FcaConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_verizon_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("vwcarnet", CtsVersion.ONE_DOT_ZERO)
    mock_config_manager.retrieve_config.assert_has_calls([call(VerizonConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_aeris_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("vwcarnet", CtsVersion.TWO_DOT_ZERO)
    mock_config_manager.retrieve_config.assert_has_calls([call(AerisConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_vodafone_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("porsche", CtsVersion.ONE_DOT_ZERO)
    mock_config_manager.retrieve_config.assert_has_calls([call(VodafoneConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_siriusxm_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("toyota", CtsVersion.ONE_DOT_ZERO)
    mock_config_manager.retrieve_config.assert_has_calls([call(SiriusXmConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_tmna_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("toyota", CtsVersion.TWO_DOT_ZERO)
    mock_config_manager.retrieve_config.assert_has_calls([call(TmnaConfig)])


def test_setup_service_manager_calls_config_manager_retrieve_wirelesscar_config_as_expected(
    service_manager_mock_setup, mock_config_manager
):
    setup_service_manager("subaru", CtsVersion.TWO_DOT_ZERO)
    mock_config_manager.retrieve_config.assert_has_calls([call(WirelessCarConfig)])


### Retrieve Config - Block End


### Create service - Block Start
@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti"], ids=["Nissan", "Infiniti"]
)
def test_setup_service_manager_creates_siriusxm_service_as_expected(
    service_manager_mock_setup,
    patched_siriusxm_client_service_class,
    patched_get_main_table,
    mock_config_manager,
    programcode,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    patched_get_main_table.return_value = "foo"
    setup_service_manager(programcode)
    patched_siriusxm_client_service_class.assert_called_once_with(
        config="fooConfig", table="foo"
    )


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("fca", CtsVersion.ONE_DOT_ZERO), ("fca", "")],
    ids=["FCA_InputVersion", "FCA_EmptyVersion"],
)
def test_setup_service_manager_creates_fca_service_as_expected(
    service_manager_mock_setup,
    patched_fca_client_service_class,
    patched_get_main_table,
    patched_get_supplement_table,
    mock_config_manager,
    programcode,
    ctsversion,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    patched_get_main_table.return_value = "foo"
    patched_get_supplement_table.return_value = "foosupplement"
    setup_service_manager(programcode, ctsversion)
    patched_fca_client_service_class.assert_called_once_with(
        config="fooConfig",
        table="foo",
        supplementtable="foosupplement",
    )


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", CtsVersion.ONE_DOT_ZERO), ("vwcarnet", "")],
    ids=["Verizon_InputVersion", "Verizon_EmptyVersion"],
)
def test_setup_service_manager_creates_verizon_service_as_expected(
    service_manager_mock_setup,
    patched_verizon_client_service_class,
    patched_get_main_table,
    patched_get_supplement_table,
    mock_config_manager,
    programcode,
    ctsversion,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    patched_get_main_table.return_value = "foo"
    patched_get_supplement_table.return_value = "foosupplement"
    setup_service_manager(programcode, ctsversion)
    patched_verizon_client_service_class.assert_called_once_with(
        config="fooConfig",
        table="foo",
        supplementtable="foosupplement",
    )


def test_setup_service_manager_creates_aeris_service_as_expected(
    service_manager_mock_setup,
    patched_aeris_client_service_class,
    mock_config_manager,
    patched_get_main_table,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    patched_get_main_table.return_value = "foo"
    setup_service_manager("vwcarnet", CtsVersion.TWO_DOT_ZERO)
    patched_aeris_client_service_class.assert_called_once_with(
        config="fooConfig", table="foo"
    )


def test_setup_service_manager_creates_vodafone_service_as_expected(
    service_manager_mock_setup,
    patched_vodafone_client_service_class,
    patched_get_main_table,
    patched_get_supplement_table,
    mock_config_manager,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    patched_get_main_table.return_value = "foo"
    patched_get_supplement_table.return_value = "foosupplement"
    setup_service_manager("porsche")
    patched_vodafone_client_service_class.assert_called_once_with(
        config="fooConfig",
        table="foo",
        supplementtable="foosupplement",
    )


def test_setup_service_manager_creates_siriusxm_service_as_expected(
    service_manager_mock_setup,
    patched_siriusxm_client_service_class,
    patched_get_main_table,
    mock_config_manager,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    patched_get_main_table.return_value = "foo"
    setup_service_manager(ProgramCode.TOYOTA, CtsVersion.ONE_DOT_ZERO)
    patched_siriusxm_client_service_class.assert_called_once_with(
        config="fooConfig", table="foo"
    )


def test_setup_service_manager_creates_tmnna_service_as_expected(
    service_manager_mock_setup,
    patched_tmna_client_service_class,
    mock_config_manager,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    setup_service_manager("toyota", CtsVersion.TWO_DOT_ZERO)
    patched_tmna_client_service_class.assert_called_once_with(
        config="fooConfig",
    )


def test_setup_service_manager_creates_wirelesscar_service_as_expected(
    service_manager_mock_setup,
    patched_wirelesscar_client_service_class,
    mock_config_manager,
):
    mock_config_manager.retrieve_config.return_value = "fooConfig"
    setup_service_manager("subaru", CtsVersion.TWO_DOT_ZERO)
    patched_wirelesscar_client_service_class.assert_called_once_with(config="fooConfig")


### Create service - Block End

### Create Service Manager - Block Start
@pytest.mark.parametrize(
    "programcode", ["nissan", "infiniti"], ids=["Nissan", "Infiniti"]
)
def test_setup_service_manager_siriusxm_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_siriusxm_client_service, programcode
):
    service_manager = setup_service_manager(programcode)
    assert service_manager.client_service == mock_siriusxm_client_service


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("fca", CtsVersion.ONE_DOT_ZERO), ("fca", "")],
    ids=["FCA_InputVersion", "FCA_EmptyVersion"],
)
def test_setup_service_manager_fca_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_fca_client_service, programcode, ctsversion
):
    service_manager = setup_service_manager(programcode, ctsversion)
    assert service_manager.client_service == mock_fca_client_service


@pytest.mark.parametrize(
    "programcode,ctsversion",
    [("vwcarnet", CtsVersion.ONE_DOT_ZERO), ("vwcarnet", "")],
    ids=["Verizon_InputVersion", "Verizon_EmptyVersion"],
)
def test_setup_service_manager_verizon_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_verizon_client_service, programcode, ctsversion
):
    service_manager = setup_service_manager(programcode, ctsversion)
    assert service_manager.client_service == mock_verizon_client_service


def test_setup_service_manager_aeris_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_aeris_client_service
):
    service_manager = setup_service_manager(
        ProgramCode.VWCARNET, CtsVersion.TWO_DOT_ZERO
    )
    assert service_manager.client_service == mock_aeris_client_service


def test_setup_service_manager_porsche_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_vodafone_client_service
):
    service_manager = setup_service_manager("porsche")
    assert service_manager.client_service == mock_vodafone_client_service


def test_setup_service_manager_porsche_with_version_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_vodafone_client_service
):
    service_manager = setup_service_manager("porsche", "1.0")
    assert service_manager.client_service == mock_vodafone_client_service


def test_setup_service_manager_toyota_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_siriusxm_client_service
):
    service_manager = setup_service_manager("toyota")
    assert service_manager.client_service == mock_siriusxm_client_service


def test_setup_service_manager_toyota_with_version_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_tmna_client_service
):
    service_manager = setup_service_manager("toyota", "2.0")
    assert service_manager.client_service == mock_tmna_client_service


def test_setup_service_manager_subaru_with_version_creates_service_manager_as_expected(
    service_manager_mock_setup, mock_wirelesscar_client_service
):
    service_manager = setup_service_manager("subaru", "2.0")
    assert service_manager.client_service == mock_wirelesscar_client_service


### Create Service Manager - Block End

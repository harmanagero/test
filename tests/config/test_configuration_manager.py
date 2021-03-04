from unittest.mock import call
from unittest.mock import patch

from agero_python_configuration import ConfigManager
from pytest import fixture

from src.config.configuration_manager import setup_config_manager
from src.config.dynamo_config import DynamoConfig
from src.config.echo_config import EchoConfig
from src.config.logger_config import LoggerConfig


@fixture
def patched_config_manager_class(mock_config_manager):
    with patch(
        "src.config.configuration_manager.ConfigManager", autospec=True
    ) as patched_manager:
        patched_manager.return_value = mock_config_manager
        yield patched_manager


def test_setup_config_manager_creates_config_manager_as_expected(
    monkeypatch, patched_config_manager_class
):
    monkeypatch.setenv("logging__environment", "fooEnvironment")
    setup_config_manager()
    patched_config_manager_class.assert_called_once_with(
        config_environment="fooEnvironment"
    )


def test_setup_config_manager_registers_config_as_expected(
    patched_config_manager_class, mock_config_manager
):
    setup_config_manager()
    calls = [
        call(config_class=LoggerConfig, key="logging"),
        call(config_class=EchoConfig, key="echo"),
        call(config_class=DynamoConfig, key="dynamo"),
    ]
    mock_config_manager.register_config.assert_has_calls(calls)


def test_setup_config_manager_returns_config_manager_as_expected(
    patched_config_manager_class
):
    response = setup_config_manager()
    assert isinstance(response, ConfigManager)

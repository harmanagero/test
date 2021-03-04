from logging import CRITICAL
from logging import getLogger
from unittest.mock import patch

from pytest import fixture

from src import __version__
from src.config.logger_config import LoggerConfig
from src.utilities.logging import LoggerFactory
from src.utilities.logging import setup_root_logger


@fixture
def patched_agero_python_logger_extend():
    with patch(
        "src.utilities.logging.agero_python_logger.extend", autospec=True
    ) as patched_extend:
        yield patched_extend


@fixture
def patched_agero_python_logger_setup_logger(mock_logger):
    with patch(
        "src.utilities.logging.agero_python_logger.setup_logging", autospec=True
    ) as patched_setup_logger:
        patched_setup_logger.return_value = mock_logger
        yield patched_setup_logger


def test_setup_root_logger_calls_extend_as_expected(patched_agero_python_logger_extend):
    setup_root_logger()
    patched_agero_python_logger_extend.assert_called_once_with(
        getLogger(), should_attach_handler=True
    )


def test_logger_factory_setup_logger_calls_agero_logger_setup_logger_as_expected(
    patched_agero_python_logger_setup_logger
):
    config = LoggerConfig(
        environment="fooEnvironment",
        application_name="fooApplicationName",
        global_log_level="critical",
    )
    uut = LoggerFactory(config)
    uut.setup_logger()
    patched_agero_python_logger_setup_logger.assert_called_once_with(
        log_level="CRITICAL",
        environment="fooEnvironment",
        application_name="fooApplicationName",
        version=__version__,
    )

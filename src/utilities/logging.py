import logging

import agero_python_logger

from src import __version__
from src.config.logger_config import LoggerConfig


def setup_root_logger():
    agero_python_logger.extend(logging.getLogger(), should_attach_handler=True)


class LoggerFactory:
    def __init__(self, config: LoggerConfig):
        self._config = config

    def setup_logger(self):
        return agero_python_logger.setup_logging(
            log_level=self._config.global_log_level.upper(),
            environment=self._config.environment,
            application_name=self._config.application_name,
            version=__version__,
        )

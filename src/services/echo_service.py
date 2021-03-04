from logging import ERROR, Logger
from src.config.echo_config import EchoConfig
from src.models.domain.echo import Echo
from src.models.exceptions.application_exception import ApplicationException
import requests


class EchoService:
    def __init__(self, logger: Logger,  config: EchoConfig):
        self._logger = logger
        # self._http = requester
        self._config = config

    #todo: update _http with requests
    def echo(self, sanitized_query: str, should_error: bool) -> Echo:
        if should_error:
            self._logger.error("You told me to error", extra={"foo": "bar"})
            raise ApplicationException("Something Bad")
        else:
            headers = self._http.make_headers(
                basic_auth=f"{self._config.raw_username}:{self._config.raw_password}"
            )
            try:
                response = self._http.get(
                    f"{self._config.url}?{sanitized_query}",
                    response_type=Echo,
                    headers=headers,
                )
                return response
            except ERROR:
                self._logger.error("Gateway error", exc_info=True, stack_info=True)
                raise ApplicationException("Something Bad")

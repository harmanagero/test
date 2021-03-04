from typing import Optional

from agero_python_configuration import BaseConfig

# from pydantic import validator


class SiriusXmConfig(BaseConfig):
    base_url: Optional[str]
    api_key: Optional[str]
    raw_apikey: Optional[str]
    root_cert: Optional[str]
    wsdl: Optional[str]

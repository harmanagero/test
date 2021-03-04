from typing import Optional
from agero_python_configuration import BaseConfig


class TmnaConfig(BaseConfig):
    base_url: Optional[str]
    terminate_url: Optional[str]
    root_cert: Optional[str]
from typing import Optional

from agero_python_configuration import BaseConfig


class DynamoConfig(BaseConfig):
    table_name: Optional[str]
    supplement_table_name: Optional[str]
    endpoint: Optional[str]

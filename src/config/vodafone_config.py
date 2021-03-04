from typing import Optional
from agero_python_configuration import BaseConfig


class VodafoneConfig(BaseConfig):
    dynamo_table_name: Optional[str]
    dynamo_supplement_table_name: Optional[str]
from typing import Optional
from agero_python_configuration import BaseConfig


class AerisConfig(BaseConfig):
    base_url: Optional[str]
    root_cert: Optional[str]
    dynamo_table_name: Optional[str]
    dynamodb_check_enable: Optional[bool]
    dynamodb_check_timelimit: Optional[int]
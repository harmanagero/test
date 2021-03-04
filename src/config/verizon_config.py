from typing import Optional

from agero_python_configuration import BaseConfig

# from pydantic import validator
# from src.utilities.decrypt import decrypt_secret


class VerizonConfig(BaseConfig):
    base_url: Optional[str]
    root_cert: Optional[str]
    wsdl: Optional[str]
    dynamo_table_name: Optional[str]
    dynamo_supplement_table_name: Optional[str]
    dynamodb_check_enable: Optional[bool]
    dynamodb_check_timelimit: Optional[int]

    # @validator("api_key")
    # def populate_raw_api_key_if_not_present(cls, v, values):
    #     if not values.get("api_key"):
    #         try:
    #             values["api_key"] = decrypt_secret(v)
    #         except Exception:
    #             raise ValueError("Unable to decrypt api_key")

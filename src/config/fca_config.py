from typing import Optional

from agero_python_configuration import BaseConfig
from pydantic import validator

from src.utilities.decrypt import decrypt_secret


class FcaConfig(BaseConfig):
    base_url: Optional[str]
    raw_api_key: Optional[str]
    api_key: Optional[str]
    dynamo_table_name: Optional[str]
    dynamo_supplement_table_name: Optional[str]
    bcall_data_url: Optional[str]
    terminate_bcall_url: Optional[str]
    max_retries: Optional[int]
    delay_for_each_retry: Optional[int]
    max_ani_length: Optional[int]
    api_gateway_base_path: Optional[str]
    root_cert: Optional[str]

    @validator("api_key")
    def populate_raw_api_key_if_not_present(cls, v, values):
        if not values.get("raw_api_key"):
            try:
                values["raw_api_key"] = decrypt_secret(v)
            except Exception as e:
                raise ValueError("Unable to decrypt api_key.{}".format(e))
        return v

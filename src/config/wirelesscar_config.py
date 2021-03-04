from typing import Optional

from agero_python_configuration import BaseConfig
from pydantic import validator

from src.utilities.decrypt import decrypt_secret


class WirelessCarConfig(BaseConfig):
    base_url: Optional[str]
    wirelesscar_raw_api_key: Optional[str] # wirelesscar_raw_api_key is the key to be used while calling the service
    wirelesscar_api_key: Optional[str] 
    callcenter_id: Optional[str]
    program_id: Optional[str]


    @validator("wirelesscar_api_key")
    def populate_wirelesscar_raw_api_key_if_not_present(cls, v, values):
        if not values.get("wirelesscar_raw_api_key"):
            try:
                values["wirelesscar_raw_api_key"] = decrypt_secret(v)
            except Exception as e:
                raise ValueError("Unable to decrypt wirelesscar_api_key.{}".format(e))
        return v

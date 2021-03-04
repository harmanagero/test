from typing import Optional

from agero_python_configuration import BaseConfig
from pydantic import validator

from src.utilities.decrypt import decrypt_secret


class EchoConfig(BaseConfig):
    raw_username: Optional[str]
    username: str
    raw_password: Optional[str]
    password: str
    url: str

    # @validator("username")
    # def populate_raw_username_if_not_present(cls, v, values):
    #     if not values.get("raw_username"):
    #         try:
    #             values["raw_username"] = decrypt_secret(v)
    #         except Exception:
    #             raise ValueError("Unable to decrypt username")

    # @validator("password")
    # def populate_raw_password_if_not_present(cls, v, values):
    #     if not values.get("raw_password"):
    #         try:
    #             values["raw_password"] = decrypt_secret(v)
    #         except Exception:
    #             raise ValueError("Unable to decrypt password")

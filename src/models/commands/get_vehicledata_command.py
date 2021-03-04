from typing import Optional
from pydantic import BaseModel, Field
from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from src.models.enums.programcode_type import ProgramCode
from src.models.enums.ctsversion_type import CtsVersion


class GetVehicleDataCommand(BaseModel):
    msisdn: str = Field(
        description="msisdn is associated with call that is received by call center. It stands for Mobile Station International Subscriber Directory Number and is required for callback incase call gets disconnected"
    )
    programcode: ProgramCode = Field(description="Program Code Type")
    ctsversion: Optional[CtsVersion] = Field(
        description="Program Version passed in input"
    )

    @validator("msisdn")
    def validate_msisdn(cls, v):
        if v is not None or len(v) > 0:
            v = v.replace("-", "")  # Remove hyphen
            v = v.replace("+", "") 
            v = v.replace("\"", "") 
            v = v.replace("\'", "") 
            v = v.replace(" ", "") 
        if v == "" or v == "None" or v is None or len(v) == 0:
            raise ValueError("Msisdn cannot be null or empty")
        if len(v) < 10:
            raise ValueError(
                "Msisdn character length should be minimum 10 digit numbers"
            )
        if not v.isdecimal():  # Dont allow msisdn if it is non numeric
            raise ValueError("Msisdn has non numeric characters")
        return v

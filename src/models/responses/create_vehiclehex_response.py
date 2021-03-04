from pydantic.fields import Field
from pydantic.main import BaseModel


class CreateVehicleHexData(BaseModel):
    """
    Vehicle Hex Data Response
    """

    VarName: str = Field("User-to-User", description="Variable Name")
    Value: str = Field(
        "Value", description="Hex Value of the  Latitude, longitude, reference id etc"
    )

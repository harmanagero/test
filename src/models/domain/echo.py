from typing import Dict

from pydantic import BaseModel
from pydantic import Field


class Echo(BaseModel):
    args: Dict[str, str] = Field(
        None, description="Represents the query strings used in the call"
    )
    headers: Dict[str, str] = Field(None, description="Represents the headers sent")
    url: str = Field(None, description="Represents the URL used to service the request")

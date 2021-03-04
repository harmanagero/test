from typing import Optional
from pydantic import BaseModel
from pydantic import Field


class HealthCheckResponse(BaseModel):
    success: bool = Field(
        None, description="Indicates whether the health check was successful"
    )
    responsemessage: Optional[str] = Field(description="Response message")


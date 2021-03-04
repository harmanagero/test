from pydantic import BaseModel
from pydantic import Field

from src.models.enums.status_type import Status


class CreateAgentAssignmentResponse(BaseModel):
    reference_id: str = Field(
        None, description="Passed reference ID for the agent assignment"
    )
    status: Status = Field(
        Status.UNKNOWN, description="Current status for the agent assignment"
    )
    agent_assigned: bool = Field(description="value for agent assignment.")

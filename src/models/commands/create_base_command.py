from abc import ABC

from pydantic import Field

from src.models.enums.programcode_type import ProgramCode


class CreateBaseCommand(ABC):
    programcode: ProgramCode = Field(description="Program Code Type")

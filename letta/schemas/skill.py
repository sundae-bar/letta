from typing import Optional

from pydantic import BaseModel, Field

from letta.schemas.enums import PrimitiveType
from letta.schemas.letta_base import LettaBase


class BaseSkill(LettaBase):
    __id_prefix__ = PrimitiveType.SKILL.value


class Skill(BaseSkill):
    """Representation of a skill that can be attached to an agent.

    Skills are SKILL.md files containing instructions and resources that agents
    can load on demand to improve performance on specialized tasks.
    """

    id: str = BaseSkill.generate_id_field()
    name: str = Field(..., description="The display name of the skill.")
    description: str = Field(..., description="Short description of when to use this skill.")
    content: str = Field(..., description="The full SKILL.md content including instructions and resources.")

    # Organization/project scoping
    organization_id: Optional[str] = Field(None, description="The unique identifier of the organization.")
    project_id: Optional[str] = Field(None, description="The unique identifier of the project.")


class CreateSkill(BaseModel):
    """Schema for creating a new skill."""

    name: str = Field(..., description="The display name of the skill.")
    description: str = Field(..., description="Short description of when to use this skill.")
    content: str = Field(..., description="The full SKILL.md content including instructions and resources.")


class UpdateSkill(BaseModel):
    """Schema for updating an existing skill."""

    name: Optional[str] = Field(None, description="The display name of the skill.")
    description: Optional[str] = Field(None, description="Short description of when to use this skill.")
    content: Optional[str] = Field(None, description="The full SKILL.md content including instructions and resources.")

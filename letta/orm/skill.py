from typing import TYPE_CHECKING, Optional

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from letta.orm.mixins import OrganizationMixin, ProjectMixin
from letta.orm.sqlalchemy_base import SqlalchemyBase
from letta.schemas.skill import Skill as PydanticSkill

if TYPE_CHECKING:
    from letta.orm.organization import Organization


class Skill(SqlalchemyBase, OrganizationMixin, ProjectMixin):
    """Represents a skill that can be attached to an agent.

    Skills are instructions and resources (SKILL.md files) that agents can load
    on demand to improve performance on specialized tasks. They follow the open
    Agent Skills standard and are framework-agnostic.
    """

    __tablename__ = "skills"
    __pydantic_model__ = PydanticSkill

    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uix_skill_name_organization"),
        Index("ix_skills_organization_id", "organization_id"),
        Index("ix_skills_created_at_name", "created_at", "name"),
    )

    name: Mapped[str] = mapped_column(String, doc="The display name of the skill.")
    description: Mapped[str] = mapped_column(String, doc="Short description of when to use this skill (~100 words).")
    content: Mapped[str] = mapped_column(Text, doc="The full SKILL.md content including instructions and resources.")

    # relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="skills", lazy="selectin")

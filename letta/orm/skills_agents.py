from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from letta.orm import Base


class SkillsAgents(Base):
    """Agents can have one or many skills associated with them."""

    __tablename__ = "skills_agents"
    __table_args__ = (
        UniqueConstraint("agent_id", "skill_id", name="unique_agent_skill"),
        Index("ix_skills_agents_skill_id", "skill_id"),
    )

    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

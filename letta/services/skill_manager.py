from typing import List, Optional

from sqlalchemy import select

from letta.orm.errors import NoResultFound
from letta.orm.skill import Skill as SkillModel
from letta.orm.skills_agents import SkillsAgents
from letta.otel.tracing import trace_method
from letta.schemas.skill import CreateSkill, Skill as PydanticSkill, UpdateSkill
from letta.schemas.user import User as PydanticUser
from letta.server.db import db_registry
from letta.utils import enforce_types


class SkillManager:
    """Manager class to handle business logic related to Skills."""

    @enforce_types
    @trace_method
    async def create_skill(self, skill_create: CreateSkill, actor: PydanticUser) -> PydanticSkill:
        """Create a new skill."""
        skill = PydanticSkill(
            name=skill_create.name,
            description=skill_create.description,
            content=skill_create.content,
            organization_id=actor.organization_id,
        )

        async with db_registry.async_session() as session:
            db_skill = SkillModel(**skill.model_dump(exclude_none=True))
            await db_skill.create_async(session, actor=actor)
            return db_skill.to_pydantic()

    @enforce_types
    @trace_method
    async def get_skill_by_id(self, skill_id: str, actor: PydanticUser) -> PydanticSkill:
        """Get a skill by ID."""
        async with db_registry.async_session() as session:
            skill = await SkillModel.read_async(session, identifier=skill_id, actor=actor)
            return skill.to_pydantic()

    @enforce_types
    @trace_method
    async def list_skills(
        self,
        actor: PydanticUser,
        after: Optional[str] = None,
        limit: Optional[int] = 50,
    ) -> List[PydanticSkill]:
        """List all skills for the actor's organization."""
        async with db_registry.async_session() as session:
            skills = await SkillModel.list_async(
                db_session=session,
                after=after,
                limit=limit,
                actor=actor,
            )
            return [s.to_pydantic() for s in skills]

    @enforce_types
    @trace_method
    async def update_skill(
        self, skill_id: str, skill_update: UpdateSkill, actor: PydanticUser
    ) -> PydanticSkill:
        """Update an existing skill."""
        async with db_registry.async_session() as session:
            skill = await SkillModel.read_async(session, identifier=skill_id, actor=actor)

            update_data = skill_update.model_dump(exclude_none=True)
            for key, value in update_data.items():
                setattr(skill, key, value)

            await skill.update_async(session, actor=actor)
            return skill.to_pydantic()

    @enforce_types
    @trace_method
    async def delete_skill(self, skill_id: str, actor: PydanticUser) -> None:
        """Delete a skill by ID."""
        async with db_registry.async_session() as session:
            skill = await SkillModel.read_async(session, identifier=skill_id, actor=actor)
            await skill.hard_delete_async(session, actor=actor)

    @enforce_types
    @trace_method
    async def list_skills_for_agent(self, agent_id: str, actor: PydanticUser) -> List[PydanticSkill]:
        """List all skills attached to an agent."""
        async with db_registry.async_session() as session:
            query = (
                select(SkillModel)
                .join(SkillsAgents, SkillsAgents.skill_id == SkillModel.id)
                .where(SkillsAgents.agent_id == agent_id)
                .where(SkillModel.organization_id == actor.organization_id)
            )
            result = await session.execute(query)
            skills = result.scalars().all()
            return [s.to_pydantic() for s in skills]

    @enforce_types
    @trace_method
    async def attach_skill_to_agent(
        self, skill_id: str, agent_id: str, actor: PydanticUser
    ) -> None:
        """Attach a skill to an agent."""
        async with db_registry.async_session() as session:
            # Verify skill exists and actor has access
            await SkillModel.read_async(session, identifier=skill_id, actor=actor)

            # Check if already attached
            existing = await session.execute(
                select(SkillsAgents).where(
                    SkillsAgents.agent_id == agent_id,
                    SkillsAgents.skill_id == skill_id,
                )
            )
            if existing.scalar_one_or_none():
                return  # Already attached

            association = SkillsAgents(agent_id=agent_id, skill_id=skill_id)
            session.add(association)
            await session.commit()

    @enforce_types
    @trace_method
    async def detach_skill_from_agent(
        self, skill_id: str, agent_id: str, actor: PydanticUser
    ) -> None:
        """Detach a skill from an agent."""
        async with db_registry.async_session() as session:
            result = await session.execute(
                select(SkillsAgents).where(
                    SkillsAgents.agent_id == agent_id,
                    SkillsAgents.skill_id == skill_id,
                )
            )
            association = result.scalar_one_or_none()
            if association is None:
                raise NoResultFound(f"Skill {skill_id} is not attached to agent {agent_id}")
            await session.delete(association)
            await session.commit()

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from letta.log import get_logger
from letta.orm.errors import NoResultFound
from letta.schemas.skill import CreateSkill, Skill, UpdateSkill
from letta.server.rest_api.dependencies import HeaderParams, get_headers, get_letta_server
from letta.server.server import SyncServer

router = APIRouter(prefix="/skills", tags=["skills"])

logger = get_logger(__name__)


@router.post("/", response_model=Skill, operation_id="create_skill")
async def create_skill(
    skill_create: CreateSkill,
    server: SyncServer = Depends(get_letta_server),
    headers: HeaderParams = Depends(get_headers),
):
    """Create a new skill."""
    actor = await server.user_manager.get_actor_or_default_async(actor_id=headers.actor_id)
    return await server.skill_manager.create_skill(skill_create, actor=actor)


@router.get("/", response_model=List[Skill], operation_id="list_skills")
async def list_skills(
    after: Optional[str] = None,
    limit: Optional[int] = 50,
    server: SyncServer = Depends(get_letta_server),
    headers: HeaderParams = Depends(get_headers),
):
    """List all skills."""
    actor = await server.user_manager.get_actor_or_default_async(actor_id=headers.actor_id)
    return await server.skill_manager.list_skills(actor=actor, after=after, limit=limit)


@router.get("/{skill_id}", response_model=Skill, operation_id="retrieve_skill")
async def retrieve_skill(
    skill_id: str,
    server: SyncServer = Depends(get_letta_server),
    headers: HeaderParams = Depends(get_headers),
):
    """Get a skill by ID."""
    actor = await server.user_manager.get_actor_or_default_async(actor_id=headers.actor_id)
    try:
        return await server.skill_manager.get_skill_by_id(skill_id, actor=actor)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Skill with id {skill_id} not found")


@router.patch("/{skill_id}", response_model=Skill, operation_id="update_skill")
async def update_skill(
    skill_id: str,
    skill_update: UpdateSkill,
    server: SyncServer = Depends(get_letta_server),
    headers: HeaderParams = Depends(get_headers),
):
    """Update a skill."""
    actor = await server.user_manager.get_actor_or_default_async(actor_id=headers.actor_id)
    try:
        return await server.skill_manager.update_skill(skill_id, skill_update, actor=actor)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Skill with id {skill_id} not found")


@router.delete("/{skill_id}", operation_id="delete_skill")
async def delete_skill(
    skill_id: str,
    server: SyncServer = Depends(get_letta_server),
    headers: HeaderParams = Depends(get_headers),
):
    """Delete a skill."""
    actor = await server.user_manager.get_actor_or_default_async(actor_id=headers.actor_id)
    try:
        await server.skill_manager.delete_skill(skill_id, actor=actor)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Skill with id {skill_id} not found")

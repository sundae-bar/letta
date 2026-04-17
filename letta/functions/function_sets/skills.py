from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from letta.schemas.agent import AgentState


async def load_skill(agent_state: "AgentState", skill_name: str) -> str:
    """Load a skill's full content into context. Use this when you need the
    detailed instructions and resources from a skill to complete a task.

    You can see which skills are available in the <available_skills> section
    of your system prompt. Call this tool with the skill name to load
    its full SKILL.md content.

    Args:
        skill_name: The name of the skill to load (as shown in available_skills)

    Returns:
        The full SKILL.md content for the requested skill, or an error message if not found
    """
    if not hasattr(agent_state, "skills") or not agent_state.skills:
        return "Error: No skills are attached to this agent."

    for skill in agent_state.skills:
        if skill.name == skill_name:
            return f"=== SKILL: {skill.name} ===\n\n{skill.content}"

    available = ", ".join(s.name for s in agent_state.skills)
    return f"Error: Skill '{skill_name}' not found. Available skills: {available}"

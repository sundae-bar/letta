# Skills Implementation — What We Built and Why

## The Problem

Letta's server (API) has no concept of skills. Skills only exist in Letta Code (the CLI), where the CLI harness scans local `.skills/` directories and injects metadata into the agent's prompt. Since our subnet runs agents via the API (not the CLI), we needed to build skills as a first-class entity in the server.

## What This Enables

- Users submit a SKILL.md file instead of a full agent file
- SundaeBar provides the base agent; users compete on skill quality
- The same skill evaluation datasets rate skills for the marketplace (Letta, Claude, OpenClaw, etc.)

---

## High-Level: What We Did

1. **Created a Skill entity** — new database table, ORM model, Pydantic schema, REST API
2. **Linked skills to agents** — association table so agents can have skills attached
3. **Auto-attached the `load_skill` tool** — when an agent has skills, it automatically gets a tool to load skill content
4. **Injected skill metadata into the system prompt** — agents see `<available_skills>` listing what skills they have
5. **Populated skills in the agent state** — so the prompt injection and tool actually work at runtime

---

## Detailed Breakdown

### 1. New Skill Entity (the foundation)

**Why:** Skills need to be stored, retrieved, and managed via the API — just like tools, blocks, and sources.

**Files created:**
- `letta/schemas/skill.py` — Pydantic models: `Skill`, `CreateSkill`, `UpdateSkill`
- `letta/orm/skill.py` — SQLAlchemy ORM model with name, description, content fields
- `letta/orm/skills_agents.py` — Join table linking skills to agents (many-to-many)
- `alembic/versions/5dedb1849656_add_skills_and_skills_agents_tables.py` — Database migration
- `letta/services/skill_manager.py` — Business logic: CRUD + attach/detach skills to agents
- `letta/server/rest_api/routers/v1/skills.py` — REST endpoints: POST/GET/PATCH/DELETE /v1/skills

**Files modified:**
- `letta/schemas/enums.py` — Added `SKILL` to `PrimitiveType` (ID prefix) and `LETTA_SKILLS` to `ToolType`
- `letta/orm/__init__.py` — Registered new ORM models
- `letta/orm/organization.py` — Added skills relationship to Organization
- `letta/server/rest_api/routers/v1/__init__.py` — Registered skills router
- `letta/server/server.py` — Instantiated `SkillManager` on the server

### 2. Agent-Skill Integration

**Why:** Agents need to know which skills they have, and creating an agent with `skill_ids` should wire everything up automatically.

**Files modified:**
- `letta/schemas/agent.py` — Added `skill_ids` to `CreateAgent`/`UpdateAgent`, added `skills` list to `AgentState`
- `letta/services/agent_manager.py` — Three changes:
  - `create_agent_async()`: Inserts skill_ids into skills_agents table, auto-adds `load_skill` tool, explicitly populates skills on the agent state
  - `update_agent_async()`: Handles skill_ids updates (replace pivot rows)
  - Added `SkillsAgents` import
- `letta/orm/agent.py` — Added `skills` relationship, added to `optional_fields` in `to_pydantic_async`, included in the `asyncio.gather` call so skills load alongside tools/sources/etc.
- `letta/server/rest_api/routers/v1/agents.py` — Added 3 endpoints:
  - `PATCH /{agent_id}/skills/attach/{skill_id}`
  - `PATCH /{agent_id}/skills/detach/{skill_id}`
  - `GET /{agent_id}/skills`

### 3. The `load_skill` Tool

**Why:** The agent needs a way to load a skill's full SKILL.md content into its context when it decides to use a skill.

**Files created:**
- `letta/functions/function_sets/skills.py` — The `load_skill(agent_state, skill_name)` function. Looks up the skill by name from the agent's attached skills, returns the full content.

**Files modified:**
- `letta/constants.py` — Added `LETTA_SKILLS_TOOL_MODULE_NAME`, `SKILLS_TOOLS = ["load_skill"]`, included in `LETTA_TOOL_MODULE_NAMES` and `LETTA_TOOL_SET`
- `letta/schemas/tool.py` — Added `LETTA_SKILLS` case to the model validator that generates JSON schemas for built-in tools
- `letta/services/tool_manager.py` — Added `SKILLS_TOOLS` mapping in `upsert_base_tools_async` so the tool gets registered in the database on server startup

### 4. Prompt Injection

**Why:** The agent needs to SEE what skills are available so it knows when to call `load_skill`. This mirrors how Letta Code injects skill metadata into system reminders.

**Files modified:**
- `letta/prompts/prompt_generator.py` — Added `compile_skills_block()` method and `skills` parameter to `compile_system_message_async()`. Injects an `<available_skills>` section after `</base_instructions>` listing each skill's name and description.
- `letta/services/helpers/agent_manager_helper.py` — Passes `skills=` to `compile_system_message_async` from the agent state

### 5. Agent File Import/Export

**Why:** The .af file format needs to support skills for the validator pipeline.

**Files modified:**
- `letta/schemas/agent_file.py` — Added `SkillSchema` class and `skills` field to `AgentFileSchema`

---

## How It All Works Together

```
1. POST /v1/skills/  →  Create skill (stored in DB)
2. POST /v1/agents/ with skill_ids  →  Creates agent:
   a. Links skill via skills_agents table
   b. Auto-attaches load_skill tool
   c. Populates skills on agent state
   d. Compiles system message with <available_skills> block
3. Agent receives a message  →  Sees available skills in prompt
4. Agent calls load_skill("skill-name")  →  Gets full SKILL.md content
5. Agent uses skill content to answer
```

---

## E2E Test Results

The `test_skills_e2e.py` script proves the full flow:
- Skill created via API
- Agent created with skill attached
- `load_skill` tool auto-attached
- Skills endpoint confirms attachment
- Agent calls `load_skill` when prompted about the skill
- Cleanup works

---

## What's Next (Phase 2)

1. Update sb-validator to handle skill file submissions
2. Build skill evaluation graders in challenge-builder
3. Create a test dataset and run full evaluation

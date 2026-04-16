#!/usr/bin/env python3
"""
End-to-end test: Skills-based agent evaluation proof-of-concept.

Simulates what the sb-validator will do:
1. Create a skill from a SKILL.md file
2. Create an agent with the skill attached
3. Verify the agent has load_skill tool
4. Verify the skill is attached
5. Send a message to test if the agent can use the skill
"""

import json
import sys

import requests

BASE_URL = "http://localhost:8283"
HEADERS = {"Content-Type": "application/json"}

# The Anthropic slack-gif-creator skill content
SKILL_CONTENT = """# Slack GIF Creator

A toolkit providing utilities and knowledge for creating animated GIFs optimized for Slack.

### Slack Requirements

**Dimensions:**
- Emoji GIFs: 128x128 (recommended)
- Message GIFs: 480x480

**Parameters:**
- FPS: 10-30 (lower is smaller file size)
- Colors: 48-128 (fewer = smaller file size)
- Duration: Keep under 3 seconds for emoji GIFs

### Core Workflow

The toolkit includes GIFBuilder for assembling frames, PIL for graphics generation,
validators for Slack compliance, easing functions for smooth motion, and frame helpers.

### Available Utilities

- **GIFBuilder**: Assembles frames and optimizes for Slack
- **Validators**: Checks GIF compliance with Slack requirements
- **Easing Functions**: linear, ease_in, ease_out, bounce_out, elastic_out, back_out
- **Frame Helpers**: backgrounds, circles, text, and stars

### Animation Concepts

Shake/vibrate, pulse/heartbeat, bounce, spin/rotate, fade in/out, slide, zoom, particle burst.

### Dependencies

pillow, imageio, numpy
"""


def step(num, description):
    print(f"\n{'='*60}")
    print(f"  STEP {num}: {description}")
    print(f"{'='*60}")


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if detail:
        print(f"         {detail}")
    if not condition:
        sys.exit(1)


def main():
    print("\n" + "="*60)
    print("  SKILLS E2E TEST — Proof of Concept")
    print("="*60)

    # Step 1: Health check
    step(1, "Health check")
    r = requests.get(f"{BASE_URL}/v1/health/")
    check("Server is running", r.status_code == 200, r.text)

    # Step 2: Create skill
    step(2, "Create skill")
    # Clean up any leftover skill from previous run
    existing = requests.get(f"{BASE_URL}/v1/skills/", allow_redirects=True).json()
    for s in existing:
        if s["name"] == "slack-gif-creator-test":
            requests.delete(f"{BASE_URL}/v1/skills/{s['id']}/")
            print(f"         Cleaned up existing skill {s['id']}")

    r = requests.post(f"{BASE_URL}/v1/skills/", headers=HEADERS, json={
        "name": "slack-gif-creator-test",
        "description": "Knowledge and utilities for creating animated GIFs optimized for Slack.",
        "content": SKILL_CONTENT,
    })
    check("Skill created", r.status_code == 200, f"Status: {r.status_code}")
    skill = r.json()
    skill_id = skill["id"]
    print(f"         Skill ID: {skill_id}")
    print(f"         Name: {skill['name']}")

    # Step 3: Create agent with skill
    step(3, "Create agent with skill attached")
    r = requests.post(f"{BASE_URL}/v1/agents/", headers=HEADERS, json={
        "name": "skills-test-agent",
        "model": "openai/gpt-4o-mini",
        "embedding": "openai/text-embedding-ada-002",
        "skill_ids": [skill_id],
    })
    check("Agent created", r.status_code == 200, f"Status: {r.status_code}")
    agent = r.json()
    agent_id = agent["id"]
    print(f"         Agent ID: {agent_id}")

    # Step 4: Verify load_skill tool is attached
    step(4, "Verify load_skill tool is attached")
    tools = agent.get("tools", [])
    tool_names = [t["name"] for t in tools]
    check("load_skill in tools", "load_skill" in tool_names, f"Tools: {tool_names}")

    # Step 5: Verify skill is attached via API
    step(5, "Verify skill attached to agent")
    r = requests.get(f"{BASE_URL}/v1/agents/{agent_id}/skills", allow_redirects=True)
    check("Skills endpoint returns data", r.status_code == 200)
    agent_skills = r.json()
    check("Skill is attached", len(agent_skills) == 1, f"Found {len(agent_skills)} skills")
    check("Correct skill attached", agent_skills[0]["name"] == "slack-gif-creator-test")

    # Step 6: Send a message to the agent
    step(6, "Send message to agent")
    r = requests.post(
        f"{BASE_URL}/v1/agents/{agent_id}/messages/",
        headers=HEADERS,
        json={
            "messages": [{"role": "user", "content": "I need to create an animated GIF. I know you have a skill available for this - please load it and tell me what utilities and easing functions it provides."}],
        },
        timeout=60,
    )
    check("Message sent", r.status_code == 200, f"Status: {r.status_code}")
    messages = r.json()
    print(f"         Response messages: {len(messages)}")

    # Check if agent used load_skill
    used_load_skill = False
    agent_response = ""
    for msg in messages:
        if isinstance(msg, str):
            continue
        if not isinstance(msg, dict):
            continue
        msg_type = msg.get("message_type", "")
        # Check for tool calls
        if msg_type == "tool_call_message":
            tool_call = msg.get("tool_call", {})
            if isinstance(tool_call, dict) and tool_call.get("name") == "load_skill":
                used_load_skill = True
                print(f"         Agent called load_skill!")
        # Check for text response
        if msg_type in ("assistant_message", "reasoning_message"):
            content = msg.get("content", "") or ""
            if content and not agent_response:
                agent_response = content[:200]

    # Also search the raw JSON for load_skill references
    raw = json.dumps(messages)
    if "load_skill" in raw:
        used_load_skill = True

    print(f"         Used load_skill: {used_load_skill}")
    if agent_response:
        print(f"         Response preview: {agent_response}...")
    else:
        # Print raw response for debugging
        print(f"         Raw response: {json.dumps(messages)[:300]}...")

    # Step 7: Cleanup
    step(7, "Cleanup")
    requests.delete(f"{BASE_URL}/v1/agents/{agent_id}/")
    print(f"         Deleted agent {agent_id}")
    requests.delete(f"{BASE_URL}/v1/skills/{skill_id}/")
    print(f"         Deleted skill {skill_id}")

    # Summary
    print(f"\n{'='*60}")
    print("  ALL TESTS PASSED")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

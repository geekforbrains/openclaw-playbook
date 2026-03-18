#!/usr/bin/env python3
"""Agent creator — scaffold a new OpenClaw agent.

Usage:
    create.py --id <agent-id> --name "Display Name" --emoji "🤖"
"""

import argparse
import json
import os
import sys

OPENCLAW_DIR = os.environ.get("OPENCLAW_STATE_DIR", os.path.expanduser("~/.openclaw"))

AGENTS_MD_TEMPLATE = """# {name} {emoji}

<One paragraph personality description.>

- **Vibe:** <one sentence tone/personality summary>
- **Context:** Running in team Slack

## Personality

<!-- Bullet list of personality traits, tone, quirks -->

## Role

<!-- Bold role label. Bullet list of responsibilities -->

## Other Agents

<!-- List other agents: emoji, name, one-line role summary -->

## Rules

<!-- Role-specific rules only. Shared rules are in SHARED.md -->
"""

MEMORY_MD_TEMPLATE = """# Long-Term Memory

_Curated. Updated over time._

---

## Setup & Context

- Installed via OpenClaw playbook setup
- Agent: {name} {emoji}

---

<!-- Add sections as you learn things worth persisting -->
"""


def main():
    parser = argparse.ArgumentParser(prog="create.py", description="Scaffold a new OpenClaw agent")
    parser.add_argument("--id", required=True, help="Agent identifier (lowercase, used everywhere)")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--emoji", default="🤖", help="Agent emoji")
    args = parser.parse_args()

    agent_id = args.id
    agent_name = args.name
    agent_emoji = args.emoji

    # Paths
    agent_base = os.path.join(OPENCLAW_DIR, "agents", agent_id)
    workspace = os.path.join(agent_base, "workspace")
    agent_dir = os.path.join(agent_base, "agent")

    # Check if already exists
    if os.path.exists(agent_base):
        print(json.dumps({"error": f"Agent directory already exists: {agent_base}"}))
        sys.exit(1)

    # Create directories
    dirs = ["memory", "cron", "skills", "output", "data", "tmp"]
    for d in dirs:
        os.makedirs(os.path.join(workspace, d), exist_ok=True)
    os.makedirs(agent_dir, exist_ok=True)

    # Write AGENTS.md
    agents_md = os.path.join(workspace, "AGENTS.md")
    with open(agents_md, "w") as f:
        f.write(AGENTS_MD_TEMPLATE.format(name=agent_name, emoji=agent_emoji))

    # Write MEMORY.md
    memory_md = os.path.join(workspace, "MEMORY.md")
    with open(memory_md, "w") as f:
        f.write(MEMORY_MD_TEMPLATE.format(name=agent_name, emoji=agent_emoji))

    # Generate config snippets
    env_name = agent_id.upper()
    config_entry = {
        "id": agent_id,
        "workspace": f"~/.openclaw/agents/{agent_id}/workspace",
        "agentDir": f"~/.openclaw/agents/{agent_id}/agent",
        "identity": {"name": agent_name, "emoji": agent_emoji},
    }

    binding_entry = {
        "agentId": agent_id,
        "match": {"channel": "slack", "accountId": agent_id},
    }

    slack_account = {
        agent_id: {
            "botToken": f"${{SLACK_BOT_TOKEN_{env_name}}}",
            "appToken": f"${{SLACK_APP_TOKEN_{env_name}}}",
        }
    }

    result = {
        "status": "created",
        "agent_id": agent_id,
        "workspace": workspace,
        "agent_dir": agent_dir,
        "files_created": ["AGENTS.md", "MEMORY.md"],
        "directories_created": dirs,
        "next_steps": {
            "1_add_to_agents_list": config_entry,
            "2_add_binding": binding_entry,
            "3_add_slack_account": slack_account,
            "4_add_to_env": [
                f"SLACK_BOT_TOKEN_{env_name}=",
                f"SLACK_APP_TOKEN_{env_name}=",
            ],
            "5_customize": "Edit AGENTS.md with personality, role, and other agents",
            "6_update_others": "Add this agent to every existing agent's AGENTS.md",
            "7_restart": "Restart the gateway",
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

---
name: agent-creator
description: Scaffold a new OpenClaw agent — creates workspace directories, config entry template, and starter files. Use when adding a new agent to an install.
metadata: { "openclaw": { "emoji": "🤖" } }
---

# Agent Creator

Scaffold a new agent with workspace directories, config template, and starter files.

## Scripts

### Create a new agent

```bash
python3 {baseDir}/scripts/create.py \
  --id <agent-id> \
  --name "Display Name" \
  --emoji "🤖"
```

This will:
1. Create workspace directories at `~/.openclaw/agents/<id>/workspace/{memory,cron,skills,output,data,tmp}`
2. Create agent directory at `~/.openclaw/agents/<id>/agent/`
3. Copy `AGENTS.md` and `MEMORY.md` templates into the workspace
4. Print the config JSON to add to `openclaw.json` (agents.list entry + binding + Slack account)
5. Print the `.env` variables to add

### Options

- `--id` — agent identifier (used everywhere: directory, config, Slack account)
- `--name` — display name shown in Slack
- `--emoji` — agent's signature emoji

## After running

1. Add the printed config JSON to `openclaw.json`
2. Add the printed env vars to `~/.openclaw/.env` and fill in the Slack tokens
3. Customize `AGENTS.md` in the new workspace with personality and role
4. Update every existing agent's `AGENTS.md` to list the new agent
5. Restart the gateway

## Conventions

For full agent setup conventions, fetch:
https://raw.githubusercontent.com/geekforbrains/openclaw-playbook/main/standards/guide.md

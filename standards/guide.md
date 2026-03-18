# Conventions Guide

How we structure and maintain OpenClaw multi-agent installs. This is the shared standard — generic enough for any install, specific enough to keep things consistent.

## Directory Structure

```
~/.openclaw/
├── .env                         # Secrets (auto-loaded by OpenClaw)
├── openclaw.json                # Main config
├── SHARED.md                    # Global prompt — injected into ALL agents
├── credentials/                 # Channel credentials (managed by OpenClaw)
├── identity/                    # Device identity (managed by OpenClaw)
├── logs/                        # Gateway logs (managed by OpenClaw)
├── skills/                      # Shared skills — available to ALL agents
└── agents/
    └── <agent-name>/
        ├── agent/               # Per-agent state (managed by OpenClaw)
        └── workspace/
            ├── AGENTS.md        # Personality, role, other agents
            ├── MEMORY.md        # Curated long-term memory
            ├── cron/            # Cron prompt files
            ├── memory/          # Daily logs (YYYY-MM-DD.md)
            ├── skills/          # Agent-specific skills
            ├── output/          # Finished deliverables
            ├── data/            # Persistent reference data
            └── tmp/             # Scratch space
```

## Naming Convention

The agent `id` in config, the `agents/<name>/` directory, and the Slack `accountId` must all match. No translation layer — the name is the name everywhere.

> OpenClaw may auto-create an empty `agents/main/` on startup (upstream default). Ignore it.

## Prompt Files

All workspace files are optional. With `skipBootstrap: true`, OpenClaw won't auto-create workspace files — you control exactly what exists.

| File | Location | Injected | Purpose |
|------|----------|----------|---------|
| `SHARED.md` | `~/.openclaw/` | Every turn | Install identity, team context, pointers to standards |
| `AGENTS.md` | Agent workspace | Every turn | Personality, role, other agents, agent-specific rules |
| `MEMORY.md` | Agent workspace | Every turn | Curated long-term memory |

**SHARED.md** (one file, all agents): install identity, team context, workspace conventions, pointers to standards and skills.

**AGENTS.md** (one per agent): personality, vibe, role, other agents, role-specific rules. Agent name and emoji come from `agents.list[].identity` in config.

**MEMORY.md** (one per agent): curated long-term memory. Agents append to this as they learn things worth persisting.

Upstream also supports `IDENTITY.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`, and `BOOTSTRAP.md` — we fold those concerns into `AGENTS.md` and `SHARED.md` to keep things simple.

## Workspace Directories

| Directory | Purpose |
|-----------|---------|
| `memory/` | Daily logs (`YYYY-MM-DD.md`). Append, don't overwrite. |
| `cron/` | Prompt files for cron jobs. One `.md` per job. |
| `skills/` | Per-agent skill scripts and definitions. |
| `output/` | Finished deliverables, organized by topic. |
| `data/` | Persistent reference data, exports, repos. |
| `tmp/` | Scratch space. Clean up after use. |

Create subdirectories as needed. Name files descriptively with dates when relevant (e.g. `output/reports/monthly-2026-03.md`).

## Adding an Agent

Every agent needs: a config entry, a workspace, and (for Slack) a dedicated app.

### 1. Config entry

Add to `agents.list` in `openclaw.json`:

```json
{
  "id": "agent-name",
  "workspace": "~/.openclaw/agents/agent-name/workspace",
  "agentDir": "~/.openclaw/agents/agent-name/agent",
  "identity": { "name": "Display Name", "emoji": "🤖" }
}
```

### 2. Workspace scaffold

```bash
mkdir -p ~/.openclaw/agents/<name>/workspace/{memory,cron,skills,output,data,tmp}
mkdir -p ~/.openclaw/agents/<name>/agent
```

Then create `AGENTS.md` in the workspace with personality, role, and other agents.

### 3. Slack app

Each agent gets its own Slack app for a distinct identity:

1. Create a Slack app with Socket Mode enabled
2. Required bot scopes: `chat:write`, `channels:history`, `channels:read`, `im:history`, `im:read`, `im:write`, `app_mentions:read`, `reactions:read`, `reactions:write`, `files:read`, `users:read`
3. Generate an App Token (`xapp-...`) with `connections:write` scope
4. Install the app — get Bot Token (`xoxb-...`)
5. Add tokens to `.env` as `SLACK_BOT_TOKEN_<NAME>` and `SLACK_APP_TOKEN_<NAME>`
6. Add to `channels.slack.accounts` in `openclaw.json`
7. Add a binding to route the account to the agent

### 4. Auth profile

`agents/<name>/agent/auth-profiles.json` is auto-created at first run. Don't pre-populate.

## Skills

Precedence (highest first):

1. `<workspace>/skills/` — per-agent
2. `~/.openclaw/skills/` — shared across all agents
3. Bundled skills (only those in `skills.allowBundled` are loaded)

Use shared skills for capabilities all agents need (Slack lookups, cron management). Use per-agent skills for role-specific tooling.

### Skill authoring — path patterns

Skills must be portable across agents and machines. Use the right path pattern for each kind of reference:

| What you're referencing | Pattern | Example |
|-------------------------|---------|---------|
| Skill-local files (tokens, config, assets) | `Path(__file__).resolve().parent.parent` | `xero_tokens.json` in the skill root |
| Install-level shared data | `OPENCLAW_STATE_DIR` env var | `~/.openclaw/shared/agency.db` |
| Workspace files (memory, cron, output) | Relative from cwd | `cron/morning-brief.md` |
| Other skills in same workspace | Relative from cwd | `skills/humi/scripts/main.py` |

**Key env vars for path resolution:**

- `OPENCLAW_STATE_DIR` — the install root (defaults to `~/.openclaw`). Use this for install-level data.
- `OPENCLAW_HOME` — overrides `$HOME` (affects tilde expansion). This is *not* the install root — don't confuse the two.
- `OPENCLAW_AGENT_DIR` — set by OpenClaw at runtime to the agent's state directory. Not the workspace.

When a cron job or agent turn runs, the working directory is the agent's workspace. Relative paths in prompts and scripts resolve from there.

**In SKILL.md**, use `{baseDir}` to reference the skill's own directory. OpenClaw substitutes this at load time:

```markdown
python3 {baseDir}/scripts/main.py sync
```

**Python pattern for skill-local files:**

```python
from pathlib import Path
SKILL_DIR = Path(__file__).resolve().parent.parent  # scripts/ -> skill root
TOKENS_FILE = SKILL_DIR / "tokens.json"
```

**Python pattern for install-level data:**

```python
from pathlib import Path
import os
STATE_DIR = Path(os.environ.get("OPENCLAW_STATE_DIR", str(Path.home() / ".openclaw")))
```

### Skill authoring — anti-patterns

- **Hardcoded absolute paths** (`/Users/me/.openclaw/...`) — breaks on other machines
- **`~/...` in Python** — tilde expansion is a shell feature; use `Path.home()` or `os.path.expanduser()`
- **`OPENCLAW_HOME` for install-level data** — use `OPENCLAW_STATE_DIR` instead; `OPENCLAW_HOME` overrides `$HOME`, not the state root
- **Duplicate data sources** (JSON file + DB table for the same data) — pick one source of truth
- **Cross-skill imports** — skills should be isolated and portable; the agent orchestrates between them, not the skills themselves

## Git Tracking

Track config changes in `~/.openclaw/` with git:

```bash
cd ~/.openclaw && git init
```

Recommended `.gitignore`:

```
.env
logs/
agents/*/sessions/
agents/*/workspace/.openclaw/
agents/*/workspace/.claude/
agents/*/workspace/state/
cron/state/
cron/runs/
browser/
memory/*.sqlite
*.bak
```

## Communication Style

- Be concise by default, thorough when it matters
- No filler phrases ("Great question!", "I'd be happy to help!")
- Use Slack threads — every thread is its own session
- Slack formatting: no markdown tables (use bullet lists), bold = `*single asterisks*`

## Git Conventions

- Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`, etc.)
- Never commit secrets or `.env` files

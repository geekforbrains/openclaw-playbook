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
├── skills/                      # Shared skills — only when multiple agents need them
└── agents/
    └── <agent-name>/
        ├── agent/               # Per-agent state (managed by OpenClaw)
        └── workspace/
            ├── AGENTS.md        # Role, scope, rules, other agents
            ├── MEMORY.md        # Curated long-term memory
            ├── cron/            # Cron prompt files
            ├── memory/          # Daily logs (YYYY-MM-DD.md)
            ├── skills/          # Agent-specific skills (default location)
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
| `SHARED.md` | `~/.openclaw/` | Every turn | Safety rules, team context, workspace layout |
| `AGENTS.md` | Agent workspace | Every turn | Role, scope, rules, other agents |
| `MEMORY.md` | Agent workspace | Every turn | Curated long-term memory |

**SHARED.md** (one file, all agents): safety rules, team context, workspace layout, pointers to standards.

**AGENTS.md** (one per agent): role, scope, rules, referrals to other agents. Uses frontmatter for metadata (name, emoji, description, vibe).

**MEMORY.md** (one per agent): curated long-term memory. Agents append as they learn things worth persisting.

### What NOT to put in prompt files

- **Tool descriptions** — tools are injected at runtime with name and description. Duplicating them in AGENTS.md adds noise and goes stale.
- **Full standards docs** — prompt files should be short. Point agents to standards URLs for reference, don't inline them.

## Workspace Directories

| Directory | Purpose |
|-----------|---------|
| `memory/` | Daily logs (`YYYY-MM-DD.md`). Append, don't overwrite. |
| `cron/` | Prompt files for cron jobs. One `.md` per job. |
| `skills/` | Agent-specific skills. Default location for new skills. |
| `output/` | Finished deliverables, organized by topic. |
| `data/` | Persistent reference data, exports, repos. |
| `tmp/` | Scratch space. Clean up after use. |

## Adding an Agent

Every agent needs: a config entry with tool policy, a workspace, and (for Slack) a dedicated app.

### 1. Config entry

Add to `agents.list` in `openclaw.json`. Start from the locked-down default and add only the tools the agent needs:

```json
{
  "id": "agent-name",
  "workspace": "~/.openclaw/agents/agent-name/workspace",
  "agentDir": "~/.openclaw/agents/agent-name/agent",
  "identity": { "name": "Display Name", "emoji": "🤖" },
  "tools": {
    "allow": ["message", "cron"],
    "deny": ["exec", "group:automation", "group:runtime", "sessions_spawn", "gateway"]
  }
}
```

### 2. Workspace scaffold

```bash
mkdir -p ~/.openclaw/agents/<name>/workspace/{memory,cron,skills,output,data,tmp}
mkdir -p ~/.openclaw/agents/<name>/agent
```

Then create `AGENTS.md` using the template format (see `templates/RESEARCHER.md` for example).

### 3. Update other agents

Add the new agent to the "Other Agents" section of every existing agent's `AGENTS.md`.

### 4. Slack app

Each agent gets its own Slack app for a distinct identity:

1. Create a Slack app with Socket Mode enabled
2. Required bot scopes: `chat:write`, `channels:history`, `channels:read`, `im:history`, `im:read`, `im:write`, `app_mentions:read`, `reactions:read`, `reactions:write`, `files:read`, `users:read`
3. Generate an App Token (`xapp-...`) with `connections:write` scope
4. Install the app — get Bot Token (`xoxb-...`)
5. Add tokens to `.env` as `SLACK_BOT_TOKEN_<NAME>` and `SLACK_APP_TOKEN_<NAME>`
6. Add to `channels.slack.accounts` in `openclaw.json`
7. Add a binding to route the account to the agent

## Skills

Precedence (highest first):

1. `<workspace>/skills/` — agent-specific (default)
2. `~/.openclaw/skills/` — shared across all agents
3. Bundled skills (only those in `skills.allowBundled` are loaded)

**Skills are agent-specific by default.** Place new skills in the agent's `workspace/skills/` directory. Only promote to `~/.openclaw/skills/` when multiple agents need the same skill.

Skills that reference scripts need `exec` in the agent's tool allowlist. Skills that reference plugin tools don't need `exec` — the agent calls the tool directly. Prefer plugin tools for constrained agents.

### Skill authoring — path patterns

| What you're referencing | Pattern | Example |
|-------------------------|---------|---------|
| Skill-local files | `Path(__file__).resolve().parent.parent` | `xero_tokens.json` in the skill root |
| Install-level shared data | `OPENCLAW_STATE_DIR` env var | `~/.openclaw/shared/agency.db` |
| Workspace files | Relative from cwd | `cron/morning-brief.md` |

In SKILL.md, use `{baseDir}` to reference the skill's own directory.

### Skill authoring — anti-patterns

- Hardcoded absolute paths — breaks on other machines
- `~/...` in Python — use `Path.home()` or `os.path.expanduser()`
- Cross-skill imports — skills should be isolated; the agent orchestrates between them

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

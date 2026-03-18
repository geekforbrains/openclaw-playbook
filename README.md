# OpenClaw Playbook

A reference standard, setup automation, and skill pack for OpenClaw multi-agent installs.

This repo serves three audiences:

1. **Humans** reading or sharing the standard with others
2. **Setup agents** bootstrapping a fresh install from scratch
3. **Running agents** referencing conventions day-to-day

## Quick start

```bash
git clone https://github.com/geekforbrains/openclaw-playbook.git
cd openclaw-playbook
./setup.sh
```

Setup scaffolds two agents — an **admin** (full access) and a **researcher** (constrained) — to demonstrate the security model. You fill in `.env` with your API keys and Slack tokens, tweak configs for your team, and you're running.

## Structure

```
setup.sh                              # Automated install bootstrap (macOS/Linux)

standards/                             # Source of truth — referenced by URL, not copied
  guide.md                             #   Organization, naming, workspace conventions
  config.md                            #   Config reference, tool policy, gateway security
  cron.md                              #   Cron conventions, delivery modes, gates
  safety.md                            #   Safety model — structural + behavioral

templates/                             # Copied + customized during setup
  openclaw.json                        #   Baseline config (admin + researcher agents)
  .env.example                         #   All env vars with placeholders
  SHARED.md                            #   Global prompt — safety, team context, workspace
  AGENTS.md                            #   Generic per-agent template
  ADMIN.md                             #   Admin agent template (full access)
  RESEARCHER.md                        #   Researcher agent template (constrained)
  MEMORY.md                            #   Memory seed structure

skills/                                # Shared skills — copied to ~/.openclaw/skills/
  cron-manager/                        #   Cron job conventions (guidance only, no scripts)

examples/                              # Reference only — not auto-deployed
  cron/                                #   Sample cron prompt templates
  scripts/                             #   Sample gate scripts
```

## Security Model

Agents are **locked down by default**. Every agent starts with all tools denied and capabilities are allowlisted per-agent based on role.

| Concept | Default | Open up when... |
|---------|---------|-----------------|
| Tools | All denied | Agent's role requires specific tools |
| Exec | Denied | Only for admin agent |
| Filesystem | Workspace only | Agent needs cross-workspace access |
| Gateway/cron management | Denied | Only for admin agent |
| Sub-agent spawning | Denied | Agent needs orchestration |

The admin agent has full access and can build plugin tools and skills for other agents. Constrained agents get only what they need — no exec, no shell, just their allowlisted tools and workspace.

See `standards/safety.md` for the full safety model and `standards/config.md` for tool policy configuration.

## How the pieces fit

### Standards (generic, lives in this repo)

The `standards/` directory defines how we structure and maintain OpenClaw installs. Running agents fetch the latest version from GitHub when they need to check conventions:

```
https://raw.githubusercontent.com/geekforbrains/openclaw-playbook/main/standards/guide.md
```

### Templates (copied + customized per install)

The `templates/` directory contains starting-point files that get personalized during setup. ADMIN.md and RESEARCHER.md show the two ends of the access spectrum — copy the one closest to your needs when adding new agents.

### Skills (shared across agents)

Skills in `skills/` get copied to `~/.openclaw/skills/` and are available to all agents. Agent-specific skills go in the agent's `workspace/skills/` directory instead.

Skills are **guidance only** by default (just a SKILL.md). For agents that need executable capabilities, favor plugin tools over exec-based scripts.

### Examples (browse, don't deploy)

Sample cron prompts and gate scripts. Reference these when creating new crons for your install.

## Adding an agent

1. Copy the closest template (ADMIN.md or RESEARCHER.md) and customize it
2. Add agent config to `openclaw.json` — start from deny-all, allowlist only needed tools
3. Scaffold the workspace: `mkdir -p ~/.openclaw/agents/<name>/workspace/{memory,cron,skills,output,data,tmp}`
4. Create a Slack app with its own tokens (see `standards/guide.md`)
5. Add a binding entry in config
6. Update every existing agent's "Other Agents" section in their AGENTS.md
7. Restart the gateway

## Patched fork

This playbook assumes the [patched OpenClaw fork](https://github.com/geekforbrains/openclaw). The `custom` branch adds:

| Patch | Purpose |
|-------|---------|
| `feat/cron-gate` | Gate option for deterministic pre-run checks |
| `feat/require-mention-threads` | Require @mention in threads |
| `feat/shared-bootstrap` | Load `~/.openclaw/SHARED.md` as global prompt |

Stock OpenClaw works too — you just won't have gates, thread mention control, or the shared bootstrap file.

## License

MIT

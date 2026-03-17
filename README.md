# OpenClaw Playbook

A reference standard, setup automation, and skill pack for OpenClaw multi-agent installs.

This repo serves three audiences:

1. **Humans** reading or sharing the standard with others
2. **Setup agents** bootstrapping a fresh install from scratch
3. **Running agents** referencing conventions and using skills day-to-day

## Quick start

```bash
git clone https://github.com/geekforbrains/openclaw-playbook.git
cd openclaw-playbook
./setup.sh
```

The setup script installs OpenClaw (patched fork), scaffolds `~/.openclaw/`, drops in config and templates, installs skills, and starts the gateway. You fill in `.env` with your API keys and Slack tokens, tweak `openclaw.json` for your agent's identity, and you're talking to your agent.

## Structure

```
setup.sh                              # Automated install bootstrap (macOS/Linux)

standards/                             # Source of truth — referenced by URL, not copied
  guide.md                             #   Organization, naming, workspace conventions
  config.md                            #   Config reference and key decisions
  cron.md                              #   Cron conventions, delivery modes, gates
  safety.md                            #   Safety rules for all agents

templates/                             # Copied + customized during setup
  openclaw.json                        #   Baseline config (one agent, stubs)
  .env.example                         #   All env vars with placeholders
  SHARED.md                            #   Global prompt — install identity + pointers
  AGENTS.md                            #   Per-agent personality template
  MEMORY.md                            #   Memory seed structure

skills/                                # Copied to ~/.openclaw/skills/ during setup
  slack-directory/                     #   Resolve Slack users/channels by name or ID
  cron-manager/                        #   Create and audit cron jobs per conventions
  system-audit/                        #   Audit install health and standards compliance
  agent-creator/                       #   Scaffold new agents (dirs, config, templates)

examples/                              # Reference only — not auto-deployed
  cron/                                #   Sample cron prompt templates
  scripts/                             #   Sample gate scripts
```

## How the pieces fit

### Standards (generic, lives in this repo)

The `standards/` directory defines how we structure and maintain OpenClaw installs. These docs are generic — not specific to any install. Running agents fetch the latest version from GitHub when they need to check conventions:

```
https://raw.githubusercontent.com/geekforbrains/openclaw-playbook/main/standards/guide.md
```

This avoids stale copies on disk. Standards evolve in one place and every install picks up changes automatically.

### Templates (copied + customized per install)

The `templates/` directory contains starting-point files that get personalized during setup. Once customized, the install's copy is authoritative — not the repo's.

### Skills (copied to install, kept aligned)

Skills in `skills/` get copied to `~/.openclaw/skills/` and are available to all agents. They provide deterministic tooling (Slack lookups, cron management, audits) so agents don't have to memorize conventions — the skills enforce them.

### Examples (browse, don't deploy)

Sample cron prompts and gate scripts. Reference these when creating new crons for your install. Every install's crons will be unique to their workload.

## Adding an agent

After initial setup with one agent, adding another is:

1. Add Slack bot + app tokens to `~/.openclaw/.env`
2. Copy the agent block in `openclaw.json` — change `id`, `identity`, tokens
3. Add a binding entry
4. Run the `agent-creator` skill (or manually: `mkdir -p ~/.openclaw/agents/<name>/workspace/{memory,cron,skills,output,data,tmp}`)
5. Customize `AGENTS.md` in the new workspace
6. Restart the gateway

See `standards/guide.md` for full conventions.

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

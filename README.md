# OpenClaw Playbook

A reference standard for OpenClaw multi-agent installs. Use it to bootstrap a new install or keep an existing one aligned over time.

This is a **guide, not an installer.** On an existing install, check structure and conventions — don't blindly overwrite files that may have been customized. The shared docs are starting templates; installs may diverge. The checklist defines *what should be true*, not a script to run mechanically.

Designed for humans and LLMs alike. You can point an agent at the checklist as a recurring audit — it reports what's drifted and what needs attention, without clobbering anything.

## Structure

```
checklist.md                       # Setup & alignment checklist
shared/                            # → ~/.openclaw/shared/
  guide.md                         #   Conventions — agents, workspaces, projects, crons
  config.md                        #   Config defaults and key decisions
  cron.md                          #   Cron job patterns and delivery modes
  safety.md                        #   Safety rules
cron/                              # → agent workspace/cron/ (customize per agent)
  daily_standup.md                 #   Orchestrator — morning project summary
  project_dev.md                   #   Developer — GitHub issue queue worker
  project_checkin.md               #   Orchestrator — project status check-in
  system_audit.md                  #   Self-healing system standards audit
scripts/                           # → agent workspace/scripts/
  gh_has_issues.sh                 #   Gate — only run if repo has labeled issues
  list_slack_channels.sh           #   Utility — fetch channel list from Slack API
```

## Setup

```bash
git clone <repo-url>
cd openclaw-playbook
```

Then follow [`checklist.md`](checklist.md). It walks through every step from shared docs to agent workspaces to cron jobs.

For a **new install**, work through the checklist in order — it bootstraps everything from scratch.

For an **existing install**, use the checklist as an audit. Check each item, note what's drifted, and decide what to fix. Don't assume every mismatch is wrong — some may be intentional customizations.

For **ongoing alignment**, set up a cron job that runs an agent against the checklist periodically. The agent can diff the install against the standard and report back (or auto-fix) as needed.

## Key conventions

- **Crons over heartbeat** — heartbeat is disabled. Isolated cron jobs are cheaper and more predictable.
- **Open by default** — Slack channels and DMs are open to all agents. Tighten per-channel with `requireMention`, not globally.
- **`NO_REPLY` for silent crons** — when there's nothing to report, the agent replies `NO_REPLY` to suppress delivery.
- **Gate scripts** — high-frequency crons check cheaply before waking the LLM.
- **Secrets in `.env`** — all API keys and tokens in one place, referenced via `${VAR}` in config.
- **UPPERCASE = injected** — `AGENTS.md`, `SOUL.md`, `USER.md`, etc. are auto-loaded by OpenClaw. Everything else lowercase.

## File naming

- **UPPERCASE.md** — auto-injected into agent context by OpenClaw every turn
- **lowercase.md** — reference docs read on demand

Injected files: `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md`, `MEMORY.md`, `BOOT.md`, `BOOTSTRAP.md`

Note the uppercase files are already created and maintained by OpenClaw. Noted here for clarity.

## License

MIT

# Setup & Alignment Checklist

A reference standard for OpenClaw installs. Each item describes *what should be true* — not a command to run blindly.

- **New install:** work through in order. Use the docs in `shared/` as templates to bootstrap files.
- **Existing install:** audit each item. A mismatch isn't necessarily wrong — it may be an intentional customization. Check structure and conventions; don't clobber content.
- **Recurring audit:** an agent can run this checklist periodically (e.g. via cron) to detect drift and report what needs attention.

---

## 1. Prerequisites

- [ ] OpenClaw is installed and `openclaw` CLI is available
- [ ] `~/.openclaw/` directory exists
- [ ] `~/.openclaw/.env` exists with at least one provider key, like `ANTHROPIC_API_KEY` set
- [ ] `gh` CLI is installed and authenticated (needed for dev crons)

## 2. Shared Docs

Copy playbook reference docs into the install. These are lowercase (not auto-injected). On existing installs, verify each installed file contains the playbook version's content — the playbook is the baseline spec. Additional install-specific content is expected and should not be flagged or removed.

- [ ] `~/.openclaw/shared/` directory exists
- [ ] Copy `shared/guide.md` → `~/.openclaw/shared/guide.md`
- [ ] Copy `shared/config.md` → `~/.openclaw/shared/config.md`
- [ ] Copy `shared/cron.md` → `~/.openclaw/shared/cron.md`
- [ ] Copy `shared/safety.md` → `~/.openclaw/shared/safety.md`
- [ ] `~/.openclaw/shared/USER.md` exists (UPPERCASE — this IS auto-injected). Create if missing with user's name, timezone, preferences.
- [ ] `~/.openclaw/shared/projects.md` exists (lowercase). Create empty `# Projects` file if no projects yet.
- [ ] `~/.openclaw/shared/channels.md` exists (lowercase). Create empty `# Slack Channels` file if no channels yet.
- [ ] `~/.openclaw/shared/browsers.md` exists if browser profiles are configured in `openclaw.json`. Lists each profile's purpose, logged-in accounts, and usage rules.
- [ ] Subdirectories exist: `shared/projects/`, `shared/research/` (create as needed)

> **Naming:** UPPERCASE = auto-injected by OpenClaw into every agent turn. lowercase = reference material, read on demand. Only `USER.md` is uppercase in `shared/`. See `guide.md` for the full list of injected workspace files.

## 3. Agent Defaults (`openclaw.json`)

Ref: `shared/config.md`

- [ ] `agents.defaults.model.primary` is set (e.g., `"heavy"`)
- [ ] `agents.defaults.models` defines aliases for `heavy`, `medium`, `light`
- [ ] `agents.defaults.heartbeat.every` is `"0m"` (disabled)
- [ ] `agents.defaults.memorySearch.enabled` is `true`
- [ ] `agents.defaults.memorySearch.extraPaths` includes the `shared/` directory
- [ ] `agents.defaults.maxConcurrent` is set (e.g., `4`)

## 4. Gateway (`openclaw.json`)

- [ ] `gateway.port` is set
- [ ] `gateway.mode` is `"local"`
- [ ] `gateway.bind` is `"loopback"`
- [ ] `gateway.auth.mode` is `"token"` with `token` referencing `${OPENCLAW_GATEWAY_TOKEN}`
- [ ] `OPENCLAW_GATEWAY_TOKEN` is set in `.env`

## 5. Channels (`openclaw.json`)

- [ ] `channels.slack.enabled` is `true`
- [ ] `channels.slack.mode` is `"socket"`
- [ ] `channels.slack.groupPolicy` is `"open"`
- [ ] `channels.slack.dmPolicy` is `"open"`
- [ ] `channels.slack.allowFrom` is `["*"]` (sibling of `dmPolicy`, not nested)
- [ ] `channels.slack.thread.historyScope` is `"thread"`
- [ ] `channels.slack.replyToModeByChatType` is set: `direct: "all"`, `group: "first"`, `channel: "first"` — threads channel replies under the original message for clean channels and isolated thread sessions
- [ ] `channels.slack.streaming` is `"partial"` (streams responses in Slack as they generate)
- [ ] `channels.slack.nativeStreaming` is `true` (uses Slack's native streaming API — requires `channel: "first"` threading to work)
- [ ] Per-channel `requireMention: true` set for noisy channels (e.g., `#general`)
- [ ] One account entry per agent in `channels.slack.accounts`
- [ ] Each account has `botToken` and `appToken` referencing `${VAR}` env vars
- [ ] All Slack tokens are set in `.env`

## 6. Sessions (`openclaw.json`)

- [ ] `session.dmScope` is `"per-channel-peer"`
- [ ] `session.threadBindings.enabled` is `true`
- [ ] `session.threadBindings.idleHours` is set (e.g., `24`)
- [ ] `session.maintenance.mode` is `"enforce"`
- [ ] `session.maintenance.pruneAfter` is set (e.g., `"30d"`)

## 7. Tools (`openclaw.json`)

- [ ] `tools.agentToAgent.enabled` is `true` (enables agent delegation)
- [ ] `tools.loopDetection.enabled` is `true`

## 8. Agent Setup

Repeat for each agent. Ref: `shared/guide.md` → Adding an Agent

### Config entry
- [ ] Agent exists in `agents.list` with `id`, `workspace`, `identity.name`, `identity.emoji`
- [ ] Default agent has `"default": true`
- [ ] `groupChat.mentionPatterns` includes the agent's Slack bot user ID (`<@UXXXXXXXXX>`)
- [ ] `subagents.allowAgents` follows delegation rules — the orchestrator (the `default: true` agent) reaches all others; specialists reach each other but not the orchestrator
- [ ] `tools.profile` is set (e.g., `"full"`)

### Binding
- [ ] Non-default agents have a binding routing their Slack account to them

### Workspace structure
- [ ] Workspace directory exists at the path in config
- [ ] Required UPPERCASE files (auto-injected): `AGENTS.md`, `HEARTBEAT.md`, `IDENTITY.md`, `MEMORY.md`, `SOUL.md`, `TOOLS.md`
- [ ] `USER.md` symlink → `shared/USER.md` (absolute path preferred, e.g. `/Users/<you>/.openclaw/shared/USER.md`)
- [ ] `shared/` symlink → `shared/` directory (absolute path preferred, e.g. `/Users/<you>/.openclaw/shared`)
- [ ] Required directories: `cron/`, `memory/`, `scripts/`, `skills/` (skills is scaffolding — agents put custom skills here; OpenClaw auto-discovers them. Prefer agent-level `skills/` over the shared `~/.openclaw/skills/` unless the skill is used by multiple agents.)

### AGENTS.md required content

Don't clobber a user's customized AGENTS.md — just verify it contains the essentials:

- [ ] Lists all other agents with name, role, and how to reach them (`sessions_spawn`)
- [ ] References shared docs: `shared/guide.md`, `shared/cron.md`, `shared/safety.md`, `shared/projects.md`, `shared/channels.md`
- [ ] Delegation rules are documented (who can reach whom)

## 9. Cron Jobs

Ref: `shared/cron.md`

These rules apply to all cron jobs — standard templates and custom ones alike. The goal is consistency: every job follows the same conventions regardless of when it was created.

For each cron job:
- [ ] Name is snake_case, agent-prefixed: `<agent>_<job>`
- [ ] Schedule uses `kind: "cron"` with a cron expression — not `kind: "every"` (interval-based). Flag any jobs using `"every"`.
- [ ] `sessionTarget` is `"isolated"`
- [ ] `model` and `thinking` are explicitly set (`heavy`/`high` for complex jobs like dev or audits; `medium`/`medium` or `light`/`off` for simple summaries and status checks)
- [ ] `message` tells the agent to read a prompt template — e.g., `"Read cron/project_dev.md for instructions."`. Keep `message` short; the real prompt lives in the file. This keeps `jobs.json` manageable and lets both humans and agents edit prompts without touching cron config.
- [ ] Prompt template exists at `workspace/cron/<name>.md` (multiple jobs can share one template)
- [ ] Delivery mode is set appropriately (see below)
- [ ] Announce-mode templates include `NO_REPLY` instructions (agent must reply `NO_REPLY` when there's nothing to report)

### Gate scripts
- [ ] Crons running more than once per hour have a gate script
- [ ] Gate scripts use absolute paths
- [ ] Gate scripts are executable (`chmod +x`)

## 10. Projects

For each project in `shared/projects.md`:
- [ ] Directory exists at `shared/projects/<name>/` with at least `brief.md`
- [ ] Active dev projects have an enabled dev agent cron
- [ ] Paused projects have their crons disabled

## 11. Version Control

Track config changes over time with a git repo in `~/.openclaw/`.

- [ ] `git init` in `~/.openclaw/` (if not already a repo)
- [ ] `.gitignore` excludes secrets and runtime state at minimum — each install can add more as needed:
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
  shared/projects/*/repos/
  shared/projects/*/media/
  memory/*.sqlite
  *.bak
  ```
- [ ] Optional: add a remote to back up config (`git remote add origin <url>`)
- [ ] Initial commit with current config

## 12. Standard Config

These are expected defaults for consistent behavior across installs. Deviations should be flagged — they may be intentional, but should be explicitly justified rather than silently accepted.

### Context & compaction (`openclaw.json`)
- [ ] `agents.defaults.contextPruning.mode` is set (e.g., `"cache-ttl"`)
- [ ] `agents.defaults.compaction.mode` is set (e.g., `"safeguard"`)
- [ ] `agents.defaults.compaction.memoryFlush.enabled` is `true`

### Typing & UX (`openclaw.json`)
- [ ] `agents.defaults.typingMode` is set (e.g., `"instant"`)

### Messages (`openclaw.json`)
- [ ] `messages.ackReaction` is set (e.g., `"eyes"`)
- [ ] `messages.ackReactionScope` is set (e.g., `"group-mentions"`)
- [ ] `messages.removeAckAfterReply` is `true`

### Commands (`openclaw.json`)
- [ ] `commands.native` is set (e.g., `"auto"`)
- [ ] `commands.bash` is `true`
- [ ] `commands.restart` is `true`

### Hooks (`openclaw.json`)
- [ ] `hooks.internal.enabled` is `true`
- [ ] Hook entries enabled: `boot-md`, `session-memory`, `command-logger`

### Skills (`openclaw.json`)
- [ ] `skills.allowBundled` lists any bundled skills in use
- [ ] Each skill entry has its required env vars set (referencing `${VAR}` from `.env`)

### Browser profiles (`openclaw.json`)
- [ ] Each browser profile has a unique `cdpPort`
- [ ] Ports don't conflict with the gateway port

## 13. Final Verification

- [ ] `openclaw status` shows no errors — gateway is running, all configured channels are connected
- [ ] `openclaw cron list` shows expected jobs with correct schedules — no jobs in `error` state, no unexpected `consecutiveErrors`
- [ ] Cron jobs with `lastDeliveryStatus: "not-delivered"` are confirmed NO_REPLY (not delivery failures)
- [ ] All symlinks resolve (`USER.md`, `shared/`)
- [ ] `.env` has no placeholder values
- [ ] `openclaw.json` has no hardcoded secrets

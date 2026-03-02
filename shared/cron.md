# Cron Jobs

Conventions for creating and managing cron jobs. For the full CLI reference and field details, see the [official docs](https://docs.openclaw.ai/automation/cron-jobs.md).

## Naming

Snake case, agent-prefixed: `<agent>_<job_name>`. Prompt templates live at `workspace/cron/<job_name>.md` and match the job name.

## Required fields

Every cron job must have:
- `--model` — tier alias: `heavy`, `medium`, or `light`
- `--thinking` — `off`, `low`, `medium`, or `high`
- `--session isolated` — always. Never `main` (heartbeat is disabled).
- `--message` referencing a markdown file — no large inline prompts

## Delivery modes

### `announce` (default)

The agent's reply gets posted to a Slack channel. Use this for jobs that report status, summaries, or findings.

```bash
openclaw cron add \
  --name "hermy_daily_standup" \
  --agent hermy \
  --cron "0 8 * * 1-5" --tz "America/Los_Angeles" \
  --session isolated \
  --model medium --thinking off \
  --message "Read cron/daily_standup.md for instructions." \
  --announce --channel slack --to "channel:C1234567890"
```

When there's nothing to report, the agent replies `NO_REPLY` — OpenClaw silently suppresses it so nothing gets posted.

### `none`

The agent handles its own output. Use this when the cron needs to post a message to a channel AND follow up in the thread — `announce` can only post the reply as a top-level message, so it can't do threaded follow-ups.

Example use case: "Check for new support tickets. Post a one-liner summary to #support, then post a detailed breakdown in that message's thread."

```bash
openclaw cron add \
  --name "pearl_support_triage" \
  --agent pearl \
  --cron "*/15 * * * *" \
  --session isolated \
  --model medium --thinking low \
  --message "Read cron/support_triage.md for instructions."
```

Omit `--announce` entirely — delivery defaults to `none`. The prompt template must then instruct the agent to use the `message` tool to post to Slack directly.

## Model tiers

Use aliases, not model names. Swap providers in one place.

| Tier | When to use |
|------|-------------|
| `heavy` | Audits, complex reasoning, multi-step implementation |
| `medium` | Summaries, check-ins, consolidation |
| `light` | High-volume, low-stakes tasks |

## Gate scripts

Gates prevent unnecessary LLM calls on high-frequency crons. A gate is a shell script that exits 0 (run) or non-zero (skip). The cron runner calls the gate first — if it exits non-zero, the job is skipped without invoking the model.

> **Note:** Gate support requires the [custom fork](https://github.com/geekforbrains/openclaw). On stock OpenClaw, skip this — jobs work fine, they just can't be conditionally skipped.

Gate scripts live in `workspace/scripts/`. **Always use absolute paths** (`~/.openclaw/agents/<agent>/workspace/scripts/<script>.sh`) — relative paths don't resolve from the cron runner.

```bash
openclaw cron add \
  --name "cora_myproject" \
  --agent cora \
  --cron "*/15 * * * *" \
  --session isolated \
  --model heavy --thinking medium \
  --message "Read cron/project_dev.md. Repo: owner/myproject." \
  --gate "~/.openclaw/agents/cora/workspace/scripts/gh_has_issues.sh owner/myproject ready" \
  --announce --channel slack --to "channel:C1234567890"
```

## Why crons, not heartbeat

Heartbeat runs periodic turns inside the main session, paying full context cost (170k–210k tokens on a busy session) every tick. Isolated crons start fresh each run — token cost is fixed and predictable, and you control the model, schedule, and delivery per job.

Disable heartbeat: `agents.defaults.heartbeat.every: "0m"`. Use `--session isolated` on all crons.

---
name: cron-manager
description: Conventions for creating cron jobs. Reference this when setting up scheduled tasks.
metadata: { "openclaw": { "emoji": "⏰" } }
---

# Cron Manager

Conventions for creating and managing cron jobs. Use OpenClaw's built-in `cron` tool — not the CLI.

## Creating a Cron Job

Follow these rules when creating any cron job:

- **Name:** snake_case, prefixed with your agent id (`<agent>_<job_name>`)
- **Session:** always `isolated` — never use `main`
- **Model:** explicitly set (don't rely on defaults)
- **Thinking:** explicitly set (`off`, `low`, `medium`, or `high`)
- **Message:** `Read cron/<job_name>.md and follow its instructions.`
- **Prompt file:** create `cron/<job_name>.md` in your workspace with the full job instructions

## Delivery Modes

**Announce** (default) — the cron system delivers the agent's response as a single message to a Slack channel. Use for status updates, summaries, findings. When there's nothing to report, reply `NO_REPLY` — OpenClaw suppresses delivery silently.

**None** (no delivery) — the agent handles its own messaging via the `message` tool. Use when the job needs multi-step messaging, conditional posting, or multi-channel delivery. The prompt file must instruct the agent to use `message` directly.

## Prompt File Format

Each prompt file (`cron/<job_name>.md`) should include:

- What to do (the task)
- Where to post (explicit channel/user ID if using no-delivery mode)
- Constraints or rules
- What to do when there's nothing to report (typically "reply `NO_REPLY`")

## Channel Targeting

- Use explicit Slack channel IDs (`channel:C...`) or user IDs (`user:U...`)
- Never rely on "last" channel — it resolves nondeterministically
- Channel names change; IDs are stable

## Gates

A gate is a shell command that runs before the agent turn. Exit 0 = proceed, non-zero = skip. No tokens spent on skipped jobs. Requires the [patched fork](https://github.com/geekforbrains/openclaw).

Use a gate when there's a cheap pre-check:

```bash
# Only if open GitHub issues with label
--gate "gh issue list --repo owner/repo --label ready --state open --limit 1 | grep -q ."

# Only on weekdays
--gate "[ $(date +%u) -le 5 ]"
```

## Cost Controls

- Use `--light-context` for jobs that don't need workspace bootstrap files
- Use cheaper models for routine tasks
- Use `--thinking off` or `--thinking low` for simple jobs

For full conventions: https://raw.githubusercontent.com/geekforbrains/openclaw-playbook/main/standards/cron.md

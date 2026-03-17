---
name: cron-manager
description: Create, list, validate, and audit cron jobs following playbook conventions. Use when setting up new crons or checking existing ones for standards compliance.
metadata: { "openclaw": { "emoji": "⏰" } }
---

# Cron Manager

Create and audit cron jobs that follow playbook conventions.

## Scripts

All scripts live at `{baseDir}/scripts/`.

### Create a cron job

```bash
python3 {baseDir}/scripts/cron.py create \
  --name "<agent>_<job_name>" \
  --agent <agent> \
  --cron "0 8 * * 1-5" \
  --tz "America/Vancouver" \
  --model "anthropic/claude-sonnet-4-6" \
  --thinking off \
  --deliver announce \
  --channel slack \
  --to "channel:C1234567890"
```

This validates naming conventions, required fields, and delivery mode, then runs `openclaw cron add` with the right flags. It also creates the prompt template at `cron/<job_name>.md` in the agent's workspace if it doesn't exist.

### Validate all cron jobs

```bash
python3 {baseDir}/scripts/cron.py validate
```

Checks every cron job for:
- Snake case, agent-prefixed naming
- Isolated session (never main)
- Model and thinking explicitly set
- Message references a file (not inline prompts)
- Prompt file exists in the agent's workspace
- Announce-mode jobs have channel targeting

### List cron jobs

```bash
python3 {baseDir}/scripts/cron.py list
```

Lists all cron jobs with status, schedule, and last run info.

## Conventions

When creating crons, follow these rules:

- **Name:** snake_case, agent-prefixed (`<agent>_<job_name>`)
- **Session:** always `isolated`
- **Message:** `Read cron/<job_name>.md and follow its instructions.`
- **Model:** explicitly set (don't rely on defaults)
- **Thinking:** explicitly set (`off`, `low`, `medium`, or `high`)
- **Announce mode:** pair with `--channel` and `--to` (explicit channel ID)
- **None mode:** omit `--announce` — the prompt handles messaging
- **Gates:** use when there's a cheap pre-check (requires patched fork)

For full conventions, fetch: https://raw.githubusercontent.com/geekforbrains/openclaw-playbook/main/standards/cron.md

---
name: system-audit
description: Audit an OpenClaw install for standards compliance, workspace hygiene, cron health, and gateway status. Use for periodic health checks or after configuration changes.
metadata: { "openclaw": { "emoji": "🔍" } }
---

# System Audit

Audit an OpenClaw install against playbook standards. Fixes what it can, reports what needs judgment.

## Scripts

### Run full audit

```bash
python3 {baseDir}/scripts/audit.py run
```

Checks:
- **Workspace structure** — required directories and files for each agent
- **Cron health** — jobs in error state, naming violations, missing fields
- **Config basics** — heartbeat disabled, skipBootstrap set, secrets not hardcoded
- **Gateway status** — running and responsive
- **Prompt files** — every cron job has a corresponding prompt template

### Check a specific area

```bash
python3 {baseDir}/scripts/audit.py check workspace
python3 {baseDir}/scripts/audit.py check crons
python3 {baseDir}/scripts/audit.py check config
python3 {baseDir}/scripts/audit.py check gateway
```

## Output

JSON report with `fixed` (auto-resolved) and `needs_attention` (requires human judgment) sections.

## What gets auto-fixed

- Missing workspace directories (created)
- Cron jobs missing model/thinking (set to defaults)

## What gets reported only

- Jobs in error state (include error message)
- Gateway disconnected or unhealthy
- Naming convention violations
- Config deviations from standard

## Standards reference

For the full standard being audited against, fetch:
https://raw.githubusercontent.com/geekforbrains/openclaw-playbook/main/standards/guide.md

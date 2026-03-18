# System Audit

Run a daily health check on the OpenClaw install and DM the admin user with findings.

## What to check

1. **Workspace structure** — verify each agent in config has the expected workspace directories (memory, cron, skills, output, data, tmp)
2. **AGENTS.md roster** — compare the agent list in `openclaw.json` against each agent's "Other Agents" section in AGENTS.md. Flag any agent that exists in config but is missing from another agent's roster.
3. **Gateway config** — verify `bind: "loopback"` and `auth.mode: "token"` are set
4. **Tool policies** — check each agent's tool allowlist. Flag any non-admin agent with `exec` enabled or without `workspaceOnly: true`
5. **Cron health** — list all cron jobs, check for naming convention compliance (snake_case, agent-prefixed), isolated sessions, explicit model/thinking

## Delivery

DM the admin user with findings. Use `message` tool to send directly to `user:UXXXXXXXXX`.

## Format

Keep it concise. Group by status:

**Needs attention:**
- List issues found, one per line

**All clear:**
- If nothing needs attention, reply `NO_REPLY`

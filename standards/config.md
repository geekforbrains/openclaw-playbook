# Config Reference

Sensible defaults and key decisions for `openclaw.json`. For the full field reference, see the [official docs](https://docs.openclaw.ai/gateway/configuration-reference).

## Principles

- **All secrets in `.env`** — `openclaw.json` uses `${VAR}` references. Never hardcode keys.
- **Deny by default** — agents get no tools unless explicitly allowlisted. Open up per-agent based on role.
- **Crons over heartbeat** — heartbeat runs in the main session and pays full context cost every tick. Disable it; use isolated cron jobs instead.

## Gateway

Every install must have loopback binding and [token auth](https://docs.openclaw.ai/gateway/authentication). No exceptions, even for local-only setups.

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": { "mode": "token", "token": "${OPENCLAW_GATEWAY_TOKEN}" }
  }
}
```

Generate the token during setup: `openssl rand -hex 32`

## Agent Defaults

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-opus-4-6",
        "fallbacks": ["openai/gpt-5.4"]
      },
      "maxConcurrent": 1,
      "thinkingDefault": "adaptive",
      "compaction": { "mode": "safeguard" },
      "heartbeat": { "every": "0m" },
      "skipBootstrap": true
    }
  }
}
```

Key decisions:
- **`skipBootstrap: true`** — OpenClaw won't auto-create workspace files. You control exactly what exists. See [system prompt](https://docs.openclaw.ai/concepts/system-prompt).
- **`heartbeat.every: "0m"`** — disabled. Use isolated [cron jobs](https://docs.openclaw.ai/automation/cron-jobs) instead. See [cron vs heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat).
- **`compaction.mode: "safeguard"`** — compacts context when approaching limits. See [compaction](https://docs.openclaw.ai/concepts/compaction).

## Tool Policy

Every agent starts fully locked down. Open capabilities per-agent based on what the role requires. See [tool policy vs sandbox vs elevated](https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated).

The deny-all baseline goes in the **top-level `tools`** block (not in `agents.defaults` — that key doesn't support `tools`):

```json
{
  "tools": {
    "profile": "messaging",
    "allow": [],
    "deny": ["*"],
    "fs": { "workspaceOnly": true },
    "exec": { "security": "deny" },
    "elevated": { "enabled": false }
  }
}
```

`exec.security` valid values: `"deny"`, `"allowlist"`, `"full"`.

Override per-agent in `agents.list[].tools`:

```json
{
  "id": "researcher",
  "tools": {
    "allow": ["web_search", "web_fetch", "read", "write", "message", "cron"],
    "deny": ["exec", "group:automation", "group:runtime", "sessions_spawn", "gateway"]
  }
}
```

Use allowlists so new tools/features are denied by default. The `deny` list is explicit about high-risk tools to prevent accidental enablement.

### Guidelines

- **Favor [plugin tools](https://docs.openclaw.ai/tools/plugin) over [exec](https://docs.openclaw.ai/tools/exec)** — if an agent has a specific job, write a plugin tool for it. Schema-validated inputs, no shell injection risk, deterministic behavior.
- **Don't document tools in prompt files** — tool names and descriptions are injected at runtime. Duplicating them in AGENTS.md adds noise and goes stale.
- **`cron` tool** — add to any agent that users may ask to schedule work. The shared cron-manager skill provides conventions. See [cron jobs](https://docs.openclaw.ai/automation/cron-jobs).
- **`gateway` and [`sessions_spawn`](https://docs.openclaw.ai/tools/subagents)** — control plane tools. Almost never needed outside the admin agent.

## Channels (Slack)

```json
{
  "channels": {
    "slack": {
      "mode": "socket",
      "enabled": true,
      "groupPolicy": "open",
      "dmPolicy": "allowlist",
      "allowFrom": ["<your-slack-user-id>"],
      "nativeStreaming": true,
      "streaming": "partial",
      "replyToMode": "first",
      "requireMention": true,
      "requireMentionInThreads": true,
      "accounts": {}
    }
  }
}
```

Key decisions:
- **`groupPolicy: "open"`** — agents can respond in any channel they're added to. No friction for users.
- **`dmPolicy: "allowlist"`** — DMs restricted to listed user IDs.
- **`requireMention: true`** + **`requireMentionInThreads: true`** — agents only respond when @mentioned.
- **One [Slack app](https://docs.openclaw.ai/channels/slack) per agent** — each gets its own identity via separate bot/app tokens.

## Bindings

Route each agent's Slack account to it. See [channel routing](https://docs.openclaw.ai/channels/channel-routing).

```json
{
  "bindings": [
    { "agentId": "<agent-name>", "match": { "channel": "slack", "accountId": "<agent-name>" } }
  ]
}
```

## Skills

Precedence (highest first):

1. `<workspace>/skills/` — agent-specific (default location for new skills)
2. `~/.openclaw/skills/` — shared (promote here only when multiple agents need it)
3. Bundled skills (only those in `skills.allowBundled` are loaded)

Skills are agent-specific by default. Only promote to shared when multiple agents need the same capability.

## Auth Profiles

Each agent has an `auth-profiles.json` in its `agent/` directory. Don't pre-populate — credentials are auto-synced at runtime.

## Environment Variables

`~/.openclaw/.env` is gitignored. All secrets live here:

```bash
# AI providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Gateway
OPENCLAW_GATEWAY_TOKEN=<generate with: openssl rand -hex 32>

# Slack (one pair per agent — name matches agent id)
SLACK_BOT_TOKEN_<AGENT_NAME>=xoxb-...
SLACK_APP_TOKEN_<AGENT_NAME>=xapp-...
```

# Config Reference

Sensible defaults and key decisions for `openclaw.json`. For the full field reference, see the [official docs](https://docs.openclaw.ai/gateway/configuration-reference).

## Principles

- **All secrets in `.env`** — `openclaw.json` uses `${VAR}` references. Never hardcode keys.
- **Open by default** — channels and DMs are open. Tighten per-channel with `requireMention`, not globally.
- **Crons over heartbeat** — heartbeat runs in the main session and pays full context cost every tick. Disable it; use isolated cron jobs instead.

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
- **`skipBootstrap: true`** — OpenClaw won't auto-create workspace files. You control exactly what exists.
- **`heartbeat.every: "0m"`** — disabled. Use isolated cron jobs instead.
- **`compaction.mode: "safeguard"`** — compacts context when approaching limits.

## Gateway

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
      "accounts": {
        "<agent-name>": {
          "botToken": "${SLACK_BOT_TOKEN_<AGENT_NAME>}",
          "appToken": "${SLACK_APP_TOKEN_<AGENT_NAME>}"
        }
      },
      "defaultAccount": "<agent-name>"
    }
  }
}
```

Key decisions:
- **`groupPolicy: "open"`** — agents can respond in any channel. Use per-channel `requireMention` for noisy channels.
- **`dmPolicy: "allowlist"`** — DMs restricted to listed user IDs.
- **`requireMention: true`** + **`requireMentionInThreads: true`** — agents only respond when @mentioned. Prevents noise in busy channels and threads.
- **`replyToMode: "first"`** — channel replies go in a thread under the original message. Required for `nativeStreaming`.
- **One account per agent** — each agent has its own Slack app. Non-default agents need a binding.

## Bindings

Route each agent's Slack account to it:

```json
{
  "bindings": [
    { "agentId": "<agent-name>", "match": { "channel": "slack", "accountId": "<agent-name>" } }
  ]
}
```

## Tools

```json
{
  "tools": {
    "profile": "full"
  }
}
```

Agents get all tools by default. Narrow per-agent via `agents.list[].tools.profile` only if needed.

## Auth Profiles

Each agent has an `auth-profiles.json` in its `agent/` directory. Don't pre-populate — credentials are auto-synced at runtime:

- **Anthropic:** resolved from `auth.profiles` in `openclaw.json` (uses `ANTHROPIC_API_KEY` from `.env`)
- **OpenAI:** OAuth tokens synced automatically
- **Multi-agent fallback:** agents fall back to the primary agent's credentials if their own are missing

## Environment Variables

`~/.openclaw/.env` is gitignored. All secrets live here:

```bash
# AI providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=

# Gateway
OPENCLAW_GATEWAY_TOKEN=<generate with: openssl rand -hex 32>

# Slack (one pair per agent — name matches agent id)
SLACK_BOT_TOKEN_<AGENT_NAME>=xoxb-...
SLACK_APP_TOKEN_<AGENT_NAME>=xapp-...
```

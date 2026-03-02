# Config Reference

Sensible defaults and key decisions for `openclaw.json`. For the full field reference, see the [official docs](https://docs.openclaw.ai/gateway/configuration-reference.md).

## Principles

- **All secrets in `.env`** — `openclaw.json` uses `${VAR}` references. Never hardcode keys.
- **Open by default** — channels and DMs are open to all. Tighten after, not before. This avoids silent failures when adding new channels or agents.
- **Crons over heartbeat** — heartbeat runs in the main session and pays full context cost every tick. Disable it and use isolated cron jobs instead.

## Agent Defaults

```json
{
  "agents": {
    "defaults": {
      "model": { "primary": "heavy" },
      "models": {
        "anthropic/claude-opus-4-6": { "alias": "heavy" },
        "anthropic/claude-sonnet-4-6": { "alias": "medium" },
        "anthropic/claude-haiku-4-5": { "alias": "light" }
      },
      "memorySearch": {
        "enabled": true,
        "extraPaths": ["~/.openclaw/shared"]
      },
      "contextPruning": { "mode": "cache-ttl", "ttl": "1h" },
      "compaction": { "mode": "safeguard", "memoryFlush": { "enabled": true } },
      "heartbeat": { "every": "0m" },
      "maxConcurrent": 4,
      "subagents": { "maxConcurrent": 8 }
    }
  }
}
```

Model aliases (`heavy`/`medium`/`light`) let cron jobs and prompts reference tiers. Swap providers in one place.

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
      "dmPolicy": "open",
      "allowFrom": ["*"],
      "streaming": "partial",
      "nativeStreaming": true,
      "replyToModeByChatType": {
        "direct": "all",
        "group": "first",
        "channel": "first"
      },
      "thread": {
        "historyScope": "thread",
        "inheritParent": false,
        "initialHistoryLimit": 25
      },
      "channels": {
        "#general": { "requireMention": true }
      },
      "accounts": {
        "default": {
          "mode": "socket",
          "botToken": "${SLACK_BOT_TOKEN_DEFAULT}",
          "appToken": "${SLACK_APP_TOKEN_DEFAULT}"
        }
      }
    }
  }
}
```

Key decisions:
- **`groupPolicy: "open"`** — agents can respond in any channel. Use per-channel `requireMention: true` for noisy channels instead of restricting globally.
- **`dmPolicy: "open"`, `allowFrom: ["*"]`** — anyone can DM any agent.
- **`replyToModeByChatType.channel: "first"`** — channel replies go in a thread under the original message. Keeps channels easy to follow and gives each thread an isolated session (`historyScope: "thread"`). Also required for `nativeStreaming: true` to work, since Slack's streaming API needs a thread context. Do not set to `"off"` — that posts replies as top-level channel messages with no threading.
- **`thread.historyScope: "thread"`** — each thread is its own session. The thread does not see the parent channel's conversation history. Critical for Slack.
- **One account per agent** — each agent has its own Slack app. Non-default agents need a binding to route their account.

## Bindings

Route non-default agent accounts:

```json
{
  "bindings": [
    { "agentId": "agent_id", "match": { "channel": "slack", "accountId": "agent_id" } }
  ]
}
```

## Sessions

```json
{
  "session": {
    "dmScope": "per-channel-peer",
    "threadBindings": { "enabled": true, "idleHours": 24 },
    "maintenance": { "mode": "enforce", "pruneAfter": "30d" }
  }
}
```

## Tools

```json
{
  "tools": {
    "agentToAgent": { "enabled": true },
    "loopDetection": { "enabled": true, "globalCircuitBreakerThreshold": 30 }
  }
}
```

Enable agent-to-agent delegation and loop detection. Loop detection defaults are conservative — tune thresholds if you get false positives.

## Environment Variables

`~/.openclaw/.env` is gitignored. All secrets live here:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENCLAW_GATEWAY_TOKEN=<generate with: openssl rand -hex 32>

# One pair per Slack agent
SLACK_BOT_TOKEN_DEFAULT=xoxb-...
SLACK_APP_TOKEN_DEFAULT=xapp-...
SLACK_BOT_TOKEN_AGENT2=xoxb-...
SLACK_APP_TOKEN_AGENT2=xapp-...

# Optional
OPENAI_API_KEY=sk-...
```

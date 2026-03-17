---
name: slack-directory
description: Look up Slack users and channels by name or ID. Use when you need to resolve a person or channel before sending messages, reacting, or referencing someone.
metadata: { "openclaw": { "emoji": "📇", "requires": { "env": ["SLACK_BOT_TOKEN"] } } }
---

# Slack Directory

Resolve Slack users and channels by name or ID. Always use this before guessing IDs.

## Scripts

All scripts live at `{baseDir}/scripts/`. They output JSON for consistent parsing.

### Find a user by name

```bash
python3 {baseDir}/scripts/user.py find "bob"
```

Fuzzy matches against display name and real name. Returns all matches.

### Get a user by ID

```bash
python3 {baseDir}/scripts/user.py get U12345678
```

### List all users

```bash
python3 {baseDir}/scripts/user.py list
```

### Find a channel by name

```bash
python3 {baseDir}/scripts/channel.py find "general"
```

Matches against channel name. Returns all matches.

### Get a channel by ID

```bash
python3 {baseDir}/scripts/channel.py get C12345678
```

### List all channels

```bash
python3 {baseDir}/scripts/channel.py list
```

## Environment

Requires `SLACK_BOT_TOKEN` environment variable. Configure in `openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "slack-directory": {
        "enabled": true,
        "env": {
          "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN_<YOUR_DEFAULT_AGENT>}"
        }
      }
    }
  }
}
```

## When to use

- Someone says "message Bob" — find Bob's user ID first
- You need to post to a channel by name — find the channel ID first
- You want to mention someone — look up their ID for `<@U...>` format
- Don't guess Slack IDs. Always look them up.

## Caching

Results are cached in `/tmp/openclaw-slack-cache/` for 1 hour. First call per cache cycle hits the Slack API (may be slow for large workspaces). Subsequent calls are instant.

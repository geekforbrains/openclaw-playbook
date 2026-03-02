#!/usr/bin/env bash
# Lists all non-archived public Slack channels (name + ID) as JSON.
# Used by the system audit cron to sync the channel registry.
#
# Usage: list_slack_channels.sh
# Output: JSON array of {name, id} objects, sorted by name.
#
# Reads the default bot token from .env. Update TOKEN_VAR below
# if your default agent uses a different variable name.

set -euo pipefail

ENV_FILE="$HOME/.openclaw/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found" >&2
  exit 1
fi

# Change this to match your default agent's bot token variable
TOKEN_VAR="SLACK_BOT_TOKEN_DEFAULT"
TOKEN=$(grep "^${TOKEN_VAR}=" "$ENV_FILE" | cut -d= -f2-)

if [ -z "$TOKEN" ]; then
  echo "Error: ${TOKEN_VAR} not set in $ENV_FILE" >&2
  exit 1
fi

RESPONSE=$(curl -s "https://slack.com/api/conversations.list?types=public_channel&exclude_archived=true&limit=200" \
  -H "Authorization: Bearer $TOKEN")

OK=$(echo "$RESPONSE" | jq -r '.ok')

if [ "$OK" != "true" ]; then
  ERROR=$(echo "$RESPONSE" | jq -r '.error // "unknown"')
  echo "Error: Slack API returned: $ERROR" >&2
  exit 1
fi

echo "$RESPONSE" | jq '[.channels[] | {name: .name, id: .id}] | sort_by(.name)'

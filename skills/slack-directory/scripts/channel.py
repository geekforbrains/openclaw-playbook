#!/usr/bin/env python3
"""Slack channel directory — find, get, or list channels via the Slack API.

Usage:
    channel.py find <query>      Match by channel name
    channel.py get <channel_id>  Exact lookup by channel ID
    channel.py list              List all non-archived public channels

Requires SLACK_BOT_TOKEN environment variable.
Results are cached in /tmp/openclaw-slack-cache/ for 1 hour.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

CACHE_DIR = "/tmp/openclaw-slack-cache"
CACHE_TTL = 3600  # 1 hour
CACHE_FILE = os.path.join(CACHE_DIR, "channels.json")


def get_token():
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print(json.dumps({"error": "SLACK_BOT_TOKEN not set"}))
        sys.exit(1)
    return token


def slack_api(method, token, params=None):
    url = f"https://slack.com/api/{method}"
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if not data.get("ok"):
        print(json.dumps({"error": f"Slack API error: {data.get('error', 'unknown')}"}))
        sys.exit(1)
    return data


def fetch_all_channels(token):
    """Paginate through conversations.list and return all public channels."""
    all_channels = []
    cursor = None
    while True:
        params = {
            "types": "public_channel",
            "exclude_archived": "true",
            "limit": 200,
        }
        if cursor:
            params["cursor"] = cursor
        data = slack_api("conversations.list", token, params)
        all_channels.extend(data.get("channels", []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return all_channels


def load_cache():
    """Load cached channels if fresh enough."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        age = time.time() - os.path.getmtime(CACHE_FILE)
        if age > CACHE_TTL:
            return None
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_cache(channels):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(channels, f)


def get_channels(token):
    """Get all channels, using cache if available."""
    cached = load_cache()
    if cached is not None:
        return cached
    channels = fetch_all_channels(token)
    save_cache(channels)
    return channels


def format_channel(channel):
    """Extract the useful fields from a channel object."""
    return {
        "id": channel.get("id"),
        "name": channel.get("name"),
        "topic": channel.get("topic", {}).get("value", ""),
        "purpose": channel.get("purpose", {}).get("value", ""),
        "num_members": channel.get("num_members", 0),
        "is_private": channel.get("is_private", False),
    }


def cmd_find(query):
    token = get_token()
    channels = get_channels(token)
    query_lower = query.lower().lstrip("#")
    matches = []
    for channel in channels:
        name = channel.get("name", "").lower()
        topic = channel.get("topic", {}).get("value", "").lower()
        purpose = channel.get("purpose", {}).get("value", "").lower()
        if query_lower in name or query_lower in topic or query_lower in purpose:
            matches.append(format_channel(channel))
    print(json.dumps(matches, indent=2))


def cmd_get(channel_id):
    token = get_token()
    data = slack_api("conversations.info", token, {
        "channel": channel_id,
        "include_num_members": "true",
    })
    print(json.dumps(format_channel(data["channel"]), indent=2))


def cmd_list():
    token = get_token()
    channels = get_channels(token)
    result = [format_channel(c) for c in channels]
    result.sort(key=lambda c: c.get("name", "").lower())
    print(json.dumps(result, indent=2))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: channel.py <find|get|list> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "find":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: channel.py find <query>"}))
            sys.exit(1)
        cmd_find(sys.argv[2])
    elif cmd == "get":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: channel.py get <channel_id>"}))
            sys.exit(1)
        cmd_get(sys.argv[2])
    elif cmd == "list":
        cmd_list()
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}. Use find, get, or list."}))
        sys.exit(1)


if __name__ == "__main__":
    import urllib.parse
    main()

#!/usr/bin/env python3
"""Slack user directory — find, get, or list users via the Slack API.

Usage:
    user.py find <query>    Fuzzy match by display name or real name
    user.py get <user_id>   Exact lookup by Slack user ID
    user.py list            List all non-bot, non-deleted users

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
CACHE_FILE = os.path.join(CACHE_DIR, "users.json")


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


def fetch_all_users(token):
    """Paginate through users.list and return all members."""
    all_users = []
    cursor = None
    while True:
        params = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = slack_api("users.list", token, params)
        all_users.extend(data.get("members", []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return all_users


def load_cache():
    """Load cached users if fresh enough."""
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


def save_cache(users):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(users, f)


def get_users(token):
    """Get all users, using cache if available."""
    cached = load_cache()
    if cached is not None:
        return cached
    users = fetch_all_users(token)
    save_cache(users)
    return users


def format_user(user):
    """Extract the useful fields from a user object."""
    profile = user.get("profile", {})
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "real_name": user.get("real_name", ""),
        "display_name": profile.get("display_name", ""),
        "is_bot": user.get("is_bot", False),
        "deleted": user.get("deleted", False),
        "is_admin": user.get("is_admin", False),
        "title": profile.get("title", ""),
        "tz": user.get("tz", ""),
    }


def cmd_find(query):
    token = get_token()
    users = get_users(token)
    query_lower = query.lower()
    matches = []
    for user in users:
        if user.get("deleted") or user.get("is_bot") or user.get("id") == "USLACKBOT":
            continue
        profile = user.get("profile", {})
        display = profile.get("display_name", "").lower()
        real = user.get("real_name", "").lower()
        name = user.get("name", "").lower()
        if query_lower in display or query_lower in real or query_lower in name:
            matches.append(format_user(user))
    print(json.dumps(matches, indent=2))


def cmd_get(user_id):
    token = get_token()
    data = slack_api("users.info", token, {"user": user_id})
    print(json.dumps(format_user(data["user"]), indent=2))


def cmd_list():
    token = get_token()
    users = get_users(token)
    result = []
    for user in users:
        if user.get("deleted") or user.get("is_bot") or user.get("id") == "USLACKBOT":
            continue
        result.append(format_user(user))
    result.sort(key=lambda u: u.get("real_name", "").lower())
    print(json.dumps(result, indent=2))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: user.py <find|get|list> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "find":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: user.py find <query>"}))
            sys.exit(1)
        cmd_find(sys.argv[2])
    elif cmd == "get":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: user.py get <user_id>"}))
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

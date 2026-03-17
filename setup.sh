#!/usr/bin/env bash
# OpenClaw Playbook — automated install bootstrap
# Supports macOS and Linux.
#
# What this does:
#   1. Clones and builds the patched OpenClaw fork
#   2. Bootstraps ~/.openclaw/ via openclaw onboard
#   3. Installs baseline config, templates, and skills
#   4. Starts the gateway and runs a health check
#
# Usage:
#   ./setup.sh                          # Interactive — prompts for agent details
#   ./setup.sh --agent-id hermy \
#              --agent-name "Hermy" \
#              --agent-emoji "🦀"       # Non-interactive

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_REPO="https://github.com/geekforbrains/openclaw.git"
OPENCLAW_DIR="$HOME/.openclaw"
PROJECTS_DIR="$HOME/Projects"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[info]${NC} $1"; }
ok()    { echo -e "${GREEN}[ok]${NC} $1"; }
warn()  { echo -e "${YELLOW}[warn]${NC} $1"; }
error() { echo -e "${RED}[error]${NC} $1"; exit 1; }

# --- Parse args ---

AGENT_ID=""
AGENT_NAME=""
AGENT_EMOJI="🤖"

while [[ $# -gt 0 ]]; do
  case $1 in
    --agent-id)    AGENT_ID="$2"; shift 2 ;;
    --agent-name)  AGENT_NAME="$2"; shift 2 ;;
    --agent-emoji) AGENT_EMOJI="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: setup.sh [--agent-id ID] [--agent-name NAME] [--agent-emoji EMOJI]"
      exit 0
      ;;
    *) error "Unknown option: $1" ;;
  esac
done

# --- Interactive prompts if not provided ---

if [[ -z "$AGENT_ID" ]]; then
  echo ""
  echo -e "${BLUE}OpenClaw Playbook Setup${NC}"
  echo ""
  read -rp "Agent ID (lowercase, e.g. hermy): " AGENT_ID
  [[ -z "$AGENT_ID" ]] && error "Agent ID is required"
fi

if [[ -z "$AGENT_NAME" ]]; then
  read -rp "Agent display name (e.g. Hermy): " AGENT_NAME
  [[ -z "$AGENT_NAME" ]] && AGENT_NAME="$AGENT_ID"
fi

read -rp "Agent emoji (default: 🤖): " input_emoji
[[ -n "$input_emoji" ]] && AGENT_EMOJI="$input_emoji"

echo ""

# --- Prerequisites ---

info "Checking prerequisites..."

# Node 22+
if ! command -v node &>/dev/null; then
  error "Node.js not found. Install Node 22+ first: https://nodejs.org"
fi
NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [[ "$NODE_VERSION" -lt 22 ]]; then
  error "Node 22+ required (found v$(node -v))"
fi
ok "Node $(node -v)"

# pnpm
if ! command -v pnpm &>/dev/null; then
  warn "pnpm not found — installing via corepack"
  corepack enable
  corepack prepare pnpm@latest --activate
fi
ok "pnpm $(pnpm -v)"

# git
command -v git &>/dev/null || error "git not found"
ok "git $(git --version | awk '{print $3}')"

# gh (optional)
if command -v gh &>/dev/null; then
  ok "gh CLI $(gh --version | head -1 | awk '{print $3}')"
else
  warn "gh CLI not found — some cron gates won't work. Install: https://cli.github.com"
fi

echo ""

# --- Step 1: Clone and build OpenClaw ---

OPENCLAW_SRC="$PROJECTS_DIR/openclaw"

if [[ -d "$OPENCLAW_SRC" ]]; then
  info "OpenClaw repo already exists at $OPENCLAW_SRC"
  cd "$OPENCLAW_SRC"
  CURRENT_BRANCH=$(git branch --show-current)
  if [[ "$CURRENT_BRANCH" != "custom" ]]; then
    warn "Not on 'custom' branch (on '$CURRENT_BRANCH'). Switching..."
    git checkout custom
  fi
  info "Pulling latest..."
  git pull --rebase origin custom
else
  info "Cloning OpenClaw fork..."
  mkdir -p "$PROJECTS_DIR"
  git clone "$OPENCLAW_REPO" "$OPENCLAW_SRC"
  cd "$OPENCLAW_SRC"
  git checkout custom
fi

info "Building OpenClaw (make install)..."
make install
ok "OpenClaw installed: $(openclaw --version 2>/dev/null || echo 'version check failed')"
echo ""

# --- Step 2: Bootstrap ~/.openclaw/ ---

if [[ -d "$OPENCLAW_DIR" ]]; then
  info "~/.openclaw/ already exists — skipping onboard"
else
  info "Running openclaw onboard..."
  openclaw onboard --non-interactive --accept-risk --mode local --skip-health
  ok "Onboard complete"
fi

# Remove default workspace if it exists (we don't use it)
[[ -d "$OPENCLAW_DIR/workspace" ]] && rm -rf "$OPENCLAW_DIR/workspace"

echo ""

# --- Step 3: Create agent workspace ---

AGENT_BASE="$OPENCLAW_DIR/agents/$AGENT_ID"
AGENT_WORKSPACE="$AGENT_BASE/workspace"
AGENT_AGENT_DIR="$AGENT_BASE/agent"

if [[ -d "$AGENT_WORKSPACE" ]]; then
  info "Agent workspace already exists at $AGENT_WORKSPACE"
else
  info "Creating agent workspace..."
  mkdir -p "$AGENT_WORKSPACE"/{memory,cron,skills,output,data,tmp}
  mkdir -p "$AGENT_AGENT_DIR"
  ok "Created $AGENT_WORKSPACE"
fi

# --- Step 4: Install templates ---

info "Installing templates..."

# SHARED.md
if [[ ! -f "$OPENCLAW_DIR/SHARED.md" ]]; then
  cp "$SCRIPT_DIR/templates/SHARED.md" "$OPENCLAW_DIR/SHARED.md"
  ok "Installed SHARED.md"
else
  info "SHARED.md already exists — skipping"
fi

# AGENTS.md (per-agent)
if [[ ! -f "$AGENT_WORKSPACE/AGENTS.md" ]]; then
  sed "s/<Name>/$AGENT_NAME/g; s/<Emoji>/$AGENT_EMOJI/g" \
    "$SCRIPT_DIR/templates/AGENTS.md" > "$AGENT_WORKSPACE/AGENTS.md"
  ok "Installed AGENTS.md for $AGENT_NAME"
else
  info "AGENTS.md already exists — skipping"
fi

# MEMORY.md (per-agent)
if [[ ! -f "$AGENT_WORKSPACE/MEMORY.md" ]]; then
  sed "s/<company>/your company/g" \
    "$SCRIPT_DIR/templates/MEMORY.md" > "$AGENT_WORKSPACE/MEMORY.md"
  ok "Installed MEMORY.md"
else
  info "MEMORY.md already exists — skipping"
fi

# .env
if [[ ! -f "$OPENCLAW_DIR/.env" ]]; then
  AGENT_UPPER=$(echo "$AGENT_ID" | tr '[:lower:]' '[:upper:]')
  sed "s/AGENT1/$AGENT_UPPER/g" \
    "$SCRIPT_DIR/templates/.env.example" > "$OPENCLAW_DIR/.env"
  ok "Installed .env (fill in your keys!)"
else
  info ".env already exists — skipping"
fi

echo ""

# --- Step 5: Merge config ---

info "Installing config..."

# Read the existing config (from onboard) and merge our template on top
if [[ -f "$CONFIG_FILE" ]] 2>/dev/null; then
  CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
else
  CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
fi

AGENT_UPPER=$(echo "$AGENT_ID" | tr '[:lower:]' '[:upper:]')

# Generate the config from template with substitutions
python3 -c "
import json, sys, os

template_path = '$SCRIPT_DIR/templates/openclaw.json'
config_path = '$OPENCLAW_DIR/openclaw.json'
agent_id = '$AGENT_ID'
agent_name = '$AGENT_NAME'
agent_emoji = '$AGENT_EMOJI'
agent_upper = '$AGENT_UPPER'
home = os.path.expanduser('~')

# Load template
with open(template_path) as f:
    template = json.load(f)

# Apply substitutions to agent list
for agent in template.get('agents', {}).get('list', []):
    if agent.get('id') == 'AGENT_ID':
        agent['id'] = agent_id
        agent['workspace'] = f'{home}/.openclaw/agents/{agent_id}/workspace'
        agent['agentDir'] = f'{home}/.openclaw/agents/{agent_id}/agent'
        agent['identity'] = {'name': agent_name, 'emoji': agent_emoji}

# Fix Slack accounts
slack = template.get('channels', {}).get('slack', {})
accounts = slack.get('accounts', {})
if 'AGENT_ID' in accounts:
    accounts[agent_id] = {
        'botToken': f'\${SLACK_BOT_TOKEN_{agent_upper}}',
        'appToken': f'\${SLACK_APP_TOKEN_{agent_upper}}'
    }
    del accounts['AGENT_ID']
slack['defaultAccount'] = agent_id

# Fix bindings
for binding in template.get('bindings', []):
    if binding.get('agentId') == 'AGENT_ID':
        binding['agentId'] = agent_id
        binding['match']['accountId'] = agent_id

# Load existing config if it exists and merge gateway/auth from it
if os.path.exists(config_path):
    with open(config_path) as f:
        existing = json.load(f)
    # Preserve onboard-generated sections
    for key in ['gateway', 'auth', 'wizard', 'session']:
        if key in existing:
            template[key] = existing[key]

# Write final config
with open(config_path, 'w') as f:
    json.dump(template, f, indent=2)
    f.write('\n')

print('ok')
" && ok "Config installed" || warn "Config merge failed — check $OPENCLAW_DIR/openclaw.json manually"

echo ""

# --- Step 6: Install skills ---

info "Installing skills..."

SKILLS_DIR="$OPENCLAW_DIR/skills"
mkdir -p "$SKILLS_DIR"

for skill_dir in "$SCRIPT_DIR"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  target="$SKILLS_DIR/$skill_name"
  if [[ -d "$target" ]]; then
    info "Skill '$skill_name' already exists — updating"
    rm -rf "$target"
  fi
  cp -r "$skill_dir" "$target"
  # Make scripts executable
  find "$target/scripts" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
  find "$target/scripts" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
  ok "Installed skill: $skill_name"
done

echo ""

# --- Step 7: Health check ---

info "Running health checks..."

if command -v openclaw &>/dev/null; then
  ok "openclaw CLI available"

  # Try doctor
  if openclaw doctor 2>/dev/null; then
    ok "openclaw doctor passed"
  else
    warn "openclaw doctor reported issues (may be expected before filling in .env)"
  fi
else
  warn "openclaw not in PATH — you may need to restart your shell"
fi

echo ""

# --- Done ---

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Fill in your API keys and Slack tokens:"
echo "     $OPENCLAW_DIR/.env"
echo ""
echo "  2. Set your Slack user ID in the config (allowFrom):"
echo "     $OPENCLAW_DIR/openclaw.json"
echo ""
echo "  3. Customize your agent's personality:"
echo "     $AGENT_WORKSPACE/AGENTS.md"
echo ""
echo "  4. Update SHARED.md with your team info:"
echo "     $OPENCLAW_DIR/SHARED.md"
echo ""
echo "  5. Start the gateway:"
echo "     openclaw gateway run"
echo ""
echo "  6. Verify everything:"
echo "     openclaw channels status --probe"
echo ""

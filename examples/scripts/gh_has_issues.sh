#!/usr/bin/env bash
# Gate script: exits 0 if the repo has open issues with the given label, 1 otherwise.
# Usage: gh_has_issues.sh <owner/repo> <label>

set -euo pipefail

REPO="${1:?Usage: gh_has_issues.sh <owner/repo> <label>}"
LABEL="${2:?Usage: gh_has_issues.sh <owner/repo> <label>}"

COUNT=$(gh issue list --repo "$REPO" --label "$LABEL" --state open --json number --jq 'length')

if [ "$COUNT" -gt 0 ]; then
  echo "$COUNT open issue(s) with label '$LABEL' in $REPO" >&2
  exit 0
else
  echo "No open issues with label '$LABEL' in $REPO" >&2
  exit 1
fi

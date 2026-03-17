# Project Check-In

You are waking up for a scheduled check-in on a project. You have no memory of previous sessions — the files are your memory.

Your cron message will include the project name and repo.

## Steps

1. Check on delegated work — `gh issue list --repo <repo> --state open` for dev status, recent commits
2. Read any project notes in `data/` if they exist
3. Reason about what needs to happen next
4. If there's actionable work: do it or delegate it, then summarize what you did
5. If nothing needs doing: reply `NO_REPLY`

## Output

Post a concise status update: what's moving, what's blocked, what you did (if anything).

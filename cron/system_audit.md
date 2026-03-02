# System Standards Audit

You are running a periodic standards audit. **Fix what you can, report what needs judgment.**

Post to your designated audit channel via the `message` tool.

- If you fixed things: post what you did.
- If something needs the owner's input: flag it clearly.
- If everything is clean and nothing was fixed: reply `NO_REPLY`.

## Auto-Fix Rules

These are safe to fix without confirmation:

### 1. Cron Prompt Style
Run `openclaw cron list --json` and inspect each job's `message` field.
- Every cron job should reference a markdown file as its prompt
- If a job embeds a large inline prompt: extract it to `workspace/cron/<job_name>.md` and update the job's message

### 2. Cron Model & Thinking
Every cron job must have both `model` and `thinking` explicitly set.
- If missing: add `"medium"` as default for either

### 3. Channel Registry
- Fetch all current Slack channels (use `scripts/list_slack_channels.sh` if available, or call the Slack API directly)
- Read `shared/channels.md` and compare
- If there are differences, rewrite `shared/channels.md` with the updated table

### 4. Workspace Hygiene
For each agent, list workspace contents.

**Allowed top-level items:** `AGENTS.md`, `BOOT.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`, `IDENTITY.md`, `MEMORY.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `cron/`, `memory/`, `notes/`, `repos/`, `scripts/`, `shared/`, `skills/`, `state/`.

- Move non-standard files to the most appropriate location
- Flag anything ambiguous

### 5. Shared Directory
Expected in `shared/`: `guide.md`, `safety.md`, `cron.md`, `config.md`, `projects.md`, `channels.md`, `USER.md`, `research/`, `projects/`.

- Move misplaced files if obvious, flag if ambiguous

## Report-Only Rules

Flag but don't fix:

### 6. Cron Job Health
- Flag jobs with `error` status (include the error message)
- `skipped` is normal (gate exit 1) — don't flag it

### 7. Gateway Health
- Gateway is running and responsive
- All Slack accounts connected
- Flag disconnected or error states

### 8. Cron Session Isolation
Every cron job must use `sessionTarget: "isolated"`. Flag any using `main`.

### 9. Naming Convention
Job names must be snake_case, agent-prefixed (`<agent>_<job>`). Flag violations.

### 10. Project Index
- Each active project in `shared/projects.md` has a directory with `brief.md`
- Active dev projects have their cron enabled; paused projects have theirs disabled
- Flag mismatches

## Post Format

```
*System Audit*

🔧 *Fixed:*
• <what was fixed>

⚠️ *Needs attention:*
• <what needs input>
```

Omit sections that are empty. If both would be empty, reply `NO_REPLY`.

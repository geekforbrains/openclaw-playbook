# Cron Conventions

How we create and manage cron jobs. For the full CLI reference, see the [official docs](https://docs.openclaw.ai/automation/cron-jobs).

## Naming

Snake case, agent-prefixed: `<agent>_<job_name>`. Prompt templates live at `workspace/cron/<job_name>.md`.

## Required Fields

Every cron job must have:
- `--model` — model name or alias
- `--thinking` — `off`, `low`, `medium`, or `high`
- `--session isolated` — always. Never `main` ([heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat) is disabled).
- `--message` referencing a markdown file — no large inline prompts

## Delivery Modes

### `announce` (default)

The cron system delivers the agent's final response as a single message to a Slack channel. Use for status, summaries, or findings.

```bash
openclaw cron add \
  --name "<agent>_daily_standup" \
  --agent <agent> \
  --cron "0 8 * * 1-5" --tz "America/Vancouver" \
  --session isolated \
  --model anthropic/claude-sonnet-4-6 --thinking off \
  --message "Read cron/daily_standup.md and follow its instructions." \
  --announce --channel slack --to "channel:C1234567890"
```

When there's nothing to report, the agent replies `NO_REPLY` — OpenClaw suppresses delivery silently.

### `none` (--no-deliver)

The agent handles its own messaging via the `message` tool. Use when:
- The job needs multi-step messaging (post + thread reply)
- The job conditionally decides whether to post
- The job posts to multiple channels

```bash
openclaw cron add \
  --name "<agent>_support_triage" \
  --agent <agent> \
  --cron "*/15 * * * *" \
  --session isolated \
  --model anthropic/claude-sonnet-4-6 --thinking low \
  --message "Read cron/support_triage.md and follow its instructions."
```

Omit `--announce` entirely — delivery defaults to `none`. The prompt template must instruct the agent to use the `message` tool directly.

## Prompt Files

Keep job prompts in `cron/<job-name>.md` in the agent's workspace. The job message should be:

```
Read cron/<job-name>.md and follow its instructions.
```

This keeps prompts readable, editable, and version-controllable without touching job config. Relative paths work — the agent's cwd is its workspace.

Each prompt file should include:
- What to do (the task)
- Where to post (explicit channel ID if using `--no-deliver`)
- Rules or constraints
- What to do when there's nothing to report (typically "reply `NO_REPLY`")

## Channel Targeting

- Always use explicit Slack channel IDs (`channel:C...`) or user IDs (`user:U...`).
- Never rely on `delivery.channel = "last"` — it resolves nondeterministically.
- Channel names can be renamed; IDs are stable.

## Gates

A gate is a shell command that runs before the agent turn. Exit 0 = proceed, non-zero = skip. No tokens spent on skipped jobs.

> Gate support requires the [patched fork](https://github.com/geekforbrains/openclaw) (`feat/cron-gate` branch).

Default to using a gate if there's any precondition checkable without an LLM:

```bash
# Only run if there are open GitHub issues with a label
--gate "gh issue list --repo owner/repo --label ready --state open --limit 1 | grep -q ."

# Only run on weekdays
--gate "[ $(date +%u) -le 5 ]"

# Only run if a file exists
--gate "test -f /tmp/should-run"
```

Omit the gate when the job must always involve the LLM (e.g. "summarize my inbox" has no cheap pre-check).

## Cost Controls

- Use `--light-context` for jobs that don't need workspace bootstrap files.
- Use `--model` to pick a cheaper model for routine chores.
- Use `--thinking low` or `--thinking off` for simple tasks.

## Why Crons, Not Heartbeat

[Heartbeat](https://docs.openclaw.ai/gateway/heartbeat) runs periodic turns inside the main session, paying full context cost (170k-210k tokens on a busy session) every tick. Isolated crons start fresh each run — token cost is fixed and predictable, and you control the model, schedule, and delivery per job. See [cron vs heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat).

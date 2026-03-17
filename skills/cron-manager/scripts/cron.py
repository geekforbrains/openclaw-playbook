#!/usr/bin/env python3
"""Cron manager — create, validate, and list cron jobs per playbook conventions.

Usage:
    cron.py create --name <name> --agent <agent> --cron <expr> [options]
    cron.py validate
    cron.py list
"""

import json
import os
import re
import subprocess
import sys


def run_cmd(args, check=True):
    """Run a command and return stdout."""
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(json.dumps({"error": f"Command failed: {' '.join(args)}", "stderr": result.stderr.strip()}))
        sys.exit(1)
    return result.stdout.strip()


def get_cron_jobs():
    """Get all cron jobs as JSON."""
    output = run_cmd(["openclaw", "cron", "list", "--json"])
    if not output:
        return []
    return json.loads(output)


def validate_name(name):
    """Check naming convention: snake_case, agent-prefixed."""
    issues = []
    if not re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$", name):
        issues.append(f"Name '{name}' is not snake_case or missing agent prefix (expected: <agent>_<job>)")
    return issues


def cmd_create(args):
    """Create a cron job with convention enforcement."""
    import argparse

    parser = argparse.ArgumentParser(prog="cron.py create")
    parser.add_argument("--name", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--cron", required=True)
    parser.add_argument("--tz", default="America/Vancouver")
    parser.add_argument("--model", required=True)
    parser.add_argument("--thinking", required=True, choices=["off", "low", "medium", "high"])
    parser.add_argument("--deliver", default="none", choices=["announce", "none"])
    parser.add_argument("--channel", default=None)
    parser.add_argument("--to", default=None)
    parser.add_argument("--gate", default=None)
    parser.add_argument("--light-context", action="store_true")
    parser.add_argument("--message", default=None, help="Custom message (default: auto-generated from name)")
    opts = parser.parse_args(args)

    # Validate naming
    issues = validate_name(opts.name)
    if not opts.name.startswith(f"{opts.agent}_"):
        issues.append(f"Name must be prefixed with agent id: {opts.agent}_<job>")

    if issues:
        print(json.dumps({"error": "Validation failed", "issues": issues}))
        sys.exit(1)

    # Derive job name from full name (strip agent prefix)
    job_name = opts.name[len(opts.agent) + 1:]

    # Build message
    if opts.message:
        message = opts.message
    else:
        message = f"Read cron/{job_name}.md and follow its instructions."

    # Validate announce mode has channel targeting
    if opts.deliver == "announce" and (not opts.channel or not opts.to):
        print(json.dumps({"error": "Announce mode requires --channel and --to"}))
        sys.exit(1)

    # Build openclaw cron add command
    cmd = [
        "openclaw", "cron", "add",
        "--name", opts.name,
        "--agent", opts.agent,
        "--cron", opts.cron,
        "--tz", opts.tz,
        "--session", "isolated",
        "--model", opts.model,
        "--thinking", opts.thinking,
        "--message", message,
    ]

    if opts.deliver == "announce":
        cmd.extend(["--announce", "--channel", opts.channel, "--to", opts.to])

    if opts.gate:
        cmd.extend(["--gate", opts.gate])

    if opts.light_context:
        cmd.append("--light-context")

    # Run it
    output = run_cmd(cmd)

    # Create prompt template if it doesn't exist
    # We need to find the agent's workspace to create the file
    prompt_path = f"cron/{job_name}.md"
    result = {
        "status": "created",
        "name": opts.name,
        "message": message,
        "prompt_template": prompt_path,
        "output": output,
    }

    print(json.dumps(result, indent=2))


def cmd_validate():
    """Validate all cron jobs against conventions."""
    jobs = get_cron_jobs()

    if not jobs:
        print(json.dumps({"status": "ok", "message": "No cron jobs found"}))
        return

    results = []
    for job in jobs:
        issues = []
        name = job.get("name", "")
        agent = job.get("agentId", "")

        # Naming
        issues.extend(validate_name(name))
        if agent and not name.startswith(f"{agent}_"):
            issues.append(f"Name should be prefixed with agent id '{agent}'")

        # Session isolation
        session = job.get("sessionTarget", "")
        if session != "isolated":
            issues.append(f"Session is '{session}', should be 'isolated'")

        # Model and thinking
        if not job.get("model"):
            issues.append("Model not explicitly set")
        if job.get("thinking") is None:
            issues.append("Thinking not explicitly set")

        # Message references a file
        message = job.get("message", "")
        if len(message) > 200 and "cron/" not in message.lower():
            issues.append("Message appears to be an inline prompt — should reference a cron/ file")

        # Delivery mode + channel targeting
        delivery = job.get("delivery", {})
        mode = delivery.get("mode", "")
        if mode == "announce":
            channel = delivery.get("channel", "")
            to = delivery.get("to", "")
            if not channel or not to or to == "last":
                issues.append("Announce mode should have explicit channel and target (not 'last')")

        # Schedule type
        kind = job.get("kind", "")
        if kind == "every":
            issues.append("Uses interval-based 'every' schedule — prefer 'cron' expressions")

        entry = {"name": name, "agent": agent}
        if issues:
            entry["issues"] = issues
            entry["status"] = "fail"
        else:
            entry["status"] = "pass"
        results.append(entry)

    failures = [r for r in results if r["status"] == "fail"]
    print(json.dumps({
        "total": len(results),
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "results": results,
    }, indent=2))


def cmd_list():
    """List all cron jobs with key info."""
    jobs = get_cron_jobs()

    if not jobs:
        print(json.dumps({"jobs": [], "message": "No cron jobs found"}))
        return

    result = []
    for job in jobs:
        entry = {
            "name": job.get("name", ""),
            "agent": job.get("agentId", ""),
            "schedule": job.get("cron", job.get("every", "")),
            "model": job.get("model", ""),
            "thinking": job.get("thinking", ""),
            "delivery": job.get("delivery", {}).get("mode", "none"),
            "enabled": job.get("enabled", True),
            "status": job.get("status", ""),
        }
        last_run = job.get("lastRun", {})
        if last_run:
            entry["last_run"] = last_run.get("completedAt", "")
            entry["last_status"] = last_run.get("status", "")
        result.append(entry)

    print(json.dumps(result, indent=2))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: cron.py <create|validate|list> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "create":
        cmd_create(sys.argv[2:])
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "list":
        cmd_list()
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}. Use create, validate, or list."}))
        sys.exit(1)


if __name__ == "__main__":
    main()

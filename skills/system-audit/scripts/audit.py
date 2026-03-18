#!/usr/bin/env python3
"""System audit — check an OpenClaw install against playbook standards.

Usage:
    audit.py run                     Full audit
    audit.py check <area>            Check specific area (workspace|crons|config|gateway)
"""

import json
import os
import subprocess
import sys

OPENCLAW_DIR = os.environ.get("OPENCLAW_STATE_DIR", os.path.expanduser("~/.openclaw"))
CONFIG_FILE = os.path.join(OPENCLAW_DIR, "openclaw.json")


def run_cmd(args, check=False):
    """Run a command and return (stdout, stderr, returncode)."""
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def load_config():
    """Load openclaw.json."""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE) as f:
        return json.load(f)


def check_workspace():
    """Check workspace structure for all agents."""
    findings = {"fixed": [], "needs_attention": []}
    config = load_config()
    if not config:
        findings["needs_attention"].append("openclaw.json not found")
        return findings

    agents = config.get("agents", {}).get("list", [])
    for agent in agents:
        agent_id = agent.get("id", "unknown")
        workspace = agent.get("workspace", "")
        workspace = os.path.expanduser(workspace)

        if not os.path.exists(workspace):
            findings["needs_attention"].append(f"Agent '{agent_id}': workspace directory missing at {workspace}")
            continue

        # Check required directories
        required_dirs = ["memory", "cron", "skills", "output", "data", "tmp"]
        for d in required_dirs:
            dir_path = os.path.join(workspace, d)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                findings["fixed"].append(f"Agent '{agent_id}': created missing directory {d}/")

        # Check AGENTS.md exists
        agents_md = os.path.join(workspace, "AGENTS.md")
        if not os.path.exists(agents_md):
            findings["needs_attention"].append(f"Agent '{agent_id}': AGENTS.md missing in workspace")

        # Check agent dir exists
        agent_dir = agent.get("agentDir", "")
        if agent_dir:
            agent_dir = os.path.expanduser(agent_dir)
            if not os.path.exists(agent_dir):
                os.makedirs(agent_dir, exist_ok=True)
                findings["fixed"].append(f"Agent '{agent_id}': created missing agent directory")

    return findings


def check_crons():
    """Check cron jobs for standards compliance."""
    findings = {"fixed": [], "needs_attention": []}

    stdout, stderr, rc = run_cmd(["openclaw", "cron", "list", "--json"])
    if rc != 0:
        findings["needs_attention"].append(f"Failed to list cron jobs: {stderr}")
        return findings

    if not stdout:
        return findings

    jobs = json.loads(stdout)
    config = load_config()
    agents_by_id = {}
    if config:
        for agent in config.get("agents", {}).get("list", []):
            agents_by_id[agent["id"]] = agent

    for job in jobs:
        name = job.get("name", "")
        agent_id = job.get("agentId", "")

        # Check error state
        status = job.get("status", "")
        if status == "error":
            error_msg = job.get("lastError", "unknown")
            findings["needs_attention"].append(f"Cron '{name}': in error state — {error_msg}")

        # Check naming
        if agent_id and not name.startswith(f"{agent_id}_"):
            findings["needs_attention"].append(f"Cron '{name}': name should be prefixed with '{agent_id}_'")

        # Check session isolation
        session = job.get("sessionTarget", "")
        if session and session != "isolated":
            findings["needs_attention"].append(f"Cron '{name}': session is '{session}', should be 'isolated'")

        # Check model/thinking set
        if not job.get("model"):
            findings["needs_attention"].append(f"Cron '{name}': model not explicitly set")
        if job.get("thinking") is None:
            findings["needs_attention"].append(f"Cron '{name}': thinking not explicitly set")

        # Check prompt file exists
        message = job.get("message", "")
        if "cron/" in message:
            # Extract filename from message like "Read cron/foo.md and follow..."
            import re
            match = re.search(r"cron/([^\s]+\.md)", message)
            if match and agent_id in agents_by_id:
                prompt_file = match.group(0)
                workspace = os.path.expanduser(agents_by_id[agent_id].get("workspace", ""))
                full_path = os.path.join(workspace, prompt_file)
                if not os.path.exists(full_path):
                    findings["needs_attention"].append(
                        f"Cron '{name}': prompt file '{prompt_file}' not found in workspace"
                    )

    return findings


def check_config():
    """Check config for standard compliance."""
    findings = {"fixed": [], "needs_attention": []}
    config = load_config()
    if not config:
        findings["needs_attention"].append("openclaw.json not found")
        return findings

    defaults = config.get("agents", {}).get("defaults", {})

    # Heartbeat disabled
    heartbeat = defaults.get("heartbeat", {}).get("every", "")
    if heartbeat and heartbeat != "0m":
        findings["needs_attention"].append(f"Heartbeat is '{heartbeat}', should be '0m' (disabled)")

    # skipBootstrap
    if not defaults.get("skipBootstrap"):
        findings["needs_attention"].append("skipBootstrap is not set to true")

    # Check for hardcoded secrets
    config_str = json.dumps(config)
    if "xoxb-" in config_str or "xapp-" in config_str or "sk-ant-" in config_str or "sk-" in config_str:
        # Check if they're ${VAR} references
        import re
        hardcoded = re.findall(r'(?<!\$\{)(xoxb-[^\s"]+|xapp-[^\s"]+|sk-ant-[^\s"]+)', config_str)
        if hardcoded:
            findings["needs_attention"].append("Possible hardcoded secrets in openclaw.json — use ${VAR} references")

    # SHARED.md exists
    shared_md = os.path.join(OPENCLAW_DIR, "SHARED.md")
    if not os.path.exists(shared_md):
        findings["needs_attention"].append("SHARED.md missing in ~/.openclaw/")

    # .env exists
    env_file = os.path.join(OPENCLAW_DIR, ".env")
    if not os.path.exists(env_file):
        findings["needs_attention"].append(".env file missing in ~/.openclaw/")

    # Skills directory
    skills_dir = os.path.join(OPENCLAW_DIR, "skills")
    if not os.path.exists(skills_dir):
        findings["needs_attention"].append("Shared skills directory missing (expected ~/.openclaw/skills/)")

    return findings


def check_gateway():
    """Check gateway health."""
    findings = {"fixed": [], "needs_attention": []}

    stdout, stderr, rc = run_cmd(["openclaw", "gateway", "status"])
    if rc != 0:
        findings["needs_attention"].append(f"Gateway status check failed: {stderr or 'not running'}")
        return findings

    if "not running" in stdout.lower() or "error" in stdout.lower():
        findings["needs_attention"].append(f"Gateway issue: {stdout}")

    return findings


def run_full_audit():
    """Run all checks."""
    results = {}
    all_fixed = []
    all_attention = []

    for area, checker in [
        ("workspace", check_workspace),
        ("crons", check_crons),
        ("config", check_config),
        ("gateway", check_gateway),
    ]:
        findings = checker()
        results[area] = findings
        all_fixed.extend(findings["fixed"])
        all_attention.extend(findings["needs_attention"])

    report = {
        "summary": {
            "fixed_count": len(all_fixed),
            "attention_count": len(all_attention),
            "status": "clean" if not all_attention else "needs_attention",
        },
        "fixed": all_fixed,
        "needs_attention": all_attention,
        "details": results,
    }
    print(json.dumps(report, indent=2))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: audit.py <run|check> [area]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "run":
        run_full_audit()
    elif cmd == "check":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: audit.py check <workspace|crons|config|gateway>"}))
            sys.exit(1)
        area = sys.argv[2]
        checkers = {
            "workspace": check_workspace,
            "crons": check_crons,
            "config": check_config,
            "gateway": check_gateway,
        }
        if area not in checkers:
            print(json.dumps({"error": f"Unknown area: {area}. Use: {', '.join(checkers.keys())}"}))
            sys.exit(1)
        findings = checkers[area]()
        print(json.dumps(findings, indent=2))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}. Use run or check."}))
        sys.exit(1)


if __name__ == "__main__":
    main()

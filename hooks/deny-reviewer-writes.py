#!/usr/bin/env python3
"""PreToolUse hook: keep the staff-engineer plan reviewer read-only.

The reviewer is defined with ``tools: Read, Grep, Glob``, but when the
plan-with-review skill spawns it as an agent-teams teammate, that allowlist is
not reliably enforced and the teammate inherits the lead's (often permissive)
permission mode. This hook is the mechanical backstop: it denies write tools for
the reviewer agent regardless of how it was spawned.

Scope: the hooks.json matcher already limits this to write tools, and this
script only acts when the calling agent is the reviewer, so the main session and
other agents are unaffected. SendMessage and the task tools are never matched, so
the reviewer can still return its written review.
"""
import json
import sys

REVIEWER_AGENT = "staff-engineer"
BLOCKED_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit", "Bash"}

DENY_REASON = (
    "The staff-engineer plan reviewer is read-only. Editing files, running shell "
    "commands, committing, pushing, or opening pull requests is not permitted. "
    "Return your written review instead."
)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Fail open: a malformed payload must never wedge the whole session.
        return

    if data.get("agent_type") != REVIEWER_AGENT:
        return
    if data.get("tool_name") not in BLOCKED_TOOLS:
        return

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": DENY_REASON,
        }
    }
    print(json.dumps(decision))


if __name__ == "__main__":
    main()

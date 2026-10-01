#!/usr/bin/env python3
"""Stop hook shared by Cursor (.cursor/hooks.json) and Antigravity (.agents/hooks.json).

Runs .githooks/pre-commit when the working tree has changes and hands failures back to the agent.
"""

import json
import os
import subprocess
import sys
import tempfile

MAX_RETRIES = 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETRY_FILE = os.path.join(tempfile.gettempdir(), "agent-harness-stop-retries.json")

os.chdir(ROOT)
event = json.loads(sys.stdin.read() or "{}")
antigravity = "terminationReason" in event


def finish(message=None):
    if message is None:
        print("{}")
    elif antigravity:
        print(json.dumps({"decision": "continue", "reason": message}, ensure_ascii=False))
    else:
        print(json.dumps({"followup_message": message}, ensure_ascii=False))
    sys.exit(0)


def record_attempt(failed):
    """Antigravity has no loop_limit, so consecutive failures are counted per conversation here."""
    try:
        with open(RETRY_FILE, "r", encoding="utf-8") as f:
            counts = json.load(f)
    except (OSError, ValueError):
        counts = {}
    key = event.get("conversationId", "")
    count = counts.get(key, 0) + 1 if failed else 0
    counts[key] = 0 if count > MAX_RETRIES else count
    with open(RETRY_FILE, "w", encoding="utf-8") as f:
        json.dump(counts, f)
    return count


def failing_output():
    if not subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip():
        return None
    res = subprocess.run(
        ["sh", ".githooks/pre-commit"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=dict(os.environ, PYTHONUNBUFFERED="1"),
    )
    if res.returncode == 0:
        return None
    return "\n".join(res.stdout.splitlines()[-60:])


# Antigravity's docs say "model_stop" but real runs send "NO_TOOL_CALL", so only skip clearly abnormal endings
reason = event.get("terminationReason", "").lower()
if event.get("status") in ("aborted", "error") or event.get("error") or any(
        word in reason for word in ("error", "cancel", "abort", "max_steps")):
    finish()

failure = failing_output()
if antigravity and record_attempt(failure is not None) > MAX_RETRIES:
    finish()
if failure is None:
    finish()
finish("自动校验未通过（单元测试 / 编译 / agent-harness check）。请根据下面的输出修复，修好后简要说明改了什么：\n\n" + failure)

#!/usr/bin/env python3
"""Cursor stop hook: run .githooks/pre-commit and hand failures back to the agent as a follow-up."""

import json
import os
import subprocess
import sys

event = json.loads(sys.stdin.read() or "{}")
dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
if event.get("status") in ("aborted", "error") or not dirty:
    print("{}")
    sys.exit(0)

res = subprocess.run(
    ["sh", ".githooks/pre-commit"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=dict(os.environ, PYTHONUNBUFFERED="1"),
)
if res.returncode == 0:
    print("{}")
    sys.exit(0)

tail = "\n".join(res.stdout.splitlines()[-60:])
print(json.dumps({
    "followup_message": "自动校验未通过（单元测试 / 编译 / agent-harness check）。请根据下面的输出修复，修好后简要说明改了什么：\n\n" + tail
}, ensure_ascii=False))

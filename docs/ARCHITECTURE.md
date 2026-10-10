# agent-harness Architecture & Technical Design

`agent-harness` is a universal, tool-agnostic anti-drift framework and codebase memory harness designed for AI coding agents (such as TRAE, Cursor, Claude Code, Antigravity, Windsurf, Zed, and VS Code).

---

## 1. System Architecture

The framework consists of three tightly coupled, lightweight layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                       AI Development Clients                           │
│     TRAE  ·  Cursor  ·  Claude Code  ·  Antigravity  ·  Windsurf       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (Model Context Protocol / stdio)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Layer 1: Cognitive Memory (C Engine Daemon)              │
│       codebase-memory-mcp (C / SQLite AST / Call Graph / ZSTD)         │
│                 Port 9749 3D Visualization Dashboard                   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (CLI / Subprocess Bridge)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Layer 2: Universal Harness CLI & Generator               │
│                        bin/agent-harness                               │
│           ├── init: Graph Indexing + Tailored AGENTS.md + Imports      │
│           ├── check: AGENTS.md vs repo stack / entry / test commands   │
│           ├── sync: Refresh marker-managed facts (keeps section 5)     │
│           ├── verify: Run AGENTS.md test commands (IDE stop hooks)     │
│           ├── guard: Ask before git discards work (pre-command hooks)  │
│           ├── setup: Multi-IDE MCP Auto-Configuration                  │
│           ├── status: Healthcheck & Indexed Projects Registry          │
│           └── ui: Open Visualizer once port 9749 answers               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (File System & Git Protection)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Layer 3: Behavioral & Physical Guardrails                │
│    ├── AGENTS.md (Karpathy 4 Rules + Auto-detected Test Harness)       │
│    ├── Stop Hooks: .cursor / .claude / .agents -> agent-harness verify │
│    ├── Pre-command Hooks: .cursor / .claude -> agent-harness guard     │
│    ├── Alias Files: CLAUDE.md / GEMINI.md (one-line @AGENTS.md)       │
│    └── Git Isolation: Global ~/.gitignore_global + Project .gitignore │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Execution Flows

### Flow A: Project Initialization (`agent-harness init [path]`)
1. **Keep existing rules**: If `AGENTS.md` is missing, create it. If it exists, keep every current line and append only the missing pieces: auto markers, Karpathy rules, test commands, doc alignment, and graph-search rules. A file that already contains those anchors is left unchanged, and a file with its own `测试与校验命令` heading keeps that list as the only one.
2. **Knowledge Graph Indexing**: Calls `codebase-memory-mcp cli --json index_repository` with `{"repo_path": <dir>}` on stdin to ingest AST and call chains. An engine that fails to start or runs past 10 minutes counts as no result: `init` warns and still writes `AGENTS.md`.
3. **Stack Fact Detection**: Derives languages and entry points from filesystem rules only — the same rules `check` / `sync` use — so a fresh `init` never fails `check`, and the result does not depend on whether the engine is installed. The graph itself is for agents to query at runtime (its own entry-point heuristic, e.g. exported functions, intentionally does not feed `AGENTS.md`).
4. **Test Harness Synthesis**: Reads manifests and the commands the repo already has: Cargo/Go toolchains, `package.json` `scripts.test` / `scripts.lint` (with Bun the test line is `bun run test`, which runs `scripts.test`), `tsconfig.json`, pytest signals, and ruff config. pytest is chosen for `pytest.ini`, `conftest.py`, `tests/conftest.py`, `[tool.pytest` in `pyproject.toml`, `[tool:pytest]` in `setup.cfg`, `[pytest]` in `tox.ini`, or `tests/test*.py` files that never mention `unittest` (unittest discover reports such files as "Ran 0 tests ... OK"). The `py_compile` line lists the real Python entry files: `app.py`, `main.py`, `src/main.py`, and Python scripts in `bin/`. A Python project without `tests/test*.py`, or a `package.json` without `scripts.test`, gets a guidance line instead of a command. When the root lacks a stack's manifest, sub-directories up to two levels down are scanned (skipping dependency, build, test, fixture, and example directories), and each sub-project's commands run as `cd <dir> && <cmd>`.
5. **Template Assembly**: Dynamically loads `templates/karpathy_rules.md` (with embedded fallback) to compose the finalized `AGENTS.md`.
6. **Cross-IDE Compatibility**: Writes `CLAUDE.md` / `GEMINI.md` containing only `@AGENTS.md` (an import, not a symlink, so tools that read several rule files load the rules once and Windows needs no copy fallback). Legacy symlinks to `AGENTS.md` from older versions, including `.cursorrules`, are migrated; hand-written alias files are left untouched.
7. **Git Safety Shielding**: Ensures `.codebase-memory/` and graph artifacts are excluded in `.gitignore`.
8. **Hooks**: Adds the stop hook `agent-harness verify --hook` to `.cursor/hooks.json` (with `loop_limit: 3`), `.claude/settings.json`, and `.agents/hooks.json`, and the pre-command hook `agent-harness guard` to `.cursor/hooks.json` (`beforeShellExecution`, matcher `git`) and `.claude/settings.json` (`PreToolUse`, matcher `Bash`). Antigravity gets the stop hook only: a failing Antigravity `PreToolUse` hook blocks the call, so a machine without the CLI would lose every command. Existing entries stay, each hook is added only once, and an unparseable file is copied to `.bak` before it is rewritten. Config files are written the same way as in Flow B. See Flow D and Flow E.
9. A second `init` on a file that already has those sections prints a reminder to run `agent-harness check` / `sync`.

### Flow B: Global Setup (`agent-harness setup`)
1. Writes MCP config for these clients, whether or not the client is installed yet (a later install picks the config up automatically):
   - TRAE (`~/Library/Application Support/TRAE SOLO CN/User/mcp.json`, `~/.trae/mcp.json`, `%APPDATA%\Trae\User\mcp.json`)
   - Cursor (`~/.cursor/mcp.json`)
   - Claude Code (`~/.claude.json`)
   - Antigravity / Gemini CLI (`~/.gemini/config/mcp_config.json`)
   - Windsurf (`~/.codeium/windsurf/mcp_config.json`)
2. Injects or merges `codebase-memory-mcp` definition safely into each client's `mcpServers` section without overwriting other tools. Each file is written to a temp file beside it and swapped in with `os.replace`, so an interrupted write leaves the old file whole; non-ASCII text such as Chinese project paths stays literal.
3. Appends graph ignore rules (`.codebase-memory/`, `*.graph.db*`, `*.db.zst`) to the excludes file `git config --global --get core.excludesfile` already points at. When that setting is unset, writes `~/.gitignore_global` and sets `core.excludesfile` to it.
4. Zed and VS Code are not given an MCP file. They read `AGENTS.md` from the repository.

### Flow C: Doc/Code Alignment (`agent-harness check` / `sync`)
1. **`check`**: Re-detects languages, every `bin/` entry point, and the stacks `harness_plan` covers. Fails if `AGENTS.md` is missing a language or entry point, or has no test command for a stack. Any equivalent runner counts: `cargo test` / `cargo nextest`; `go test`; `npm` / `pnpm` / `yarn` / `bun` test, `vitest`, `jest`, `mocha`, `playwright test`; `pytest` / `unittest` / `tox` / `nox`. Lint and type-check lines are written but not required, and placeholder lines are not checked. Languages include `.tsx` as TypeScript and `.jsx` / `.mjs` / `.cjs` as JavaScript, plus `.vue`. The scan skips `node_modules`, `target`, `vendor`, `venv`, `dist`, `build`, `tmp`, `scratch`, and dot-directories such as `.next`.
2. **`check` docs**: In a git work tree, a changed implementation file fails the command when a README / `docs/` / `AGENTS.md` paragraph cites that path and that markdown file is not in the same change. Changes come from `git status --porcelain -z` limited to the target directory, so non-ASCII paths stay readable and paths are relative to the target, like the docs; inside a git commit hook (`GIT_INDEX_FILE` is set) only staged changes count. `<!-- agent-harness:auto:* -->` blocks are inventories, not explanations, so a path that appears only there still needs a real write-up. A citation is the whole path: a sentence-ending period after it still counts, while `bin/tool.py` does not cite `bin/tool`. URLs are not citations, and history docs (`CHANGELOG`, `CHANGES`, `HISTORY`, files under `adr/` or `decisions/`) count neither as citations nor as updates. Test files alone pass: files in test directories plus `test_*.py`, `*_test.py`, `*_test.go`, `*.test.*`, and `*.spec.*`. Markdown that is not valid UTF-8 is read with replacement characters. With no git metadata, this part is skipped.
3. **`sync`**: Replaces only `<!-- agent-harness:auto:languages|entries|harness -->` blocks. If no markers exist, refuses to write (zero-overwrite for hand-crafted docs). Section 5 custom invariants are never touched. The generated `AGENTS.md` tells agents to delete a block's pair of markers before customizing it (for example, a test command that needs an environment variable); `sync` then skips that block, and `init` keeps it as the command list.
4. New `init` output embeds those markers plus the doc-alignment clause in the test loop. The listed commands end with `agent-harness check`, so the stop hooks (Flow D) hand a failing doc alignment back to the agent. This repository runs the same checks from `.githooks/pre-commit`, and its own `.cursor/hooks.json` / `.agents/hooks.json` call `python3 bin/agent-harness verify --hook`, so changes to `verify` are exercised in the repo that ships them.

### Flow D: Auto-Verify (`agent-harness verify [path]`)
1. **Commands**: Reads the lines written as ``- **name**：`command` `` under the `测试与校验命令` heading of `AGENTS.md`. Placeholder commands (starting with `#`) and guidance lines are skipped. The commands run in order from the directory holding `AGENTS.md` (the nearest one at or above the given path or the working directory), and the run stops at the first failure. On Windows a `python3` shim for the running interpreter is put on `PATH`. Child commands get `PYTHONIOENCODING=utf-8` and an empty stdin, so a prompt for input ends instead of waiting. Output goes to a temp file rather than a pipe, so a background process left behind by a command cannot hold the run open.
2. **Manual run**: Prints each command with its output and exits 1 on the first failure.
3. **Hook mode (`--hook`)**: Reads the stop event as JSON on stdin and replies in the calling IDE's format: Cursor `{"followup_message": ...}`, Claude Code `{"decision": "block", "reason": ...}`, Antigravity `{"decision": "continue", "reason": ...}`. The reply carries the failing command and the last 60 lines of its output. The commands run only when the work tree changed since the hook last looked at the project: a fingerprint of `HEAD`, `git status`, and the size and modification time of each changed file is compared with the one stored after the previous stop. A question-only turn therefore ends at once, while a turn that edited or committed files is verified. On the first look at a project the commands run only if the tree has uncommitted changes. The fingerprint is stored after the commands finish, so files they create count as the new baseline. A directory outside git, an aborted or errored turn, or a directory without `AGENTS.md` gets `{}`, and the agent stops normally.
4. **Time budget**: In hook mode the commands share 270 seconds (the hook timeout is 300). The command still running when the budget is spent is stopped together with its child processes (process group on macOS / Linux, `taskkill /T` on Windows), and the reply names it with a note to make the command finish on its own (watch mode off, no input prompts) or to run a slow first build once in a terminal.
5. **Round limit**: At most 3 consecutive failing rounds per conversation. Cursor enforces it through `loop_limit`; for Claude Code and Antigravity the count lives in the same JSON state file in the system temp directory as the fingerprints, keyed by project and session / conversation id, and resets after a passing round or once the limit is reached.

### Flow E: Git Guard (`agent-harness guard`)
1. **Input**: Reads the pre-command event as JSON on stdin: Cursor `beforeShellExecution` carries `command`, Claude Code `PreToolUse` carries `tool_input.command`. Unparseable input gets `{}`.
2. **Detection**: `git_danger` tokenizes the command line with `shlex` (punctuation-aware, so `&&`, `;` and `|` split it into separate calls; unbalanced quotes fall back to whitespace splitting) and checks each call whose first word, after `VAR=value` prefixes, is `git` / `git.exe`. Global options such as `-C <dir>` and `-c <key=value>` are skipped before the subcommand. A call discards work for `reset --hard`; `checkout` with `--`, `.` or `-f`; `restore` unless it is `--staged` only; `clean -f`; `push` with `--force`, `-f`, `--force-with-lease` or a `+ref`; `branch -D` or `--delete --force`; `stash drop` / `clear`. Text that only mentions git (`echo git reset --hard`, a commit message) stays allowed.
3. **Reply**: A discarding call gets "ask" in the calling IDE's format: Cursor `{"permission": "ask", "user_message", "agent_message"}`, Claude Code `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason"}}`. The message names what is lost and quotes the git call alone. Every other command gets `{}`, so the IDE's own approval settings decide as before.

---

## 3. Design Decisions & Trade-Offs

| Decision | Selected Approach | Rationale |
| :--- | :--- | :--- |
| **Runtime Language** | Python 3 Standard Library only | Zero external dependencies (`pip`/`npm`), runs out of the box on macOS, Linux, and Windows. The second line of `bin/agent-harness` declares `# -*- coding: utf-8 -*-`: without it, Python 3.9 checks a script it runs directly in 511-byte pieces on Windows and rejects a long line of Chinese text whose piece ends inside a character. |
| **Memory Engine** | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (C / SQLite) | Single self-contained binary (~300MB on macOS), sub-millisecond AST queries, 99%+ token reduction, small idle RAM footprint (~15MB measured). Installers always fetch the latest release (`releases/latest`) and upgrade in place, stopping older engine processes first because a newer engine refuses to start alongside them. `run_cbm_cli(tool, params)` calls `cli --json <tool>` with the params piped as JSON on stdin (0.11 deprecates raw JSON as a positional argument) and unwraps `structuredContent` from the MCP tool-result envelope. Tools that default to a text table in 0.11 (e.g. `list_projects`) are called with `format: "json"`. Unrecognized output makes `init` / `status` warn instead of reporting 0 nodes or 0 projects; an engine that fails to start or runs past 10 minutes is treated the same way. |
| **Specification Source of Truth** | Universal `AGENTS.md` | Adopted by the Agentic AI Foundation / Linux Foundation; supported natively by modern IDEs, backward-compatible via one-line `@AGENTS.md` imports. |
| **Verification Loop** | Test Harness + `agent-harness check` + IDE stop hooks | Compilers catch broken code; `check` fails when AGENTS.md drifts from stack facts, or when a doc that cites a changed implementation path was left unchanged. The stop hooks `init` installs run `agent-harness verify` at the end of each agent turn that changed files and return the first failure or timeout to the agent. |

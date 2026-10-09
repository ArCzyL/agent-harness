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
│           ├── setup: Multi-IDE MCP Auto-Configuration                  │
│           ├── status: Healthcheck & Indexed Projects Registry          │
│           └── ui: Browser Visualizer Launcher                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (File System & Git Protection)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Layer 3: Behavioral & Physical Guardrails                │
│    ├── AGENTS.md (Karpathy 4 Rules + Auto-detected Test Harness)       │
│    ├── Stop Hooks: .cursor / .claude / .agents -> agent-harness verify │
│    ├── Alias Files: CLAUDE.md / GEMINI.md (one-line @AGENTS.md)       │
│    └── Git Isolation: Global ~/.gitignore_global + Project .gitignore │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Execution Flows

### Flow A: Project Initialization (`agent-harness init [path]`)
1. **Keep existing rules**: If `AGENTS.md` is missing, create it. If it exists, keep every current line and append only the missing pieces: auto markers, Karpathy rules, test commands, doc alignment, and graph-search rules. A file that already contains those anchors is left unchanged.
2. **Knowledge Graph Indexing**: Calls `codebase-memory-mcp cli --json index_repository` with `{"repo_path": <dir>}` on stdin to ingest AST and call chains. An engine that fails to start or runs past 10 minutes counts as no result: `init` warns and still writes `AGENTS.md`.
3. **Stack Fact Detection**: Derives languages and entry points from filesystem rules only — the same rules `check` / `sync` use — so a fresh `init` never fails `check`, and the result does not depend on whether the engine is installed. The graph itself is for agents to query at runtime (its own entry-point heuristic, e.g. exported functions, intentionally does not feed `AGENTS.md`).
4. **Test Harness Synthesis**: Reads manifests and the commands the repo already has: Cargo/Go toolchains, `package.json` `scripts.test` / `scripts.lint` (with Bun the test line is `bun run test`, which runs `scripts.test`), `tsconfig.json`, pytest signals, and ruff config. pytest is chosen for `pytest.ini`, `conftest.py`, `tests/conftest.py`, `[tool.pytest` in `pyproject.toml`, `[tool:pytest]` in `setup.cfg`, `[pytest]` in `tox.ini`, or `tests/test*.py` files that never mention `unittest` (unittest discover reports such files as "Ran 0 tests ... OK"). The `py_compile` line lists the real Python entry files: `app.py`, `main.py`, `src/main.py`, and Python scripts in `bin/`. A Python project without `tests/test*.py`, or a `package.json` without `scripts.test`, gets a guidance line instead of a command. When the root lacks a stack's manifest, sub-directories up to two levels down are scanned (skipping dependency, build, test, fixture, and example directories), and each sub-project's commands run as `cd <dir> && <cmd>`.
5. **Template Assembly**: Dynamically loads `templates/karpathy_rules.md` (with embedded fallback) to compose the finalized `AGENTS.md`.
6. **Cross-IDE Compatibility**: Writes `CLAUDE.md` / `GEMINI.md` containing only `@AGENTS.md` (an import, not a symlink, so tools that read several rule files load the rules once and Windows needs no copy fallback). Legacy symlinks to `AGENTS.md` from older versions, including `.cursorrules`, are migrated; hand-written alias files are left untouched.
7. **Git Safety Shielding**: Ensures `.codebase-memory/` and graph artifacts are excluded in `.gitignore`.
8. **Stop Hooks**: Adds `agent-harness verify --hook` to `.cursor/hooks.json` (with `loop_limit: 3`), `.claude/settings.json`, and `.agents/hooks.json`. Existing entries stay, the hook is added only once, and an unparseable file is copied to `.bak` before it is rewritten. See Flow D.
9. A second `init` on a file that already has those sections prints a reminder to run `agent-harness check` / `sync`.

### Flow B: Global Setup (`agent-harness setup`)
1. Writes MCP config for these clients, whether or not the client is installed yet (a later install picks the config up automatically):
   - TRAE (`~/Library/Application Support/TRAE SOLO CN/User/mcp.json`, `~/.trae/mcp.json`, `%APPDATA%\Trae\User\mcp.json`)
   - Cursor (`~/.cursor/mcp.json`)
   - Claude Code (`~/.claude.json`)
   - Antigravity / Gemini CLI (`~/.gemini/config/mcp_config.json`)
   - Windsurf (`~/.codeium/windsurf/mcp_config.json`)
2. Injects or merges `codebase-memory-mcp` definition safely into each client's `mcpServers` section without overwriting other tools.
3. Appends graph ignore rules (`.codebase-memory/`, `*.graph.db*`, `*.db.zst`) to the excludes file `git config --global --get core.excludesfile` already points at. When that setting is unset, writes `~/.gitignore_global` and sets `core.excludesfile` to it.
4. Zed and VS Code are not given an MCP file. They read `AGENTS.md` from the repository.

### Flow C: Doc/Code Alignment (`agent-harness check` / `sync`)
1. **`check`**: Re-detects languages, every `bin/` entry point, and the stacks `harness_plan` covers. Fails if `AGENTS.md` is missing a language or entry point, or has no test command for a stack. Any equivalent runner counts: `cargo test` / `cargo nextest`; `go test`; `npm` / `pnpm` / `yarn` / `bun` test, `vitest`, `jest`, `mocha`, `playwright test`; `pytest` / `unittest` / `tox` / `nox`. Lint and type-check lines are written but not required, and placeholder lines are not checked. Languages include `.tsx` as TypeScript and `.jsx` / `.mjs` / `.cjs` as JavaScript, plus `.vue`. The scan skips `node_modules`, `target`, `vendor`, `venv`, `dist`, `build`, and dot-directories such as `.next`.
2. **`check` docs**: In a git work tree, a changed implementation file fails the command when a README / `docs/` / `AGENTS.md` paragraph cites that path and that markdown file is not in the same change. Changes come from `git status --porcelain -z` limited to the target directory, so non-ASCII paths stay readable and paths are relative to the target, like the docs; inside a git commit hook (`GIT_INDEX_FILE` is set) only staged changes count. `<!-- agent-harness:auto:* -->` blocks are inventories, not explanations, so a path that appears only there still needs a real write-up. URLs are not citations, and history docs (`CHANGELOG`, `CHANGES`, `HISTORY`, files under `adr/` or `decisions/`) count neither as citations nor as updates. Test files alone pass: files in test directories plus `test_*.py`, `*_test.py`, `*_test.go`, `*.test.*`, and `*.spec.*`. Markdown that is not valid UTF-8 is read with replacement characters. With no git metadata, this part is skipped.
3. **`sync`**: Replaces only `<!-- agent-harness:auto:languages|entries|harness -->` blocks. If no markers exist, refuses to write (zero-overwrite for hand-crafted docs). Section 5 custom invariants are never touched.
4. New `init` output embeds those markers plus the doc-alignment clause in the test loop. The listed commands end with `agent-harness check`, so the stop hooks (Flow D) hand a failing doc alignment back to the agent. This repository runs the same checks from `.githooks/pre-commit` and `.githooks/agent-stop.py`.

### Flow D: Auto-Verify (`agent-harness verify [path]`)
1. **Commands**: Reads the lines written as ``- **name**：`command` `` under the `测试与校验命令` heading of `AGENTS.md`. Placeholder commands (starting with `#`) and guidance lines are skipped. The commands run in order from the directory holding `AGENTS.md` (the nearest one at or above the given path or the working directory), and the run stops at the first failure. On Windows a `python3` shim for the running interpreter is put on `PATH`, and child commands get `PYTHONIOENCODING=utf-8`.
2. **Manual run**: Prints each command with its output and exits 1 on the first failure.
3. **Hook mode (`--hook`)**: Reads the stop event as JSON on stdin and replies in the calling IDE's format: Cursor `{"followup_message": ...}`, Claude Code `{"decision": "block", "reason": ...}`, Antigravity `{"decision": "continue", "reason": ...}`. The reply carries the failing command and the last 60 lines of its output. A clean work tree, a directory outside git, an aborted or errored turn, or a directory without `AGENTS.md` gets `{}`, and the agent stops normally.
4. **Round limit**: At most 3 consecutive failing rounds per conversation. Cursor enforces it through `loop_limit`; for Claude Code and Antigravity the count lives in a JSON file in the system temp directory, keyed by project and session / conversation id, and resets after a passing round or once the limit is reached.

---

## 3. Design Decisions & Trade-Offs

| Decision | Selected Approach | Rationale |
| :--- | :--- | :--- |
| **Runtime Language** | Python 3 Standard Library only | Zero external dependencies (`pip`/`npm`), runs out of the box on macOS, Linux, and Windows. |
| **Memory Engine** | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (C / SQLite) | Single self-contained binary (~300MB on macOS), sub-millisecond AST queries, 99%+ token reduction, small idle RAM footprint (~15MB measured). Installers always fetch the latest release (`releases/latest`) and upgrade in place, stopping older engine processes first because a newer engine refuses to start alongside them. `run_cbm_cli(tool, params)` calls `cli --json <tool>` with the params piped as JSON on stdin (0.11 deprecates raw JSON as a positional argument) and unwraps `structuredContent` from the MCP tool-result envelope. Tools that default to a text table in 0.11 (e.g. `list_projects`) are called with `format: "json"`. Unrecognized output makes `init` / `status` warn instead of reporting 0 nodes or 0 projects; an engine that fails to start or runs past 10 minutes is treated the same way. |
| **Specification Source of Truth** | Universal `AGENTS.md` | Adopted by the Agentic AI Foundation / Linux Foundation; supported natively by modern IDEs, backward-compatible via one-line `@AGENTS.md` imports. |
| **Verification Loop** | Test Harness + `agent-harness check` + IDE stop hooks | Compilers catch broken code; `check` fails when AGENTS.md drifts from stack facts, or when a doc that cites a changed implementation path was left unchanged. The stop hooks `init` installs run `agent-harness verify` at the end of each agent turn and return the first failure to the agent. |

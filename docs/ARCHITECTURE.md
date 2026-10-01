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
│           ├── init: Graph Indexing + Tailored AGENTS.md + Symlinks     │
│           ├── check: AGENTS.md vs repo stack / entry / test commands   │
│           ├── sync: Refresh marker-managed facts (keeps section 5)     │
│           ├── setup: Multi-IDE MCP Auto-Configuration                  │
│           ├── status: Healthcheck & Indexed Projects Registry          │
│           └── ui: Browser Visualizer Launcher                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (File System & Git Protection)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Layer 3: Behavioral & Physical Guardrails                │
│    ├── AGENTS.md (Karpathy 4 Rules + Auto-detected Test Harness)       │
│    ├── Alias Files: CLAUDE.md / GEMINI.md (one-line @AGENTS.md)       │
│    └── Git Isolation: Global ~/.gitignore_global + Project .gitignore │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Execution Flows

### Flow A: Project Initialization (`agent-harness init [path]`)
1. **Zero-Overwrite Safety Check**: Inspects if `AGENTS.md` already exists. If present, skips generation to preserve developer-crafted custom invariants.
2. **Knowledge Graph Indexing**: Calls `codebase-memory-mcp cli index_repository --repo-path <dir>` to ingest AST and call chains.
3. **Architectural Inspection**: Extracts language breakdown and entry points with fallback to direct filesystem heuristic analysis.
4. **Test Harness Synthesis**: Analyzes project manifest files (`Cargo.toml`, `go.mod`, `package.json`, `pyproject.toml`) and binds automated test/lint commands.
5. **Template Assembly**: Dynamically loads `templates/karpathy_rules.md` (with embedded fallback) to compose the finalized `AGENTS.md`.
6. **Cross-IDE Compatibility**: Writes `CLAUDE.md` / `GEMINI.md` containing only `@AGENTS.md` (an import, not a symlink, so tools that read several rule files load the rules once and Windows needs no copy fallback). Legacy symlinks to `AGENTS.md` from older versions, including `.cursorrules`, are migrated; hand-written alias files are left untouched.
7. **Git Safety Shielding**: Ensures `.codebase-memory/` and graph artifacts are excluded in `.gitignore`.
8. If `AGENTS.md` already exists, prints a reminder to run `agent-harness check` / `sync` instead of regenerating.

### Flow B: Global Setup (`agent-harness setup`)
1. Writes to every supported client's configuration target, whether or not the client is installed yet (a later install picks the config up automatically):
   - TRAE (`~/Library/Application Support/TRAE SOLO CN/User/mcp.json`, `~/.trae/mcp.json`, `%APPDATA%\Trae\User\mcp.json`)
   - Cursor (`~/.cursor/mcp.json`)
   - Claude Code (`~/.claude.json`)
   - Antigravity / Gemini CLI (`~/.gemini/config/mcp_config.json`)
   - Windsurf (`~/.codeium/windsurf/mcp_config.json`)
2. Injects or merges `codebase-memory-mcp` definition safely into each client's `mcpServers` section without overwriting other tools.
3. Configures global Git excludes (`~/.gitignore_global`) via `git config --global core.excludesfile`.

### Flow C: Doc/Code Alignment (`agent-harness check` / `sync`)
1. **`check`**: Re-detects languages, `bin/` entry points, and stack test signals from the filesystem. Fails if `AGENTS.md` is missing those facts. Warns (does not fail) when the git working tree has code diffs but no Markdown diffs.
2. **`sync`**: Replaces only `<!-- agent-harness:auto:languages|entries|harness -->` blocks. If no markers exist, refuses to write (zero-overwrite for hand-crafted docs). Section 5 custom invariants are never touched.
3. New `init` output embeds those markers plus a "docs must match public behavior" clause in the test loop.

---

## 3. Design Decisions & Trade-Offs

| Decision | Selected Approach | Rationale |
| :--- | :--- | :--- |
| **Runtime Language** | Python 3 Standard Library only | Zero external dependencies (`pip`/`npm`), runs out of the box on macOS, Linux, and Windows. |
| **Memory Engine** | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (C / SQLite) | Single 15MB binary, sub-millisecond AST queries, 99%+ token reduction, minimal RAM footprint (<30MB). |
| **Specification Source of Truth** | Universal `AGENTS.md` | Adopted by the Agentic AI Foundation / Linux Foundation; supported natively by modern IDEs, backward-compatible via one-line `@AGENTS.md` imports. |
| **Verification Loop** | Test Harness + `agent-harness check` | Compilers catch broken code; `check` catches stale AGENTS.md that would poison the next session. |

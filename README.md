<div align="center">

# 🛡️ agent-harness

### Universal Anti-Drift Engineering Guardrail & Codebase Memory for AI Coding Agents

**Stop AI Agents from Burning 99% of Your Tokens and Writing Untested Slop.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-brightgreen.svg)](#-installation-30-seconds)
[![Compatible With](https://img.shields.io/badge/Compatible%20With-TRAE%20%7C%20Cursor%20%7C%20Claude%20Code%20%7C%20Antigravity%20%7C%20Windsurf%20%7C%20Zed-orange.svg)](#-supported-ai-environments)

[中文文档 (Chinese)](README_CN.md) • [Features](#-key-features) • [Installation](#-installation-30-seconds) • [How It Works](#-quick-start-for-any-new-or-existing-project) • [Comparison](#-comparison) • [Acknowledgements](#-acknowledgements)

</div>

---

## ⚡ The Problem: Why Coding Agents Fail

Every developer pairing with AI coding agents (Cursor, TRAE, Claude Code, Antigravity, Windsurf) faces the exact same two fatal bottlenecks:

1. **Context Amnesia & Token Burn**: The agent has zero cross-session memory. Every new window begins by blindly running full-text `grep` across hundreds of files, consuming **hundreds of thousands of tokens** just to understand basic architecture.
2. **Cognitive Drift & Untested AI Slop**: Without strict behavioral guardrails, agents make confident wrong assumptions, overcomplicate scripts with 5 layers of premature abstractions, silently reformat working code into 600-line unreviewable diffs, and say *"I'm done!"* without running a single automated test.

**`agent-harness` solves both problems permanently in a single, lightweight, tool-agnostic package.**

---

## 🚀 Key Features

* 🧠 **Persistent Codebase Knowledge Graph**:
  Powered by the open-source **[DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)** (kudos to the author and community). Uses a high-performance, single-binary C daemon to index ASTs, call graphs, routes, and type hierarchies into a local SQLite database. **Sub-millisecond queries, reducing structural exploration tokens by over 99%**.
* 🥋 **Karpathy's 4 Golden Behavioral Rules**:
  * **Think Before Writing**: Explicitly state assumptions; when requirements are ambiguous, list the interpretations and confirm with the developer before coding.
  * **Simplicity First**: Write the minimum code necessary. Build only what the current task needs and keep one-off logic inline.
  * **Surgical Edits**: Touch only what the task requires. Leave unrelated files exactly as they are; keep Git Diffs minimal and auditable.
  * **Goal-Driven Execution**: Convert every task into verifiable criteria. Write tests first, verify in terminal before delivery.
* 📝 **Rules That Survive Long Sessions**:
  The generated `AGENTS.md` states every rule affirmatively as "what to do and how", describing only the correct behavior, and asks the agent to write docs, comments, and session summaries the same way. Long-term requirements you give in chat are written into `AGENTS.md` in the same turn, so the rules stay complete and correct after context compression.
* 🔒 **Physical Test Harness (The Execution Loop)**:
  Auto-detects Go, Rust, TypeScript/Node, and Python. When the root has no manifest for a stack, sub-projects up to two levels down get commands that run in their own directory (e.g. `cd web && pnpm test`). Test commands come from scripts and config that already exist: `scripts.test`, `scripts.lint`, `tsconfig.json`, pytest / ruff config, `Cargo.toml`, and `go.mod`. `init` also adds a stop hook for Cursor, Claude Code, and Antigravity: when an agent turn ends and files changed since the hook last looked (a commit counts; a question-only turn ends at once), `agent-harness verify` runs those commands within 270 seconds and hands any failure or timeout back to the agent (up to 3 rounds). The loop:  
  $$\text{Code} \longrightarrow \text{Run Test} \longrightarrow \text{Auto-Fix Errors} \longrightarrow \text{All Green} \longrightarrow \text{Deliver}$$
* 🌐 **100% IDE & Client Agnostic**:
  MCP config is written for **TRAE, Cursor, Claude Code, Antigravity, and Windsurf**. **Zed** and **VS Code** read `AGENTS.md` from the repo; `setup` does not write an MCP file for them. Single source of truth via universal `AGENTS.md`, complemented by one-line `@AGENTS.md` import files (`CLAUDE.md`, `GEMINI.md`) instead of symlinks, so tools that read several rule files load the rules only once.
* 🛡️ **Zero-Cloud Leakage**:
  100% local execution. Automatically configures global and project-level `.gitignore` to prevent any local database or graph artifacts from polluting private GitHub repos.

---

## 📦 Installation (30 Seconds)

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/ArCzyL/agent-harness/main/install.sh | bash
```

### Windows (PowerShell)
Run PowerShell as Administrator or regular user:
```powershell
irm https://raw.githubusercontent.com/ArCzyL/agent-harness/main/install.ps1 | iex
```

### What the installer does automatically:
1. Downloads the **latest official** `codebase-memory-mcp` release and activates its daemon; re-running the installer upgrades an older engine (then restart the MCP server once in any open AI tool).
2. Writes global MCP settings for TRAE, Cursor, Claude Code, Antigravity, and Windsurf — including ones not installed yet, so they work as soon as you install them (with automated `.bak` backups on corrupted files). Each file is written to a temp file and swapped in whole, so an interrupted write keeps the old file intact. Zed and VS Code read `AGENTS.md` from the repo.
3. Appends graph ignore rules to the global excludes file Git already uses. When `core.excludesfile` is unset, creates `~/.gitignore_global` and points `core.excludesfile` at it.
4. Installs the `agent-harness` CLI into `~/.local/bin/`: `curl | bash` downloads it and the rule templates from GitHub, and `bash install.sh` inside a clone uses that clone's files.

---

## 🛠️ Quick Start: For Any New or Existing Project

Whenever you enter an existing project or start an idea from scratch:

```bash
cd /path/to/your/project
agent-harness init .
```

### Or simply talk to your AI agent:
Open **TRAE**, **Cursor**, **Claude Code**, or **Antigravity** in that project and say:
> *"Please index this project and initialize the development specification."*

### What happens:
1. **Keep What You Wrote**: An existing `AGENTS.md` stays as written. `init` appends Karpathy rules, test commands, doc alignment, and graph-search rules when those sections are missing, and leaves a file that already has them unchanged. A hand-written `测试与校验命令` section stays the project's only command list.
2. **Graph Index + Stack Facts**: Indexes the project into the local knowledge graph for agents to query; the languages and entry points written to `AGENTS.md` come from filesystem rules shared with `check` / `sync`, so they never disagree and don't depend on whether the engine is installed.
3. **Tailor-Made `AGENTS.md`**: Fills test commands from scripts and config the repo already has, plus the Karpathy rules.
4. **Universal Import Sync**: Creates `CLAUDE.md` / `GEMINI.md` containing only `@AGENTS.md`; symlinks left by older versions (including `.cursorrules`) are migrated automatically.
5. **Stop Hooks**: Adds `agent-harness verify --hook` to `.cursor/hooks.json`, `.claude/settings.json`, and `.agents/hooks.json`, keeping every entry already there (an unparseable file is backed up to `.bak` first). Commit these files so teammates share the loop; on a machine without the CLI the hook command is not found and blocks nothing.

### Keep docs aligned (before you call the task done)

The next chat session will treat `AGENTS.md` / README as ground truth. When the implementation changes, the paragraph that describes it changes in the same edit.

```bash
agent-harness check          # fail on stack / entry / test drift, and when a doc citing changed code was left unchanged
agent-harness sync           # refresh <!-- agent-harness:auto:* --> fields only; never touches section 5
agent-harness verify         # run the test commands listed in AGENTS.md in order (the stop hooks call this)
```

`check` needs one test command per detected stack, and any equivalent runner counts (`pytest` for `unittest`, `pnpm run test` for `npm test`, and so on); lint and type-check lines stay up to you. Download URLs, `CHANGELOG` / ADR files, and test files (`tests/`, `*_test.go`, `*.test.ts`, …) are left out of the doc check, and inside `git commit` only the staged changes count. To customize a marked field (say, a test command that needs an environment variable), delete its pair of markers first; `sync` then skips that section.

---

## 📊 Comparison

| Metric / Feature | Traditional Agent (Raw Grep) | With `agent-harness` |
| :--- | :---: | :---: |
| **Architectural Exploration Tokens** | Hundreds of thousands of Tokens wasted | **Only a few thousand Tokens (-99%+)** |
| **Query Latency** | 3 - 8 seconds | **< 1 millisecond** |
| **Over-Engineering & Code Drift** | Frequent (unwanted abstractions) | **Blocked by Karpathy Rule 2** |
| **Silent Breakage on Delivery** | Common (untested code) | **Blocked by Automated Test Harness** |
| **IDE Vendor Lock-In** | High (fragmented rule formats) | **Zero (Universal AGENTS.md)** |
| **Private Code Leak Risk** | High if using cloud vector search | **Zero (100% Local SQLite)** |

---

## 🌐 Supported AI Environments

| AI Tool | MCP Configuration | Rule & Context Injection |
| :--- | :--- | :--- |
| **TRAE** | `~/Library/Application Support/TRAE SOLO CN/User/mcp.json` | Native `AGENTS.md` context toggle |
| **Antigravity / Gemini** | `~/.gemini/config/mcp_config.json` | Native `AGENTS.md` + `~/.gemini/GEMINI.md` |
| **Cursor** | `~/.cursor/mcp.json` | Native `AGENTS.md` |
| **Claude Code** | `~/.claude.json` | `CLAUDE.md` imports `@AGENTS.md` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | `AGENTS.md` integration |
| **Zed / VS Code** | Reads repo `AGENTS.md` (`setup` writes no MCP file) | Native `AGENTS.md` support |

---

## 🖥️ 3D Knowledge Graph Visualizer

Whenever you want to explore the architecture, dependency topology, and hot spots of your project visually:

```bash
agent-harness ui
```
Or open **`http://localhost:9749`** in your browser. The visualizer runs with the engine; when nothing answers on that port, `ui` prints how to start it and `status` marks it as not running.

---

## 💖 Acknowledgements

`agent-harness` stands on the shoulders of giants. We gratefully acknowledge:
- **[DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)**: For the high-performance C language AST knowledge graph engine and 3D visualizer (please consider starring their repository! ⭐️);
- **Andrej Karpathy**: For articulating the 4 fundamental engineering disciplines for AI-assisted programming;
- **Agentic AI Foundation (Linux Foundation)**: For standardizing the cross-tool `AGENTS.md` specification.

---

## 🤖 The Crucible: Multi-LLM Adversarial Engineering & Verification

`agent-harness` is designed to enforce engineering discipline on AI agents. During its inception and hardening, it embodied its own philosophy through an unprecedented **multi-round adversarial crucible across four of the world's leading frontier AI models**:

* 🏗️ **Primary Architect & Engineer**: **Google Gemini (Antigravity Agent)** designed the high-concurrency streaming parser, cross-platform architecture, and autonomous self-healing test loop;
* 🔬 **Adversarial Code Reviewer**: **Zhipu GLM-5.3 (TRAE)** executed 5 rounds of rigorous white-box auditing, surfacing edge-case bugs in test isolation, monorepo heuristics, and corrupted config recovery;
* 🧠 **Deep Reasoning & Graph Auditor**: **DeepSeek V4 PRO (Max Thinking)** inspected the complete AST graph and independently executed the test harness, confirming all 13 tests of that version passed (100% green);
* ⚖️ **Philosophical & Security Auditor**: **Anthropic Claude Sonnet 5 (Thinking)** performed a full audit of the codebase, 485 lines at the time, validating the determinism of execution exit codes versus prompt instructions and verifying zero-dependency supply-chain safety;
* 👨‍✈️ **Human Orchestrator & Principal**: **[@ArCzyL](https://github.com/ArCzyL)** directed architecture, prioritized trade-offs, and arbitrated the adversarial debate.

---

## 📄 License

Distributed under the **[MIT License](LICENSE)**.

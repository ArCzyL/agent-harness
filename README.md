<div align="center">

# 🛡️ agent-harness

### Universal Anti-Drift Engineering Guardrail & Codebase Memory for AI Coding Agents

**Stop AI Agents from Burning 99% of Your Tokens and Writing Untested Slop.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-brightgreen.svg)](#installation)
[![Compatible With](https://img.shields.io/badge/Compatible%20With-TRAE%20%7C%20Cursor%20%7C%20Claude%20Code%20%7C%20Antigravity%20%7C%20Windsurf%20%7C%20Zed-orange.svg)](#supported-ai-tools)

[中文文档 (Chinese)](README_CN.md) • [Features](#features) • [Quick Start](#quick-start) • [How It Works](#how-it-works) • [Comparison](#comparison)

</div>

---

## ⚡ The Problem: Why Coding Agents Fail

Every developer pairing with AI coding agents (Cursor, TRAE, Claude Code, Antigravity, Windsurf) faces the exact same two fatal bottlenecks:

1. **Context Amnesia & Token Burn**: The agent has zero cross-session memory. Every new window begins by blindly running full-text `grep` across hundreds of files, consuming **400,000+ tokens (~$1.50–$6.00)** just to understand basic architecture.
2. **Cognitive Drift & Untested AI Slop**: Without strict behavioral guardrails, agents make confident wrong assumptions, overcomplicate scripts with 5 layers of premature abstractions, silently reformat working code into 600-line unreviewable diffs, and say *"I'm done!"* without running a single automated test.

**`agent-harness` solves both problems permanently in a single, tool-agnostic package.**

---

## 🚀 Key Features

* 🧠 **Persistent Codebase Knowledge Graph**: Powered by a high-performance, single-binary C engine (`codebase-memory-mcp`). Indexes ASTs, call graphs, routes, and type hierarchies into a local SQLite database. **Sub-millisecond queries, reducing structural exploration tokens by 99.2%**.
* 🥋 **Karpathy's 4 Golden Behavioral Rules**:
  * **Think Before Writing**: Explicitly state assumptions; never silently pick an arbitrary interpretation when requirements are ambiguous.
  * **Simplicity First**: Write the minimum code necessary. No speculative features, no premature factory abstractions.
  * **Surgical Edits**: Touch only what the task requires. Never "clean up" working neighboring files; keep Git Diffs minimal and auditable.
  * **Goal-Driven Execution**: Convert every task into verifiable criteria. Write tests first, verify in terminal before delivery.
* 🔒 **Physical Test Harness (The Execution Loop)**: Auto-detects your project's technology stack (Go, Rust, TypeScript, Python, etc.) and binds terminal test/lint commands. Forces the agent into an autonomous self-healing loop:  
  $$\text{Code} \longrightarrow \text{Run Test} \longrightarrow \text{Auto-Fix Errors} \longrightarrow \text{All Green} \longrightarrow \text{Deliver}$$
* 🌐 **100% IDE & Client Agnostic**: Automatically configures and syncs across **TRAE, Cursor, Claude Code, Antigravity, Windsurf, Zed, and VS Code**. Single source of truth via universal `AGENTS.md`.
* 🛡️ **Zero-Cloud Leakage**: 100% local execution. Automatically configures global and project-level `.gitignore` to prevent any local database or graph artifacts from polluting private GitHub repos.

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
1. Downloads and activates the ultra-fast `codebase-memory-mcp` daemon.
2. Scans your machine for installed AI editors (TRAE, Cursor, Claude Code, Antigravity, Windsurf) and configures their global MCP settings.
3. Configures global Git protection (`~/.gitignore_global`) to safeguard private repos.
4. Installs the `agent-harness` CLI into `~/.local/bin/`.

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
1. **Zero Overwrite Safety**: If you already have hand-crafted rules in `AGENTS.md`, it **never** overwrites them.
2. **AST Architectural Scan**: Parses languages, modules, and entry points into the local knowledge graph.
3. **Tailor-Made `AGENTS.md`**: Generates a project-specific specification with your stack's exact test harness and Karpathy rules.
4. **Universal Symlink Sync**: Creates compatibility pointers (`CLAUDE.md`, `GEMINI.md`, `.cursorrules`) linking to `AGENTS.md`.

---

## 📊 Comparison

| Metric / Feature | Traditional Agent (Raw Grep) | With `agent-harness` |
| :--- | :---: | :---: |
| **5 Architectural Queries** | ~412,000 Tokens | **~3,400 Tokens (-99.2%)** |
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
| **Cursor** | `~/.cursor/mcp.json` | `.cursorrules` / `.cursor/rules/` symlink |
| **Claude Code** | `~/.claude.json` | `CLAUDE.md` symlink |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | `AGENTS.md` integration |
| **Zed / OpenCode** | Standard JSON configuration | Native `AGENTS.md` support |

---

## 🖥️ 3D Knowledge Graph Visualizer

Whenever you want to explore the architecture, dependency topology, and hot spots of your project visually:

```bash
agent-harness ui
```
Or open **`http://localhost:9749`** in your browser.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

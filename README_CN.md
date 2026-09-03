<div align="center">

# 🛡️ agent-harness

### AI 智能体跨工具防漂移工程框架与代码知识图谱围栏

**杜绝 AI 每次对话盲目烧掉 99% 的 Token，终结写出未测试垃圾代码与过度设计的恶习。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-brightgreen.svg)](#-极速安装30-秒搞定)
[![Compatible With](https://img.shields.io/badge/Compatible%20With-TRAE%20%7C%20Cursor%20%7C%20Claude%20Code%20%7C%20Antigravity%20%7C%20Windsurf%20%7C%20Zed-orange.svg)](#-多工具生态全兼容)

[English Documentation](README.md) • [核心特性](#-核心特性) • [极速安装](#-极速安装30-秒搞定) • [工作原理](#-快速开始针对任何新老项目) • [效益对比](#-实测效益对比) • [开源致谢](#-致谢与开源生态-acknowledgements)

</div>

---

## ⚡ 痛点背景：为什么 AI 编程经常让人抓狂？

每一个使用 AI 辅助编程（Cursor、TRAE、Claude Code、Antigravity、Windsurf 等）的开发者，都深陷在两大死穴之中：

1. **会话失忆与 Token 巨额消耗**：AI 编程助手跨会话没有任何持久记忆。每次新开窗口，它都要盲目地全局 `grep` 搜索几百个源文件，光是“搞清楚项目架构”这一步就要白白烧掉 **几十万个 Token**。
2. **认知漂移与未经测试的 AI 垃圾代码（AI Slop）**：缺乏刚性工程纪律时，AI 经常会犯四种毛病：
   - 需求稍有模糊就擅自猜测，自作主张写出 200 行方向彻底错误的废代码；
   - 让写个简单脚本，它给你搞出 5 层抽象类和一套带工厂模式的插件系统（过度设计）；
   - 修复 3 行小 Bug，顺手把旁边 500 行正常运行的代码全部重新格式化，Git Diff 彻底失控；
   - 改完代码看都不看，自信满满地回复“我已经修好了”，实际上终端一跑满屏报错。

**`agent-harness` 用一套独立于具体 IDE、完全轻量绿色的工程方案，从根源上一劳永逸地解决这两大难题。**

---

## 🚀 核心特性

* 🧠 **本地持久化知识图谱（Token 消耗降低 99% 以上）**：
  底层代码知识图谱能力基于开源项目 **[DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)**（致敬原作者与开源社区）。采用纯 C 语言编写的高性能单二进制守护引擎，将代码 AST、调用链、接口路由与类型系统持久化存入本地 SQLite，**查询延迟低于 1 毫秒，将结构性探索的 Token 消耗暴降 99% 以上**。
* 🥋 **Karpathy 防翻车四大行为准则（行为围栏）**：
  * **先想再写 (Think Before Writing)**：把假设说出口；需求有歧义必须先确认，严禁擅自猜测闷头写代码。
  * **简单优先 (Keep It Simple)**：写解决问题所需的最少代码；坚决拒绝过度设计和无用抽象模式。
  * **手术式修改 (Surgical Edits)**：只改任务要求触碰的代码；严禁顺手修改隔壁正常运行的无关文件，保持 Git Diff 极小可审计。
  * **目标驱动执行 (Goal-Driven Execution)**：将每个任务变成可量化的测试指标；必须在终端实际跑通测试才准交差。
* 🔒 **物理测试闭环（Test Harness Loop）**：
  自动嗅探项目技术栈（Go, Rust, TypeScript/Node, Python 等，含 Monorepo 多栈支持），自动绑定终端编译与测试命令。强制 AI 进入自动化自愈闭环：  
  $$\text{编写/修改代码} \longrightarrow \text{运行测试命令} \longrightarrow \text{根据报错自行修复} \longrightarrow \text{全部绿灯通过} \longrightarrow \text{交付开发者}$$
* 🌐 **100% 跨开发工具（IDE-Agnostic）**：
  一套配置，全网通用。自动适配 **TRAE、Cursor、Claude Code、Antigravity、Windsurf、Zed、VS Code**。以 `AGENTS.md` 为唯一事实源，并自动创建 `CLAUDE.md`、`GEMINI.md`、`.cursorrules` 等符号链接兼容各家工具生态。
* 🛡️ **私有仓库零泄露保护**：
  100% 本地运算，不上传任何私有代码。自动配置全局与项目级 `.gitignore`，确保本地图谱数据库绝不会误推到 GitHub 私密仓库。

---

## 📦 极速安装（30 秒搞定）

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/ArCzyL/agent-harness/main/install.sh | bash
```

### Windows (PowerShell)
在 PowerShell 中运行（管理员或普通终端均可）：
```powershell
irm https://raw.githubusercontent.com/ArCzyL/agent-harness/main/install.ps1 | iex
```

### 安装脚本会自动完成：
1. 自动下载并启动高性能的 `codebase-memory-mcp` 本地守护进程；
2. 扫描本机已安装的 AI 工具（TRAE、Cursor、Claude Code、Antigravity、Windsurf 等）并自动注入全局 MCP 配置（损坏配置自动生成 `.bak` 备份）；
3. 配置全局 Git 防污染规则（`~/.gitignore_global`）；
4. 将 `agent-harness` CLI 注册到 `~/.local/bin/`。

---

## 🛠️ 快速开始：针对任何新老项目

当你进入已有项目或从零开始一个新点子时：

```bash
cd /path/to/your/project
agent-harness init .
```

### 或者直接在 AI 聊天窗口里说一句话：
在 **TRAE**、**Cursor**、**Claude Code** 或 **Antigravity** 中打开该项目，对 AI 说：
> **“为当前项目建图并初始化开发规范”**

### 智能体闭环流程：
1. **防误覆盖保护**：若项目根目录下已有你精心编写的 `AGENTS.md`，**绝对跳过生成**，保护既有手写规则与业务红线；
2. **AST 架构自省**：自动解析项目主要语言比例、模块目录与 main 入口点并存入知识图谱（带目录扫描 Fallback）；
3. **定制化生成 `AGENTS.md`**：自动根据技术栈填入专属的测试命令（Harness）与 Karpathy 四大纪律；
4. **跨工具软链接同步**：自动生成 `CLAUDE.md -> AGENTS.md` 等符号链接，确保无论用哪款工具打开都 100% 生效。

---

## 📊 实测效益对比

| 指标 / 场景 | 传统纯 Prompt / Grep 模式 | 使用 `agent-harness` 之后 |
| :--- | :---: | :---: |
| **多次结构性探索 Token** | 数十万 Tokens 频繁浪费 | **仅数千 Tokens (降低 99% 以上)** |
| **架构查询延迟** | 数秒至十几秒 | **< 1 毫秒** |
| **代码过度设计与架构漂移** | 频繁（随意添加复杂设计模式） | **被 Karpathy 准则 2 严格拦截** |
| **交付未测试的暗坑 Bug** | 家常便饭（空口凭感觉说修好了） | **被自动化测试 Harness 物理围栏锁死** |
| **多 IDE 规则割裂与重复维护** | 严重（各个编辑器规则格式互不通用） | **统一以 AGENTS.md 为准，全自动软链兼容** |
| **私密代码外泄风险** | 存在（若依赖外部第三方云检索平台） | **绝对零泄露（100% 本地 SQLite 图谱）** |

---

## 🌐 多工具生态全兼容

| AI 编程工具 | MCP 自动配置路径 | 规则与上下文识别 |
| :--- | :--- | :--- |
| **TRAE** | `~/Library/Application Support/TRAE SOLO CN/User/mcp.json` | 原生识别 `AGENTS.md` |
| **Antigravity / Gemini** | `~/.gemini/config/mcp_config.json` | 原生识别 `AGENTS.md` 与全局 `GEMINI.md` |
| **Cursor** | `~/.cursor/mcp.json` | 自动软链接 `.cursorrules` / `.cursor/rules/` |
| **Claude Code** | `~/.claude.json` | 自动软链接 `CLAUDE.md` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | 自动读取 `AGENTS.md` |
| **Zed / VS Code** | 标准配置路径 | 原生识别 `AGENTS.md` |

---

## 🖥️ 3D 本地知识图谱可视化看板

当你想要直观审视整个代码库的依赖拓扑、调用热点与模块架构时：

```bash
agent-harness ui
```
或者在浏览器中直接打开：**`http://localhost:9749`**。

---

## 💖 致谢与开源生态 (Acknowledgements)

`agent-harness` 站在巨人的肩膀上构建，衷心致敬以下优秀的开源项目与理念倡导者：
- **[DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)**：提供极致性能的纯 C 语言 AST 知识图谱引擎与 3D 拓扑可视化支持（欢迎前往原仓库为作者点 Star ⭐️ 支持！）；
- **Andrej Karpathy**：为 AI 辅助编程提出了深刻的四项防翻车工程常识；
- **Agentic AI Foundation (Linux Foundation)**：推动行业跨工具通用的 `AGENTS.md` 规范。

---

## 🤖 诞生纪事：四大前沿模型红蓝对抗审计 (Multi-LLM Adversarial Engineering)

本项目是一套给 AI 智能体立规矩的工程护栏，而在它的开发与打磨过程中，也开创性地践行了这一套自我指涉的纪律，经历了一场**全球四大前沿大模型的多轮红蓝对抗式审查与自愈**：

* 🏗️ **核心架构与系统实装 (Primary Architect & Engineer)**：**Google Gemini (Antigravity Agent)** 负责高并发流式解析设计、跨平台实现与多轮测试自愈重构；
* 🔬 **白盒审计与对抗挑刺 (Adversarial Code Reviewer)**：**智谱 GLM-5.3 (TRAE)** 进行了 5 轮尖锐的代码审计，逼出并修复了包括单测隔离、Monorepo 嗅探与坏配置保护等深层隐患；
* 🧠 **深度逻辑推理与图谱验证 (Deep Reasoning & Graph Auditor)**：**DeepSeek V4 PRO (Max Thinking)** 全量通读 AST 知识图谱并实跑单测套件，验证了 13/13 项测试 100% 绿灯与架构自洽性；
* ⚖️ **形式化语义与安全辩论 (Philosophical & Security Auditor)**：**Anthropic Claude 3.7 Sonnet (Thinking)** 深度通读 485 行完整源码，对“物理围栏机制”与“退出码信号确定性”进行了极高密度的学术级论证，验证了纯标准库实现的安全与透明；
* 👨‍✈️ **人类总指挥与最终裁决者 (Human Orchestrator & Principal)**：**[@ArCzyL](https://github.com/ArCzyL)** 担任系统架构把控与多模型博弈仲裁。

---

## 📄 开源许可证

本项目基于 **[MIT License](LICENSE)** 开源。

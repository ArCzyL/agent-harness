# agent-harness AI 智能体开发规范与项目指令 (AGENTS.md)

欢迎来到 **agent-harness** 项目！本项目由独立全栈开发者维护。AI 智能体在进行开发与修改时，必须将本文件视为**最高工程铁律**。

> **【AI 开发纪律 · 动手前必读】**
> 在编写或修改任何代码之前，必须通读本规范。模型每次会话都从零开始，本文件是跨会话唯一可靠的记忆与代码质量围栏。**需求以开发者确认的为准；每次交付都附带实际运行通过的测试。**

***

## 1. 核心技术栈与架构基线

- **项目名称**：`agent-harness`

- **主要技术栈 / 语言**：<!-- agent-harness:auto:languages -->Python<!-- /agent-harness:auto:languages -->

- **核心入口点 (Entry Points)**：
<!-- agent-harness:auto:entries -->
- `bin/agent-harness`
<!-- /agent-harness:auto:entries -->

- **CLI 子命令**：`init` · `check` · `sync` · `setup` · `status` · `ui`

***

## 2. Karpathy 防翻车四大行为准则（The 4 Golden Rules）

### 准则 1：【先想再写 (Think Before Writing)】

- **把假设说出口**：需求存在两种或以上的理解时，**先向开发者列出各种理解并确认，再动手写代码**；

- 开发者的方案有更简单或更健壮的替代实现时，主动提出并说明理由，由开发者决定采用哪一种；

- 对需求理解清晰、能说出验收标准之后，再开始写代码。

### 准则 2：【简单优先 (Keep It Simple & Minimal)】

- **写解决问题所需的最少代码**；

- 只实现本次需求用到的功能（Speculative Features 一律留到真正需要时再写）；只用一次的逻辑直接写在调用处；只处理真实可能出现的输入与场景；

- **判断标准**：写完后用资深工程师的眼光复查，能删的删，能简化的简化。

### 准则 3：【手术式修改 (Surgical Edits)】

- **只动任务要求碰的代码**；

- 与任务无关的代码和文件保持原样（包括格式）；发现值得改进之处，在回复里告诉开发者，由开发者决定是否另开任务；

- 严格遵循项目中已有的编码风格与缩进规范，让 Git Diff 只包含完成任务所需的最小改动，便于逐行审查。

### 准则 4：【目标驱动与自检验收 (Goal-Driven Execution)】

- 将每个开发/修复任务转化为**客观可验证的目标**：

  - “修复 Bug” $\to$ 先构造一个能稳定复现该 Bug 的最小测试，修改代码，直到测试由红变绿；

  - “添加功能” $\to$ 必须配套对应的测试用例与调用校验。

- 宣告完成时，附上刚刚在终端实际运行的测试命令及其通过结果。

***

## 3. 测试框架（Test Harness）与执行闭环

> **物理围栏机制**：智能体改动代码后，必须调用终端命令自我闭环：
> `编写/修改代码` $\to$ `运行检查命令` $\to$ `根据报错自愈修复` $\to$ `重新运行测试` $\to$ `全部绿灯后交付`。

### 本项目测试与校验命令：

- **自动化单元测试验证**：`python3 -m unittest discover -s tests -v`

- **代码语法编译检查**：`python3 -m py_compile bin/agent-harness`

- **文档与代码对齐检查**：`python3 bin/agent-harness check`

- **自动执行**：以上三条命令写在 `.githooks/pre-commit`（改动时两处同步）。Cursor（`.cursor/hooks.json`）和 Antigravity（`.agents/hooks.json`）每轮回复结束时，都会通过 `.githooks/agent-stop.py` 自动运行它，失败则把报错发回给智能体继续修复（最多 3 轮）；`git commit` 前也会运行（clone 后执行一次 `git config core.hooksPath .githooks` 启用）。

### 文档与代码对齐（防下一会话漂移）

- 下一会话会把 `AGENTS.md` 与 README / `docs/` 当作事实源：改代码时同步改文档，事实源才可信。
- **必须同步文档**：对外行为、CLI/API、入口点、技术栈、测试命令、架构分层。
- **纯内部实现的改动**（上述事实均未变化）：文档保持原样。
- 交付前运行 `python3 bin/agent-harness check`。带 `<!-- agent-harness:auto:* -->` 标记的字段可用 `python3 bin/agent-harness sync` 刷新。**sync 只刷新带标记的字段，第 5 节业务红线始终由开发者维护。** 本仓库的测试命令为手写、未加 harness 标记，由开发者手动维护（含 `py_compile bin/agent-harness`）。
- **只写正确做法**：写规则、文档、注释或会话总结时，每条约束都写成「做什么、怎么做」的肯定句，只写正确做法本身。
- **长期要求写进本文件**：开发者在对话中提出、以后所有会话都要遵守的要求，当轮用肯定句写进本文件第 5 节，并在回复中说明新增了哪一条。

**闭环铁律**：

1. 测试或编译报错时，读取具体报错栈并自行修复；全部通过后才宣告任务完成；
2. 同一个问题连续修复 3 次仍未解决（如底层依赖或设计阻塞）时，**停下来向开发者汇报具体卡点和已尝试的方案**，等待决策。
3. 若改动改变了对外行为、入口点、技术栈或测试命令，必须同步更新 AGENTS.md（及 README / docs 对应描述），并运行 `python3 bin/agent-harness check` 直至通过。

***

## 4. 代码知识图谱检索纪律 (Codebase Memory)

- 探索系统架构、函数定义、依赖链路或接口路由时，**若当前会话可用 `codebase-memory-mcp` 工具，优先使用它**，先精准定位，再只读取所需的代码：

    - `get_architecture`: 快速获取系统整体拓扑、热点与分层；

    - `search_graph`: 精准查找函数、类、结构体、接口定义；

    - `trace_path`: 追踪上下游完整调用链，评估修改带来的“爆炸半径”；

    - `get_code_snippet`: 精确读取目标源码，让上下文只装必要内容。

- **若工具不可用**（未安装或未配置 MCP），直接改用常规的文件搜索与读取，照常推进任务。

***

## 5. 业务专属红线与约束

- **零依赖 + Python 3.9**：`bin/agent-harness` 只用 Python 标准库与 Python 3.9 语法（分支用 `if/elif`，类型注解用 `typing.Optional` / `typing.Union`），确保能在 macOS 自带的 Python 3.9 上运行。

- **保留用户内容**：`init` 只在 `AGENTS.md` 不存在时创建它；`sync` 只改 `<!-- agent-harness:auto:* -->` 标记内的内容；`setup` 改写 IDE 配置时，原文件解析失败先生成 `.bak` 备份。

- **测试隔离**：单元测试用 stub 替换 `run_cbm_cli` 和需要的外部命令（如 `git`），所有读写都在临时目录内完成。

- **三平台**：改安装或路径逻辑时，同时考虑 macOS / Linux / Windows（`install.sh`、`install.ps1`、`bin/*.cmd`）。


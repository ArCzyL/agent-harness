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

- **CLI 子命令**：`init` · `check` · `sync` · `verify` · `guard` · `graph` · `setup` · `status` · `ui`

***

## 2. Karpathy 防翻车四大行为准则（The 4 Golden Rules）

### 准则 1：【先想再写 (Think Before Writing)】

- **把假设说出口**：需求存在两种或以上的理解时，**先向开发者列出各种理解并确认，再动手写代码**；

- 开发者的方案有更简单或更健壮的替代实现时，主动提出并说明理由，由开发者决定采用哪一种；

- **提问附上推荐的答案**：每个问题后面写上你推荐的答案和一句理由，问法让开发者回一句「好」就等于采纳；能从代码、配置和终端查到的事实自己查，只把需要开发者拍板的决定拿去问；

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

 - “修复 Bug” $\to$ 先构造一个能稳定复现该 Bug 的最小测试，亲眼看到它失败后再分析原因、修改代码，直到测试由红变绿；

 - “添加功能” $\to$ 必须配套对应的测试用例与调用校验。

- **测试要能抓到错误**：通过对外接口验证行为；期望值写成手写的具体数值或需求里给出的例子，让代码算错时测试真的失败。

- **调试输出带标记**：临时加的调试输出都带同一个唯一标记（例如 `[DEBUG-a4f2]`），交付前按这个标记搜索并全部删除。

- 宣告完成时，附上刚刚在终端实际运行的测试命令及其通过结果。

***

## 3. 测试框架（Test Harness）与执行闭环

> **物理围栏机制**：智能体改动代码后，必须调用终端命令自我闭环：
> `编写/修改代码` $\to$ `运行检查命令` $\to$ `根据报错自愈修复` $\to$ `重新运行测试` $\to$ `全部绿灯后交付`。

### 本项目测试与校验命令：

- **自动化单元测试验证**：`python3 -m unittest discover -s tests -v`

- **代码语法编译检查**：`python3 -m py_compile bin/agent-harness`

- **文档与代码对齐检查**：`python3 bin/agent-harness check`

- **自动执行**：以上三条命令写在 `.githooks/pre-commit` 和 `.github/workflows/test.yml`（改动时三处同步；CI 在 Ubuntu / Windows / macOS 上用 Python 3.9 运行它们）。Cursor（`.cursor/hooks.json`）和 Antigravity（`.agents/hooks.json`）每轮回复结束时运行本仓库的 `python3 bin/agent-harness verify --hook`：文件自上次检查后有变化时，按顺序执行上面三条命令；任一条失败（例如技术栈、入口点、测试命令不一致，或实现文件已改而引用该路径的说明没有一起改），或 270 秒内没有跑完，钩子都把终端输出发回给智能体继续修改（最多 3 轮）；这一轮有新提交时，钩子还会重建本项目的知识图谱。Cursor 执行含 `git` 的命令前、以及调用 `index_repository` 前，还会运行本仓库的 `python3 bin/agent-harness guard`：会丢掉改动的 git 命令先弹框等开发者确认；建图没带文件夹名时补上文件夹名。`git commit` 前也会运行（clone 后执行一次 `git config core.hooksPath .githooks` 启用）。

### 文档与代码对齐（防下一会话漂移）

- 下一会话会把 `AGENTS.md` 与 README / `docs/` 当作事实源：改代码时同步改文档，事实源才可信。
- **必须同步文档**：对外行为、CLI/API、入口点、技术栈、测试命令、架构分层，以及逻辑与实现方法。代码里的做法变了，描述该做法的段落在同一次改动里改成现在的做法。
- 交付前运行 `python3 bin/agent-harness check`。检查核对技术栈、入口点和测试命令。实现文件有改动时，正文里写了这些路径的说明文档也在同一次改动里被修改，检查才通过。带 `<!-- agent-harness:auto:* -->` 标记的字段可用 `python3 bin/agent-harness sync` 刷新。**sync 只刷新带标记的字段，第 5 节业务红线始终由开发者维护。** 本仓库的测试命令为手写、未加 harness 标记，由开发者手动维护（含 `py_compile bin/agent-harness`）。
- **只写正确做法**：写规则、文档、注释或会话总结时，每条约束都写成「做什么、怎么做」的肯定句，只写正确做法本身。
- **长期要求写进本文件**：开发者在对话中提出、以后所有会话都要遵守的要求，当轮用肯定句写进本文件第 5 节，并在回复中说明新增了哪一条。
- 只有测试文件改动（测试目录里的文件，以及 `*_test.go`、`*.test.ts`、`*.spec.ts`、`test_*.py` 这类测试文件）、且说明文档没有写这些测试路径时，说明文档保持原样。

**闭环铁律**：

1. 测试或编译报错时，读取具体报错栈并自行修复；全部通过后才宣告任务完成；
2. 同一个问题连续修复 3 次仍未解决（如底层依赖或设计阻塞）时，**停下来向开发者汇报具体卡点和已尝试的方案**，等待决策。
3. 改动了对外行为、入口点、技术栈、测试命令、逻辑或实现方法时，同步更新 AGENTS.md 及 README / docs 里的对应描述，并运行 `python3 bin/agent-harness check` 直至通过。

***

## 4. 代码知识图谱检索纪律 (Codebase Memory)

- 探索系统架构、函数定义、依赖链路或接口路由时，**若当前会话可用 `codebase-memory-mcp` 工具，优先使用它**，先精准定位，再只读取所需的代码：

    - `get_architecture`: 快速获取系统整体拓扑、热点与分层；

    - `search_graph`: 精准查找函数、类、结构体、接口定义；

    - `trace_path`: 追踪上下游完整调用链，评估修改带来的“爆炸半径”；

    - `get_code_snippet`: 精确读取目标源码，让上下文只装必要内容。

- **若工具不可用**（未安装或未配置 MCP），直接改用常规的文件搜索与读取，照常推进任务。

- **刷新图谱**：开发者说「刷新图谱」时，运行 `agent-harness graph`。有新提交的那轮回复结束时，钩子会自动重建图谱。建图时把文件夹名作为项目名传给引擎，统计页显示 `Odzke` 这样的目录名；同一路径下旧的路径编码名称会被删掉。直接调用 MCP `index_repository` 时，本机用户级钩子也会补上文件夹名（没有 `AGENTS.md` 的项目同样生效）。

***

## 5. 业务专属红线与约束

- **使用者与优先级**：本项目只供开发者本人使用。开发者是中文用户、编程新手，代码全部由 AI 编写；AI 开发工具直接安装在 macOS 和 Windows 上。改进按开发者真实项目里会碰到的问题排优先级；向开发者汇报时用中文和平实的说法。

- **说明文档**：README 只维护中文版 `README.md`。开发者要亲自做的操作（安装、升级、给项目装规范、改测试命令、打开图谱）写在 README 开头「常用操作」一节，每项给出可以直接发给 AI 的一句话；这些操作有变化时，在同一次改动里更新这一节。

- **零依赖 + Python 3.9**：`bin/agent-harness` 只用 Python 标准库与 Python 3.9 语法（分支用 `if/elif`，类型注解用 `typing.Optional` / `typing.Union`），确保能在 macOS 自带的 Python 3.9 上运行。文件第 2 行保留 `# -*- coding: utf-8 -*-`：Windows 上的 Python 3.9 直接运行脚本时，靠这一行才能读入较长的中文行。

- **保留用户内容**：`init` 在 `AGENTS.md` 不存在时创建它；文件已存在时保留原文，只在末尾追加缺失的规范段落和 `<!-- agent-harness:auto:* -->` 标记，已经写全的文件保持不动；已有「测试与校验命令」段的文件沿用这一段作为命令清单。`sync` 只改标记内的内容；`init` 把 stop hook 合并进 `.cursor/hooks.json`、`.claude/settings.json`、`.agents/hooks.json`，把 `agent-harness guard` 合并进 `.cursor/hooks.json` 和 `.claude/settings.json`，保留原有条目且每个 matcher 只添加一次；`init` 与 `setup` 改写 IDE 配置时先写临时文件再整体替换，原文件解析失败先生成 `.bak` 备份。`setup` 还把 `agent-harness guard` 合并进 `~/.cursor/hooks.json` 和 `~/.claude/settings.json`，没有 `AGENTS.md` 的项目直接调用 MCP 建图时也用文件夹名。已有 `core.excludesfile` 时，把图谱忽略规则追加进该文件并保留原路径；还没有该配置时，才写入 `~/.gitignore_global` 并设为 excludes 文件。

- **逻辑与说明同一改动**：改了逻辑或实现方法时，同一次改动里更新描述该行为的说明（README、`docs/`、`AGENTS.md` 的对应段落）。`agent-harness check` 在实现文件已改、且引用该路径的说明文档未出现在本次改动里时失败；智能体补上对应段落后再交付。

- **测试隔离**：单元测试用 stub 替换 `run_cbm_cli` 和需要的外部命令（如 `git`），所有读写都在临时目录内完成。

- **已否决方案**：开发者否决的方案，连同理由和日期写进 `docs/decisions/rejected.md`。提出新方案前先读这份记录；记录里已有的方案，等开发者重新提起时再讨论。

- **三平台**：改安装或路径逻辑时，同时考虑 macOS / Linux / Windows（`install.sh`、`install.ps1`、`bin/*.cmd`）。


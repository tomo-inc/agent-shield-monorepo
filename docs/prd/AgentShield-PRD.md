**AgentShield PRD**

**QA Agent Month MVP Plan**

+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Version** : v5.1 (Review Optimized Version)                                                                                                                                                             |
|                                                                                                                                                                                                           |
| **Date** : 2026-03-27                                                                                                                                                                                     |
|                                                                                                                                                                                                           |
| **Product definition** : Multi-project QA access control + basic Black box capability platform                                                                                                            |
|                                                                                                                                                                                                           |
| **Core strategy** : First week basic access control full project access (compile/Lint/unit test/coverage) → stack API tests and advanced capabilities week by week → deliver sustainable MVP in one month |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Core idea**

  -----------------------------------------------------------------------
  Plain Text\
  Week 1 ──── 基础门禁版（先跑通，再优雅）\
  │ D1: CLI骨架 + BuildChecker + TestChecker（先跑通）\
  │ D2: Lint + TypeCheck + Preset + 覆盖率 + 核心单测\
  │ D3: 批量运行 + 报告 + Pydantic校验（通知 P1）\
  │ D4-5: 全量适配 + 验证 + 发布\
  │ Smoke 环境信息收集（为 Week 2 做准备）\
  │ \[Day 5 下午\] buffer 半天\
  ▼\
  Week 2 ──── 黑盒 Smoke 试点版 + 通知正式上线\
  │ Smoke 从零搭建（测试用例自动生成-接口自动化自动生成-运行）\
  │ 通知正式启用 + CI nightly + HTML 报告\
  │ go Preset + tomo-qa init + pre-flight + 重试\
  │ \[Day 10 下午\] buffer 半天\
  ▼\
  Week 3 ──── Smoke 扩面 + 回归守护 + OpenAPI 解析\
  │ Smoke 推广更多项目 + OpenAPI spec 自动解析\
  │ baseline 存储 + pass→fail 检测\
  │ \[Day 15 下午\] buffer 半天\
  ▼\
  Week 4 ──── MVP 收口（铁律：零新功能）\
  │ Bug 修复 + CI 稳定化 + 文档 + Demo\
  │ 连续 3 天 green + Demo\
  │ \[Day 20 下午\] buffer 半天

  -----------------------------------------------------------------------

**The success of the first week is not defined as \"how many test types were done\", but as \"how many projects were accessed + how many inspections were uniformly hosted\".**

**1. Definition of MVP of the month**

**Product positioning**

**\"Multi-project QA access control + basic Black box capability platform\"** - not \"complete Black box white box return platform in a month\", but a real usable and sustainable quality infrastructure.

**The core content that MVP must achieve**

  ------ -------------------------------------------------------------------------------------------------------------------------- ----------------------------------------
  \#     Capacity                                                                                                                   Introduction time

  1      Multi-project unified configuration access (Preset automatic detection + YAML deep merge + Pydantic Schema verification)   Week 1（Preset D2, Pydantic D3）

  2      Inferno-monorepo + java-maven two core Presets (covering 90% of projects)                                                  Week 1 D2

  3      Go Preset Supplement                                                                                                       Week 2

  4      Build/lint/typecheck/unit test/coverage basic access control                                                               Week 1 (build D1, rest D2)

  5      Coverage threshold detection (display layer + access layer + automatic base line mode + floor_pct bottom line)             Week 1 D2

  6      Unified batch execution (ThreadPoolExecutor concurrency + timeout control + \--strict/\--dry-run)                          Week 1 D3

  7      Unified Reporting (Markdown → HTML)                                                                                        Week 1 D3 → Week 2

  8      Unified Notifications (Slack/Feishu)                                                                                       Week 1 P1 → Week 2 officially launched

  9      Basic API Smoke Test for 2-5 items (handwritten YAML endpoint + pre-flight + retry)                                        Week 2

  10     OpenAPI spec automatically parses endpoints                                                                                Week 3

  11     Nightly CI Execution                                                                                                       Week 2

  12     Tomo-qa init interactive initialization                                                                                    Week 2

  13     Basic regression recognition (pass → fail detection)                                                                       Week 3

  14     Tomo-qa\'s own core module unit test                                                                                       Week 1 D2 starts
  ------ -------------------------------------------------------------------------------------------------------------------------- ----------------------------------------

**Things MVP doesn\'t do**

Web Dashboard UI (HTML report + CLI instead)

Independent Backend Service

SAST white-box testing/LLM automatically generates unit test code (Month 2 +)

UI automation testing

External release/open source

General Strategy DSL Expression Engine

**AgentShield SDK** (shield.log/wrap/policy engine → decoupled to Month 2 standalone project)

**Dedicated test template** (Finance/Security → Dependent API test stable, deferred to Month 2)

**Parameter Boundary Test/Certification Test Template** (Depends on Smoke to run stably, deferred to Month 2)

**Week 1 (Day 1-5) - Basic Access Control Version**

**Target**

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Let 10 + projects be connected to QA Agent first. First, unify the hosting of whether it can compile, pass static checks, pass unit tests, and whether the coverage meets the standard. Check the results uniformly and notify failures uniformly.**

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Week 1 Range**

  ---------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Capacity                           Explanation

  **Compile/Build Detection**        Whether the project can be successfully built/compiled/typechecked

  **Syntax/Lint Detection**          Static check, format check

  **Type check**                     Execute the existing typecheck command of the project

  **Unit test execution**            Can you run the existing unit test?

  **Coverage acquisition**           What is the current coverage, is it below the threshold, parse the coverage tool output

  **Coverage threshold detection**   Display layer + access control layer (see detailed design below) threshold judgment + gap display

  **Harmonized reporting**           All project results are summarized into one report

  **Unified Notification (P0)**      Detection failure pushed to group (Feishu Webhook)

  **Coverage automatic base line**   The first run automatically collects the current coverage as baseline, access control = max (baseline - 5%, floor_pct) eliminates the need to manually set thresholds item by item
  ---------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Week 1 deferred content**

The following capabilities are explicitly **not included in the first week commitment** :

  -------------------------------------------- ---------------------------------------------------------------------------------------------------------------- -----------------------
  Suspended content                            Reason                                                                                                           When to do

  Smoking pilot                                Week 1 focuses on full access to basic access control, Smoke dependency environment ready + HTTPX engine built   Week 2

  go Preset                                    Only 1 project (sentinel), priority lower than inferno-monorepo + java-maven                                     Week 2

  API smoke test (batch)                       Depends on interface assets + environment + token, project differences are large                                 Week 2-3

  Parameter boundary test                      Rely on Smoke for stable operation                                                                               Month 2

  Authentication test                          Dependency auth scheme adaptation                                                                                Month 2

  Regression baseline                          Need to accumulate data first                                                                                    Week 3

  LLM generation test                          High complexity                                                                                                  Month 2+

  White box analysis                           High complexity                                                                                                  Month 2+

  Financial dedicated test                     Need API testing foundation stability                                                                            Month 2

  AgentShield SDK                              Unrelated to the core value of QA access control, decoupled and independent                                      Month 2

  Strategy Engine (url_blocklist/rate_limit)   Belongs to the AgentShield product line                                                                          Month 2
  -------------------------------------------- ---------------------------------------------------------------------------------------------------------------- -----------------------

**Coverage detection design: display layer + access control layer**

**Key principle: Don\'t get stuck at 100% right away, otherwise 10 + projects are likely to be all red, and the landing experience will be very poor.**

Split into two layers.

**Display layer (always displayed, not blocked)**

The report clearly shows:

Current row coverage/function coverage/branch coverage

How far is it from 100%?

Top 10 documents with the lowest coverage

Which dimension is the weakest (lines/functions/branches)?

  -----------------------------------------------------------------------
  Plain Text\
  覆盖率详情：\
  行覆盖率: 72.3% ████████░░ （距 100% 差 27.7%）\
  函数覆盖率: 65.0% ███████░░░ （距 100% 差 35.0%）\
  分支覆盖率: 58.2% ██████░░░░ （距 100% 差 41.8%）\
  \
  覆盖率最低的文件（TOP 5）:\
  src/services/transfer.ts --- 行 45.2% \| 函数 40.0%\
  src/utils/crypto.ts --- 行 52.1% \| 函数 50.0%\
  src/handlers/webhook.ts --- 行 58.0% \| 函数 55.0%

  -----------------------------------------------------------------------

**Access control layer (blocking judgment, configurable)**

Support project-level threshold configuration, **default to set a feasible threshold according to the current situation of the project** , instead of 100% unified card:

  -----------------------------------------------------------------------
  YAML\
  thresholds:

  -----------------------------------------------------------------------

*#Access threshold - below this value marks FAIL*

coverage_line_min_pct: 60 *#Set according to the current situation of the project, and gradually increase it later*

coverage_func_min_pct: 50 *#Function coverage can be slightly lower*

coverage_branch_min_pct: 40 *#Branch coverage is usually lowest*

*#Target value - Display gaps in the report without blocking*

coverage_target_pct: 100 *#\"Only XX% away from 100%\"*

lint_max_errors: 0

typecheck_max_errors: 0

  -----------------------------------------------------------------------------------
  Plain Text\
  \
  \*\*后续可以逐步拉升阈值\*\*（比如每两周提高 5-10%），形成持续改进的压力。\
  \
  \#### 自动基线模式（v4.0 新增，v5.0 增强）\
  \
  手动为 10+ 项目逐个设定阈值成本高且容易拍脑袋。支持 \*\*auto-baseline\*\* 模式：\
  \
  \`\`\`yaml\
  thresholds:

  -----------------------------------------------------------------------------------

Mode: auto *#auto \| manual (default auto)*

coverage_tolerance_pct: 5 *#access control = first acquisition coverage - tolerance*

coverage_floor_pct: 0 *#v5.0 added: access bottom line (to prevent access from becoming negative when the coverage rate is very low)*

coverage_target_pct: 100 *#The display layer goal remains unchanged*

  -----------------------------------------------------------------------------------------------------------------
  Plain Text\
  \
  \*\*工作方式\*\*：\
  1. 首次 \`tomo-qa check\` 时自动采集当前覆盖率，写入 \`.qa-agent/baselines/\<project\>\_coverage.json\`\
  2. 门禁阈值 = \*\*max(baseline - tolerance, floor_pct)\*\*（例：当前 72%，tolerance 5%，floor 0%，门禁 = 67%）\
  3. 只防退步，不强求提升------团队接受度高\
  4. 后续可切换到 \`mode: manual\` 手动拉升阈值，或缩小 tolerance 逐步收紧\
  \
  \*\*v5.0 增强\*\*：\
  - \*\*floor_pct 底线保护\*\*：防止覆盖率为 0% 时门禁变为 -5%（永远不 FAIL）\
  - \*\*baseline 合理性校验\*\*：首次采集时校验覆盖率数据非异常值（非 NaN、非负数）\
  - \*\*\`\--dry-run\` 模式\*\*：试运行时不写入 baseline，避免探索性运行污染基线数据\
  - \*\*baseline 写入解耦\*\*：从 CoverageChecker 移至 Orchestrator 后处理阶段，Checker 只读不写\
  \
  \*\*好处\*\*：10+ 项目零配置即可接入门禁，大幅降低 Week 1 的适配成本。\
  \
  \### 项目配置文件\
  \
  \`\`\`yaml

  -----------------------------------------------------------------------------------------------------------------

***Projects/agent-alpha.yaml - inferno-monorepo minimalist configuration (Preset coverage, only 3 core fields required)***

project:

name: agent-alpha

repo_path: ../agent-alpha

Preset: inferno-monorepo *#Automatically detect backend Ruff/pytest + frontend ESLint/tsc*

thresholds:

Mode: auto *#Set the base line automatically for the first acquisition*

coverage_tolerance_pct: 5 *#access control = baseline - 5%*

coverage_floor_pct: 0 *#Bottom line protection (default 0, can be upgraded by project)*

timeouts:

Build: 300 *#seconds, default 300*

Test: 600 *#Java items can be set to 1200*

smoke_env:

env_status: ready *\# ready / pending / blocked*

base_url: \"https://api-staging.example.com\"

auth_token_source: \"env:AGENT_API_TOKEN\"

  -----------------------------------------------------------------------
  Plain Text\
  \
  \`\`\`yaml

  -----------------------------------------------------------------------

***Projects/wallet-service.yaml - java-maven Preset (automatically detect pom.xml)***

project:

name: wallet-service

repo_path: ../wallet-service

Preset: java-maven *#Automatically use mvn compile/mvn test/JaCoCo*

Tier: 1 *#Core Project*

*#Commands do not need to be written, Preset fills automatically*

*#To override a command, write only the differences (deep merge without losing other defaults):*

*\# commands:*

*\# lint: \"mvn checkstyle:check -q\"*

thresholds:

mode: auto

coverage_tolerance_pct: 5

coverage_floor_pct: 0

smoke_env:

env_status: ready

base_url: \"https://api-staging.example.com\"

auth_token_source: \"env:WALLET_API_TOKEN\"

  -----------------------------------------------------------------------
  Plain Text\
  \
  \`\`\`yaml

  -----------------------------------------------------------------------

***Projects/reward-service.yaml - java-maven (environment not ready)***

project:

name: reward-service

repo_path: ../reward-service

preset: java-maven

thresholds:

mode: auto

coverage_tolerance_pct: 5

smoke_env:

env_status: pending *#Environment is not ready, Week 2 is not smoking yet*

base_url: \"\"

auth_token_source: \"\"

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Plain Text\
  \
  \> \*\*v5.0 配置变更\*\*：\
  \> - 新增 \`preset\` 字段（infer-monorepo / java-maven / go / custom），大幅减少配置量\
  \> - 移除 \`language\` 字段（由 Preset 自动识别）\
  \> - 新增 \`coverage_floor_pct\`（底线保护）\
  \> - 配置使用 \*\*Pydantic Schema 校验\*\*：拼写错误（如 \`coverge_tolerance_pct\`）会立即报错，不会被静默忽略\
  \> - YAML 覆盖使用\*\*深合并\*\*：只写差异字段，不会丢失 Preset 默认值\
  \
  \### Day 1-5 逐日计划\
  \
  \> \*\*团队资源\*\*：3 人全职（Person A: 核心框架，Person B: 测试/解析，Person C: 适配/CI）\
  \> \*\*交付优先级\*\*：P0 = 必须交付（缺失则里程碑不达标），P1 = 尽力交付（可顺延至 Week 2 首日补完）\
  \> \*\*节奏原则\*\*：先跑通再优雅------Day 1 砍到骨架先让 1 个项目跑通，Preset D2 补，Pydantic D3 补\
  \
  \#### Day 1：CLI 骨架 + BuildChecker + TestChecker（先跑通）\
  \
  \| 任务 \| 负责 \| 产出 \| 优先级 \|\
  \|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\
  \| 项目脚手架：目录结构、CLI 入口（typer）、YAML 配置加载（\*\*dict 加载，不上 Pydantic\*\*） \| Person A \| \`tomo-qa check\` 命令可执行 \| P0 \|\
  \| 编译检测器：执行 build 命令 → 捕获 exit code + stderr → PASS/FAIL（含 timeout 300s → TIMEOUT） \| Person A \| BuildChecker \| P0 \|\
  \| 单测运行器：执行 test 命令 → 解析通过/失败数 \| Person B \| TestChecker \| P0 \|\
  \| 覆盖率采集器（基础版）：执行 coverage → 解析覆盖率数字 \| Person B \| CoverageChecker（基础） \| P0 \|\
  \| 10+ 项目快速摸底：确认每个项目 build / test / lint / coverage 命令可用性 \| Person C \| 项目命令清单（含哪些命令可用、哪些不存在） \| P0 \|\
  \| 为前 2-3 个项目创建配置 YAML + 验证命令可用 \| Person C \| \`projects/\*.yaml\` \| P0 \|\
  \
  \*\*Day 1 退出标准\*\*：1 个项目 \`tomo-qa check \--project \<name\>\` 能执行 build + test 检测，终端输出 PASS/FAIL。\*\*不要求 Preset 和 Pydantic\*\*。\
  \
  \#### Day 2：Lint + TypeCheck + Preset 系统 + 覆盖率解析 + 核心单测开始\
  \
  \| 任务 \| 负责 \| 产出 \| 优先级 \|\
  \|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\
  \| Lint 检测器：执行 lint → 解析错误/警告数量（优先 JSON 输出，回退正则） \| Person A \| LintChecker \| P0 \|\
  \| 类型检查器：执行 typecheck → 解析错误数 \| Person A \| TypeChecker \| P0 \|\
  \| \*\*Preset 系统\*\*：PresetDetector + PresetRegistry + infer-monorepo preset + java-maven preset \| Person A \| 两种核心 Preset 可工作 \| P0 \|\
  \| 覆盖率解析器：pytest-cov JSON + JaCoCo XML（覆盖 90% 项目） \| Person B \| PytestCovJSONParser + JacocoXMLParser \| P0 \|\
  \| 阈值判定逻辑（门禁层 + 展示层 + \*\*自动基线模式 + floor_pct 底线\*\*） \| Person B \| 统一判定，10+ 项目零配置可用 \| P0 \|\
  \| \*\*核心模块单测开始\*\*：parser / threshold / preset detector 关键路径单测 \| Person B \| tests/ 目录 + 首批单测 \| P0 \|\
  \| 继续创建 4-6 个项目配置 YAML + 验证（含 Java 项目）+ Smoke 环境信息收集 \| Person C \| 更多项目可用 + env_status 标注 \| P0 \|\
  \
  \*\*Day 2 退出标准\*\*：1 个项目跑完全部检测（build + test + coverage + lint + typecheck），终端输出每项 PASS/FAIL + 覆盖率数字 + lint 错误数。infer-monorepo + java-maven 两种 Preset 均可工作。核心模块有首批单测。\
  \
  \#### Day 3：批量运行 + 报告 + Pydantic 校验 + 深合并\
  \
  \| 任务 \| 负责 \| 产出 \| 优先级 \|\
  \|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\
  \| \`tomo-qa check-all\` 批量运行（ThreadPoolExecutor max_workers=4 + 容错 + timeout + \--strict/\--dry-run） \| Person A \| 一条命令跑所有项目 \| P0 \|\
  \| baseline / results 文件\*\*原子写入\*\*（tmp→rename），防止并发写冲突 \| Person A \| 并发安全 \| P0 \|\
  \| Markdown 报告生成器：汇总表 + 项目详情（含覆盖率展示层细节） \| Person B \| 报告文件 \| P0 \|\
  \| 结果输出 JSON 格式 + \*\*Pydantic Schema 校验 + 深合并\*\*替换 Day 1 的 dict 加载 \| Person B \| \`results.json\` + 配置校验 \| P0 \|\
  \| Slack/飞书 Webhook 通知：检测失败时推送汇总 \| Person C \| 通知到达（\*\*P1，默认关闭，W2 正式启用\*\*） \| P1 \|\
  \| 完成剩余项目配置 YAML + 验证 \| Person C \| 10+ 项目全部有配置 \| P1 \|\
  \
  \*\*Day 3 退出标准\*\*：\`tomo-qa check-all\` 可跑通 6+ 项目，输出 Markdown 汇总报告。Pydantic 校验拼写错误有明确报错。\
  \
  \#### Day 4：全量适配 + 双面检测 + 单测补充\
  \
  \| 任务 \| 负责 \| 产出 \| 优先级 \|\
  \|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\
  \| 修复 bug + 各项目检测命令边界情况处理 \| Person A \| 稳定性 \| P0 \|\
  \| CheckerFactory 实现：infer-monorepo 项目后端+前端双面检测器列表 \| Person A \| 双面检测可用 \| P0 \|\
  \| 退出码规范：全 PASS=0，有 FAIL=1，TIMEOUT/配置异常=2（CI-ready） \| Person A \| CI 可用 \| P0 \|\
  \| 覆盖率解析器边界 case（空覆盖率 / NaN / 解析失败）+ \*\*核心单测补充\*\* \| Person B \| 解析器健壮性 + 测试覆盖 \| P0 \|\
  \| 各项目适配调试：确保每个项目 build/test/lint 能正常执行 \| Person C \| 10+ 项目全可跑 \| P0 \|\
  \| 汇总 Smoke 环境就绪情况，标注 \`env_status\`，输出 Week 2 候选列表 \| Person C \| Week 2 Smoke 候选列表 \| P0 \|\
  \
  \*\*Day 4 退出标准\*\*：10+ 项目中至少 80% 可跑通 \`tomo-qa check\`。Smoke 环境信息收集完毕。核心模块单测通过。\
  \
  \#### Day 5：全量验证 + 首版发布（下午为 buffer）\
  \
  \| 任务 \| 负责 \| 产出 \| 优先级 \|\
  \|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\
  \| 全部 10+ 项目端到端验证 \| 全员 \| 全量通过 \| P0 \|\
  \| 汇总报告优化：排序、高亮重点问题 \| Person A \| 汇总报告 \| P0 \|\
  \| README + 接入指南（5 分钟接入新项目，含 Preset 说明） \| Person B \| 文档 \| P0 \|\
  \| \*\*首版内部发布\*\* --- 通知所有项目团队 \| 全员 \| 内部通知 \| P0 \|\
  \| 收集反馈 + 标注已知问题 \| Person C \| KNOWN_ISSUES.md \| P1 \|\
  \| \*\*\[下午\] Buffer\*\*：修复 W1 遗留 bug / 处理反馈 \| 全员 \| 稳定性 \| --- \|\
  \
  \### Week 1 成功标准\
  \
  \*\*按\"接入率 + 统一托管\"定义，不按测试类型数定义：\*\*\
  \
  \| \# \| 标准 \| 目标 \| 优先级 \|\
  \|\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\
  \| 1 \| 10+ 项目中接入基础门禁的比例 \| \*\*≥ 70-80%\*\*（即至少 7-8 个项目可跑通） \| P0 \|\
  \| 2 \| 核心 Preset 可用 \| infer-monorepo + java-maven 两种 Preset 自动检测可工作 \| P0 \|\
  \| 3 \| 每个接入项目至少能跑的检测 \| build + lint + unit test + coverage（typecheck 按项目情况） \| P0 \|\
  \| 4 \| 能统一输出结果 \| \`tomo-qa check-all\` → Markdown 汇总报告 + JSON \| P0 \|\
  \| 5 \| 配置校验 \| Pydantic Schema 校验可用，拼写错误/类型错误有明确报错 \| P0 \|\
  \| 6 \| 核心模块有单测 \| parser / threshold / preset detector 关键路径有单测保护 \| P0 \|\
  \| 7 \| Smoke 环境信息收集 \| 所有项目标注 \`env_status\`，输出 Week 2 Smoke 候选列表 \| P0 \|\
  \| 8 \| 新项目接入成本 \| \< 5 分钟（Preset 项目 \< 1 分钟） \| P0 \|\
  \| 9 \| 通知实现 \| Slack/飞书通知功能已实现（默认关闭，W2 随 CI 正式启用） \| P1 \|\
  \
  \### 报告示例\
  \
  \`\`\`markdown\
  \# QA Agent 检测报告 --- 2026-04-01\
  \
  \## 汇总\
  \
  \| 项目 \| 编译 \| 单测 \| 覆盖率 \| Lint \| 类型检查 \| 总评 \|\
  \|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\-\--\|\-\-\-\-\--\|\
  \| wallet-service \| ✅ \| ✅ \| ⚠️ 72% (门禁60%✅ 目标100%差28%) \| ✅ 0 err \| ✅ 0 err \| ✅ \|\
  \| reward-service \| ✅ \| ✅ \| ✅ 85% \| ❌ 12 err \| ✅ 0 err \| ❌ \|\
  \| agentpay-sdk \| ❌ 编译失败 \| ⏭️ \| ⏭️ \| ⏭️ \| ⏭️ \| ❌ \|\
  \| user-service \| ✅ \| ✅ \| ✅ 91% \| ✅ 0 err \| ✅ 0 err \| ✅ \|\
  \| sentinel \| ✅ \| ⚠️ 2 fail \| ⚠️ 55% (门禁50%✅ 目标100%差45%) \| ✅ 3 warn \| N/A \| ⚠️ \|\
  \| \... \| \... \| \... \| \... \| \... \| \... \| \... \|\
  \
  \*\*接入：10/12 \| 全通过：4 \| 有警告：3 \| 有失败：3 \| 未接入：2\*\*\
  \
  \-\--\
  \
  \## 详情\
  \
  \### wallet-service\
  - \*\*编译\*\*：✅ PASS（12.3s）\
  - \*\*单测\*\*：✅ 42/42 passed\
  - \*\*覆盖率\*\*：⚠️ 门禁通过，但距目标有差距

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Line coverage: 72.3 % ████████░░ （ access control 60% ✅ \| target 100% difference 27.7%)

Function coverage: 65.0 % ███████░░░ （ access 50% ✅ \| target 100% difference 35.0%)

Branch coverage: 58.2 % ██████░░░░ （ access 40% ✅ \| target 100% difference 41.8%)

Documents with the lowest coverage (TOP 5):

Src/services/transfer.ts - line 45.2% \| function 40.0%

Src/utils/crypto.ts - line 52.1% \| function 50.0%

Src/handlers/webhook.ts - line 58.0% \| function 55.0%

Src/middleware/auth.ts - line 61.3% \| function 60.0%

Src/models/transaction.ts - line 63.5% \| function 62.0%

  -----------------------------------------------------------------------
  Plain Text\
  - \*\*Lint\*\*：✅ 0 errors, 8 warnings\
  - \*\*类型检查\*\*：✅ 0 errors\
  \
  \### agentpay-sdk\
  - \*\*编译\*\*：❌ FAIL

  -----------------------------------------------------------------------

error TS2345: Argument of type \'string\' is not assignable to parameter of type \'number\'.

src/payments/transfer.ts:87:15

error TS2304: Cannot find name \'TransferConfig\'.

src/config/index.ts:12:3

(2 compile errors in total)

  -----------------------------------------------------------------------
  Plain Text\
  - \*\*其他检测\*\*：⏭️ 编译未通过，后续检测跳过

  -----------------------------------------------------------------------

**Week 2 (Day 6-10) - Black box Smoke Pilot Edition**

**Target**

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Smoke Test is built from scratch, and API layer automatic detection is established on 2-5 representative projects. At the same time, the basic access control of Week 1 is connected to CI nightly to run, and the report is upgraded to HTML.**

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Week 2 New Capabilities**

  -------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------- -------------
  Capacity                               Explanation                                                                                                                                               Priority

  **Notification officially launched**   The Slack/Feishu notification implemented in W1 is officially launched (the framework has been stabilized, reducing noise alarms).                        P0

  **CI running nightly**                 GitHub Actions Timed run tomo-qa check-all                                                                                                                P0

  **Distribution of the report**         CI artifact archive + Slack/Feishu notification with artifact link (clear distribution path)                                                              P0

  **HTML report**                        Jinja2 template, beautiful and readable, including summary page                                                                                           P0

  **Smoke Test Setup**                   Starting from scratch, covering 2-5 env_status: ready projects ( **only handwritten YAML endpoint descriptions are supported** )                          P0

  **Smoke environment pre-inspection**   Smoke pre-flight check (GET base_url), not ENV_ERROR FAIL                                                                                                 P0

  **Smoke HTTP retry**                   HTTP request failures can be retried up to 2 times (with an interval of 1 second), distinguishing between stable failures and occasional network errors   P0

  **Go Preset Supplement**               Implement go preset (go build/go test/go cover) to cover sentinel                                                                                         P0

  **tomo-qa init**                       Interactive initialization command: Automatically detect Preset + generate configuration YAML (truly achieve \"5-minute access\").                        P0

  **Basic error code check**             Verify error response format except status code                                                                                                           P1

  **Project Level Interface Report**     API test results as a separate section of the report                                                                                                      P1
  -------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------- -------------

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **V5.1 adjustment** : OpenAPI spec automatic parsing moved from W2 to W3 (real project spec quality is uneven, handwritten YAML is more controllable and faster); notification upgraded from W1 P1 to W2 P0 officially enabled; added tomo-qa init command and report distribution method definition.

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Week 2 Division of Labor**

  ---------- ---------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------
  Day        Person A (core framework)                                                                Person B (API Test)                                                                                                          Person C (CI + Report)

  **6**      HTML Report Template (Jinja2): Summary Page + Project Details                            **API Smoke engine from scratch** : htpx + status code assertion + authentication injection + **pre-flight check + retry**   GitHub Actions workflow setup + nightly run + **notification officially launched**

  **7**      CLI extension: tomo-qa test command + **tomo-qa init** (interactive initialization)      Handwritten YAML endpoint description format + parser                                                                        Notification upgrade (including HTML report link/CI artifact link)

  **8**      **Go Preset implementation** (go build/go test/go cover) + sentinel project adaptation   Tier 1 (2-3 pieces) smoke adaptation adjustment                                                                              CI artifact upload + **report distribution path** confirmation

  **9**      Project configuration extension: API test fields (base_url/auth/endpoints_yaml)          More items smoke adaptation (2-5 in total)                                                                                   CI full run verification

  **10**     Bug Fix + Week 1 Access CI Stabilization                                                 More env_status: ready project smoke adaptation                                                                              **\[PM\] Buffer** : CI continuous operation verification + notification acceptance + W2 legacy problem
  ---------- ---------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------

**Week 2 Exit Criteria**

  ------ ---------------------------------------------------------------------------------- -------------------------------------------------------------------------------
  \#     Standard                                                                           Acceptance

  1      10 + project basic access control CI nightly running normally                      GitHub Actions Records

  2      HTML report can be viewed in a browser, including code quality summary             Leaders can understand

  3      2-5 representative project API smoke test can be run (handwritten YAML endpoint)   tomo-qa test \--project \<name\> pass

  4      Go Preset available                                                                Sentinel project can run through detection with go preset

  5      Smoke pre-flight available                                                         Unreachable environmental label ENV_ERROR not FAIL

  6      Notification officially launched + report distribution                             The failure notification contains CI artifact link. Slack/Feishu received it.

  7      Tomo-qa init is available                                                          Interactive build configuration YAML
  ------ ---------------------------------------------------------------------------------- -------------------------------------------------------------------------------

**Week 3 (Day 11-15) - Smoke Expansion + Return Guardian (Focus Edition)**

**Target**

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Smoke test is not just about \"running\", but also about continuous protection. This week\'s focus is on solidifying Smoke and regression testing, without introducing new test types.**

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Week 3 New Capabilities**

  ------------------------------------ ----------------------------------------------------------------------------------------------------------------------- -------------
  Capacity                             Explanation                                                                                                             Priority

  **Smoking promotion**                From 2-5 → Cover as many env_status: ready items as possible                                                            P0

  **OpenAPI spec automatic parsing**   Extract endpoints from spec → automatically generate smoke case (moved in from W2, W2 only handwrites YAML)             P0

  **Baseline storage**                 Save the result of each run as base line JSON.                                                                          P0

  **Pass → Fail Detection**            Compared with the last base line, regression was found, with 4 levels of classification (new/fixed/regressed/stable).   P0

  **Nightly scheduled execution**      Smoke tests are nightly run                                                                                             P0
  ------------------------------------ ----------------------------------------------------------------------------------------------------------------------- -------------

+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Removed (→ Month 2)** : Parameter boundary test template, certification test template, financial special project template, policy engine, SDK wrap (). |
|                                                                                                                                                          |
| **Release about 6-8 person days** for Smoke expansion quality + regression detection stability + buffer.                                                 |
+----------------------------------------------------------------------------------------------------------------------------------------------------------+

**Week 3 Division of Labor**

  ----------------- --------------------------------------------------------------------------------------- -------------------------------------------------------------------------- ----------------------------------------------------------------------------------
  Day               Person A (core framework)                                                               Person B (regression test)                                                 Person C (Expansion + Report)

  **11**            Smoke test fit more items (by env_status priority)                                      Baseline storage + pass → fail diff logic                                  **OpenAPI spec parser** : extract endpoints from spec → auto generate smoke case

  **12**            Continue Smoke adaptation + boundary case handling + OpenAPI project smoke adjustment   Regression decision 4-level classification + base line update strategy     Report added API testing section + regression testing marker

  **13**            Tier 1 Project Smoke End-to-End Depth Verification                                      Regression test notification integration (pass → fail automatic alarm)     Smoke test nightly CI integration

  **14**            All connected to the project end-to-end verification.                                   Regression detection end-to-end validation (making regression scenarios)   CI full operation verification + report improvement

  **15**            Bug fix + stabilization                                                                 Bug fix + stabilization                                                    **\[PM\] Buffer** : CI full validation + W3 legacy problem
  ----------------- --------------------------------------------------------------------------------------- -------------------------------------------------------------------------- ----------------------------------------------------------------------------------

**Week 3 Exit Criteria**

  ----------------------- ---------------------------------------- ----------------------------------------------------
  \#                      Standard                                 Acceptance

  1                       5 + items smoke test can run             tomo-qa test-all

  2                       Regression diff can detect pass → fail   Manufacturing regression scenario verification

  3                       Baseline can be stored and updated       Baseline .json exists

  4                       Smoke tests nightly run                  CI record

  5                       Regression alarm can be notified         Slack/Feishu receive notification when pass → fail
  ----------------------- ---------------------------------------- ----------------------------------------------------

**Week 4 (Day 16-20) - MVP Closing**

**Target**

  ---------------------------------------------------------------------------------------------------------------------
  **Form a truly sustainable MVP. Without adding new functional modules, focus on stabilization, closure, and demo.**

  ---------------------------------------------------------------------------------------------------------------------

**Iron rule: No new functional modules will be added in Week 4.**

**Week 4 tasks**

  --------------------------------- --------------------------------------------------------------------------------------- --------------
  Task type                         Specific content                                                                        Responsible

  **Summary Kanban**                HTML summary report upgrade: multi-project panorama + stable/beta partition             Person A

  **Manual rerun**                  CLI supports rerunning specified items/specified detection items                        Person B

  **CI stabilization**              Tier 1 **3 consecutive days** nightly green                                             Person C

  **Fault-tolerant verification**   Network disconnection/environment unavailable/token expired/timeout, scenario testing   Person C

  **Document**                      Access guide + schema document (no SDK document, SDK decoupled to Month 2)              All staff

  **Demo**                          Scripted demo scene                                                                     All staff

  **Bug fixes**                     W1-W3 legacy problem                                                                    All staff

  **\[Day 20 PM\] Buffer**          Final Acceptance + Closing                                                              All staff
  --------------------------------- --------------------------------------------------------------------------------------- --------------

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **V5.1 Remove** : adapter hook (new feature) + trend chart (new feature) → Month 2. Week 4 declares \"iron law does not add new features\", which contradicts the iron law. Release\~ 2 days for CI stabilization and Demo polishing.

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Demo scene**

  ------------- ---------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  \#            Scene                  Demo

  1             **Panoramic Kanban**   Tomo-qa check-all → 10 + project compile/coverage/lint list, a project coverage is lower than the automatic base line red and display TOP 10 low coverage files

  2             **Smoke automation**   Representative project tomo-qa test \--project \< name \> → API endpoints all pass, report display

  3             **Return to guard**    Make a code change → nightly run detected pass → fail → auto notification → report flagged regression
  ------------- ---------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------

**Week 4 Exit Criteria (= MVP Final Acceptance)**

  ----------------------- ------------------------------------------------------- --------------------------
  \#                      Hard standard                                           Acceptance

  1                       Basic access control for 10 + projects can all be run   Tomo-qa check-all pass

  2                       Tier 1 (3) nightly green for **3 days** in a row        CI record

  3                       HTML summary report readable                            Browser to view

  4                       Failure notification arrives                            Artificial failure

  5                       2-5 items with smoke test                               Can run through

  6                       Regression diff can detect pass → fail                  Manufacturing regression

  7                       Demo can be presented smoothly.                         Internal demo
  ----------------------- ------------------------------------------------------- --------------------------

  ----------------------------------- -----------------------------------------------------------------------------------------------------
  \#                                  Soft standards (reach = excellent)

  1                                   New project access \< 5 minutes ( tomo-qa init + automatic base line, zero threshold configuration)

  2                                   Tier 1 5 consecutive days green (3 days beyond the hard standard)

  3                                   Tomo-qa\'s own core module test coverage rate is ≥ 60%.
  ----------------------------------- -----------------------------------------------------------------------------------------------------

**Overview of Milestones**

  ------------------------------------------------------------------------------
  Plain Text\
  Week 1 Week 2 Week 3 Week 4\
  Day 1─────Day 5 Day 6─────Day 10 Day 11────Day 15 Day 16────Day 20\
  │ │ ½d buf │ │ ½d buf │ │ ½d buf │ │ ½d buf\
  ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼\
  D1:骨架跑通 首版 CI nightly HTML Smoke 扩面 回归 汇总看板 MVP\
  D2:Preset+单测 发布 Smoke(手写YAML) 报告 OpenAPI 解析 Baseline Bug fix 交付\
  D3:批量+报告 ✅ 通知正式启用 回归检测 存储 Demo + 稳定化 ✅\
  D4-5:适配验证 go Preset+init (无专项/SDK) 文档+CI稳定\
  pre-flight+重试 (零新功能)\
  \
  ──── 基础门禁版 ──── ── Smoke 试点版 ── ── 扩面 + 回归 ── ──── 收口 ────\
  先跑通再优雅\
  \
  10+ 项目接入 Smoke 从零搭建 回归守护 连续 3 天 green\
  统一跑 + 统一看 通知正式启用 OpenAPI 自动解析 Demo ready\
  2种核心 Preset tomo-qa init 回归告警通知 文档完善\
  核心单测开始 go Preset + pre-flight Smoke 深度稳定 (无 adapter hook)\
  Smoke 环境信息收集 HTML 报告 + CI nightly

  ------------------------------------------------------------------------------

**Milestone checkpoint**

  --------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Point in time   Report to the leader

  **Day 5**       \"QA basic access control capabilities have been integrated into 10 + projects in the first week. Two kinds of Preset zero configuration automatic detection. Compile /Lint/unit test/coverage - all unified hosting. Pydantic check configuration spelling errors. Core modules have unit test protection. Smoke environment information has been collected.\"

  **Day 10**      \"CI daily automatic running + notification officially launched. Smoke Test built from scratch (handwritten YAML endpoint), 2-5 project APIs automatically detected. Go Preset + tomo-qa init launched. HTML report + CI artifact distribution.\"

  **Day 15**      API Smoke Test covers 5 + projects. Regression detection is online - code changes that cause test regression will be automatically discovered and alerted. Smoke + regression testing has been running stably on both lines.

  **Day 20**      \"One month MVP completed. 10 + project quality real-time monitoring, core project API testing coverage, regression automatic guardianship. System nightly green for 3 consecutive days. New project access 5 minutes (including automatic base line, zero threshold configuration).\"
  --------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**VII. Project stratification**

**Tier 1 selection criteria** (meet all 3):

Highest Business Criticality (Core Revenue/Core Function)

env_status: ready (Smoke environment available)

Cover at least 2 types of Presets (such as 1 inferno-monorepo + 1 java-maven + 1 go).

  ------------ ------------------------------------------------------------ --------------------------------------------------------------------- ------------------------------ ----------------------------- ---------------------------------
  Tier         Scope                                                        Week 1                                                                Week 2                         Week 3                        Week 4

  **Tier 1**   3 core projects (selected according to the above criteria)   4 access control inspections + environmental information collection   \+ smoke test + notification   \+ Regression detection       Three consecutive days of green

  **Tier 2**   3-4 projects                                                 4 access control inspections + environmental information collection   \+ smoke test (as env ready)   \+ regression                 Stabilization

  **Tier 3**   4-5 projects                                                 4 access control inspections + environmental information collection   CI nightly                     Refill smoke (as env ready)   Annotation \[beta\]
  ------------ ------------------------------------------------------------ --------------------------------------------------------------------- ------------------------------ ----------------------------- ---------------------------------

**Eight, technical selection**

  -------------------------- -------------------------------------- ------------------------------------------------------------------------------------------------
  Dimension                  Choose                                 Explanation

  **Language**               Python 3.10+                           Use Python for QA Agent, any language for the tested project

  **CLI**                    typer                                  Quick and self-help

  **Configuration model**    Pydantic ≥2.0                          Schema validation + unknown field detection ( extra = \"forbidden\" ) + value range validation

  **Configuration merge**    Deep merge                             Nested dict recursion merge, users only need to write difference fields

  **Process management**     subprocess                             Execute the build/test/lint commands for each project

  **Concurrent execution**   ThreadPoolExecutor（max_workers=4）    I/O intensive (call process), no need for ProcessPoolExecutor

  **Timeout control**        Subprocess timeout (default 300s)      Timeout flag TIMEOUT status (different from FAIL)

  **File is written to**     Atomic write (tmp → rename)            Prevent CI + manual run concurrent write conflicts

  **Coverage analysis**      Self-writing parser                    Support jest JSON/pytest-cov JSON/JaCoCo XML/lcov/go cover

  **HTTP Client**            httpx（Week 2+）                       API testing, including pre-flight + retry, can evolve AsyncClient later.

  **Report**                 Markdown（W1）→ Jinja2 HTML（W2+）     Progressive upgrade

  **CI**                     GitHub Actions                         Already

  **Notification**           Slack/Feishu Webhook                   Simple and direct

  **Storage**                JSON file (baselines/results/config)   No Ops, SQLite On Demand Month 2 Introduced

  **Data retention**         DataRetentionPolicy                    Automatically clean up expired reports (default 30 days) + disk threshold check
  -------------------------- -------------------------------------- ------------------------------------------------------------------------------------------------

**IX. Directory structure**

  ---------------------------------------------------------------------------------
  Plain Text\
  tomo-qa/\
  ├── cli/\
  │ └── main.py \# CLI 入口（typer，\--strict / \--dry-run 支持）\
  │\
  ├── models/ \# v5.0 新增：Pydantic 配置模型\
  │ ├── config.py \# ProjectConfig / ThresholdsConfig / SmokeEnvConfig\
  │ └── result.py \# CheckResult / ProjectResult\
  │\
  ├── presets/ \# v5.0 新增：Preset 系统\
  │ ├── base.py \# PresetBase + PresetRegistry\
  │ ├── detector.py \# PresetDetector（自动检测项目类型）\
  │ ├── infer_monorepo.py \# infer-monorepo preset（Week 1）\
  │ ├── java_maven.py \# java-maven preset（Week 1）\
  │ └── go.py \# go preset（Week 2）\
  │\
  ├── orchestrator/ \# v5.0 新增：编排层\
  │ ├── orchestrator.py \# 单项目编排（CheckerFactory + 后处理 baseline）\
  │ └── batch.py \# BatchOrchestrator（ThreadPoolExecutor 并发）\
  │\
  ├── checkers/ \# Week 1：代码质量检测器\
  │ ├── base.py \# 检测器基类\
  │ ├── factory.py \# CheckerFactory（按 Preset 动态创建检测器列表）\
  │ ├── build_checker.py \# 编译检测\
  │ ├── test_checker.py \# 单测执行\
  │ ├── coverage_checker.py \# 覆盖率采集 + 阈值判定（只读 baseline）\
  │ ├── lint_checker.py \# Lint 检测（JSON 优先 + 正则回退）\
  │ └── typecheck_checker.py \# 类型检查\
  │\
  ├── parsers/ \# 输出解析\
  │ ├── coverage/ \# jest / pytest-cov / JaCoCo XML / lcov / go cover\
  │ └── lint/ \# eslint / ruff / golint / checkstyle\
  │\
  ├── api_testing/ \# Week 2+：API 测试\
  │ ├── analyzer/ \# spec 解析\
  │ ├── generator/ \# 用例生成（smoke）--- boundary / auth / financial → Month 2\
  │ └── runner/ \# httpx 执行（含 pre-flight + 重试）\
  │\
  ├── tracker/ \# Week 3：回归追踪\
  │ ├── baseline.py \# BaselineWriter（Orchestrator 调用）\
  │ └── diff.py\
  │\
  ├── reporter/\
  │ ├── markdown_reporter.py \# Week 1\
  │ ├── html_reporter.py \# Week 2\
  │ ├── json_reporter.py \# Week 1（机器消费）\
  │ └── templates/ \# Jinja2 HTML 模板\
  │\
  ├── notifier/ \# Week 1：通知\
  │ ├── slack.py\
  │ └── feishu.py\
  │\
  ├── utils/\
  │ ├── deep_merge.py \# 配置深合并\
  │ ├── atomic_write.py \# 原子写入（tmp→rename）\
  │ └── retention.py \# DataRetentionPolicy（过期清理）\
  │\
  ├── tests/ \# v5.1 新增：tomo-qa 自身测试\
  │ ├── test_parsers/ \# parser 单测（coverage / lint）\
  │ ├── test_threshold.py \# 阈值判定逻辑单测\
  │ ├── test_preset_detector.py \# Preset 检测逻辑单测\
  │ └── test_config_validation.py \# Pydantic 校验单测\
  │\
  ├── projects/ \# 项目配置（每个项目一个 YAML，含 preset + smoke_env 字段）\
  ├── .qa-agent/ \# 运行时数据（reports / baselines / audit / logs）\
  ├── .github/workflows/ \# CI 配置\
  ├── requirements.txt \# 含 pydantic\>=2.0.0\
  └── README.md

  ---------------------------------------------------------------------------------

**X. Risk and mitigation**

  ---------- ------------------------------------------------------------- ------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  \#         Risk                                                          Probability        Mitigate

  1          **Some projects are missing the test/lint command**           In                 Day 1 know the real situation; non-existent detection items are marked N/A and do not block other items

  2          **Coverage output formats are diverse**                       High               W1 support pytest-cov JSON + JaCoCo XML (cover 90%), other format markup parse_error later

  3          **Full red coverage causes team resistance**                  Low                **Automatic base line mode** : the first collection automatically sets the threshold (baseline - tolerance, floor_pct fallback), only prevent regression and do not force improvement

  4          **Project dependency installation time**                      In                 Support \--skip-install ; cache node_modules/venv in CI

  5          **Smoke test environment not ready**                          High               **W1 pre-collect environmental information** , mark env_status , W2 pre-flight check automatically identify unreachable

  6          **The leader thinks there are only numbers without action**   Low                The report contains \"TOP 10 documents with the lowest coverage\" + \"lint misclassification\" - pointing to clear actions

  7          **Some projects have complex building environments**          In                 Skip the tag ENV_ERROR first (different from FAIL), W4 patch adapter hook

  8          **20 days without buffer leads to extension**                 High               **Reserve half a day per week buffer** (2 days in total) to absorb unexpected issues and technical debt

  9          **Preset detection mismatch**                                 Low                Sort the detection conditions by priority (inferno-monorepo \> java-maven \> go), inferno-monorepo needs to be detected public_ui/or frontend/directory

  10         **Silent failure due to configuration spelling error**        In                 Pydantic extra = \"forbidden\" check, unknown fields immediately report an error

  11         **HTTP transient error causes Smoke false positive**          In                 W2 Added retry mechanism (up to 2 times, interval 1s), pre-flight distinguishes between ENV_ERROR and FAIL

  12         **Report/base line file cumulative disk footprint**           Low                DataRetentionPolicy automatic cleanup (default retention 30 days, disk \> 90% forced cleanup)

  13         **Java project mvn test timed out**                           High               Some Java project mvn test may run for 20 minutes, blocking the global. timeout_seconds default 300s, timeout flag TIMEOUT

  14         **QA tool itself is not tested**                              In                 Error in parser/threshold/preset logic causes false positives. Core module unit test starts on Day 2

  15         **Baseline/results concurrent write conflict**                In                 Nightly CI + developer manually runs simultaneous writes. Atomic writes (tmp → rename) from Day 3

  16         **HTML report without distribution path**                     Low                Generated a report but the leader can\'t see it. W2 explicitly CI artifact + Slack with link
  ---------- ------------------------------------------------------------- ------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Summary of KPI**

**Week 1 (Basic Access Version)**

  ----------------------------------- -------------------------------------------------------------------------------------
  Indicator                           Target

  Proportion of Access Projects       ≥ 70-80% (at least 7-8 out of 10 + projects)

  Preset coverage                     Inferno-monorepo + java-maven two core Presets available

  Uniformly hosted detection types    Build + lint + test + coverage (typecheck depends on the project situation)

  Unified result output               Tomo-qa check-all → Markdown report + JSON

  Notification implementation         Slack/Feishu notification implemented (P1, W2 officially enabled with CI)

  Self-test                           Core modules (parser/threshold/preset) have unit test protection

  Smoke environment ready             All items env_status marked, output Week 2 candidate list

  Access costs                        \< 5 minutes/project (Preset project \< 1 minute)

  Configuration verification          Pydantic Schema verification is available, and spelling errors are clearly reported
  ----------------------------------- -------------------------------------------------------------------------------------

**MVP of the month**

  ----------------------------------- ----------------------------------------------------------------------------------------------
  Indicator                           Target

  Basic access control                10 + projects fully covered

  Preset                              3 types (inferno-monorepo/java-maven/go) covering all known project types

  API Smoke                           2-5 projects can be run through (including pre-flight + retry).

  CI                                  Nightly automatic operation

  Notification                        Failure automatic alarm (including regression alarm)

  Regression                          Pass → fail detectable + automatic notification

  Report                              HTML summary (access control + API + regression testing)

  Tier 1 stability                    3 consecutive days green (hard standard), 5 days green (soft standard)

  Access costs                        \< 5 minutes/new project ( tomo-qa init + automatic base line, zero threshold configuration)

  ENV_ERROR rate                      \< 10% (environmental issues, observability indicators)

  Self test coverage                  Core modules ≥ 60% (soft standard)
  ----------------------------------- ----------------------------------------------------------------------------------------------

**XII. Follow-up planning**

  ----------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Stage                               Core content

  **Month 2**                         AgentShield SDK independent project startup + **adapter hook mechanism** + **trend chart** + parameter boundary test + certification test + financial/security special project template + LLM automatic generation unit test + MCP interface + SQLite persistence + custom Preset mechanism + Smoke AsyncClient evolution

  **Month 3**                         SAST white-box testing + Agent infrastructure + Coverage integration + External output preparation + Observability Dashboard
  ----------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Appendix A: Summary of v4.0 Optimization Changes**

  ----------------- ---------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------ -----------------------------
  \#                Optimization point                       Change description                                                                                                                   Release working hours

  1                 **Week 3 Slimming**                      Remove parameter boundary/authentication/special project template/policy engine/SDK wrap (), focus on Smoke expansion + regression   \~ 6-8 person days

  2                 **AgentShield SDK Decoupling**           Shield.log/wrap/policy engine all moved to Month 2 independent project                                                               \~ 3-4 person days

  3                 **Buffering mechanism**                  Reserve half a day of buffer per week (2 days in total) to absorb unexpected issues                                                  ---

  4                 **Smoke environment front**              Week 1 Day 1 Start collecting testing environment URL/token/ready status, annotate env_status                                        Reduce W2 blocking

  5                 **Coverage automatic base line**         First run automatically collects baseline, access control = baseline - tolerance, zero configuration access                          Reduce W1 adaptation costs

  6                 **Special project template move back**   Finance/Security special project template moved from Week 3 to Month 2                                                               \~ 2 person days

  7                 **Stability standard adjustment**        The continuous green hard standard has been reduced from 5 days to 3 days, with 5 days as the soft standard                          Increase W4 fault tolerance
  ----------------- ---------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------ -----------------------------

**Appendix B: Summary of v5.0 Architecture Alignment Changes**

  ----------------- ----------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------
  \#                Optimization point                              Change description                                                                                                                              Impact

  1                 **Go preset + Smoke pilot to Week 2**           Go has only one project; Smoke relies on the HTTPX engine to build + environment ready, Week 1 focuses on full access to basic access control   Week 1 Focus Enhancement

  2                 **Preset detection conditions are tightened**   Inferno-monorepo needs to check Makefile + pyproject.toml + (public_ui/or frontend/) at the same time to prevent mismatch                       Reduce Preset Misjudgment

  3                 **Coverage base line enhancement**              Change the access control formula to max (baseline - tolerance, floor_pct), and add baseline rationality check                                  Prevent extreme values from causing access control failure

  4                 **\--Dry-run mode**                             Practice run does not write baselines or send notifications, only outputs reports                                                               Safe exploratory operation

  5                 **\--Strict mode**                              WARN also returns exit code 1, suitable for strict access control scenarios                                                                     CI flexible configuration

  6                 **Exit code specification**                     0 = PASS, 1 = FAIL/WARN, 2 = Configuration/System Exception                                                                                     CI can distinguish processing based on exit code

  7                 **Deliverables P0/P1 grading**                  Day 1-5 mark the priority of daily tasks, P0 must be delivered, P1 can be postponed                                                             Clear decision-making to avoid full heap until Day 5

  8                 **Clear team resources**                        Clearly indicate the assumption of 3 full-time employees + role division                                                                        Ensure that the plan is executable

  9                 **Configure Pydantic validation**               Change from dataclass to Pydantic BaseModel, extra = \"forbidden\" to detect spelling errors                                                    Reduce the cost of configuration errors

  10                **Configure deep merge**                        YAML override uses recursion deep merge, users only need to write difference fields                                                             Prevent nested default values from being overwritten

  11                **Concurrency to use ThreadPoolExecutor**       I/O intensive (call subprocess), no serialization overhead of ProcessPoolExecutor                                                               Performance optimization

  12                **Smoke pre-flight + Retry**                    Check environmental reachability before execution (ENV_ERROR vs FAIL), HTTP requests are automatically retried twice                            Reduce false positives

  13                **Data Retention Policy**                       DataRetentionPolicy automatically cleans up expired reports (30 days), disk threshold check                                                     Prevent disk accumulation

  14                **Lint parsing enhancement**                    Prioritize parsing JSON output, remove unsafe count (\"error\") fallback                                                                        Improve analytical accuracy

  15                **CheckerFactory**                              Dynamically create detector list according to Preset, inferor-monorepo supports backend + frontend double-sided detection                       Architecture flexibility

  16                **Baseline write decoupling**                   Move from CoverageChecker to Orchestrator post-processing stage                                                                                 Support \--dry-run + clear responsibilities
  ----------------- ----------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------

**Appendix C: Summary of v5.1 Review Optimization Changes**

  ----------------- -------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------
  \#                Optimization point                     Change description                                                                                                                                                   Source

  1                 **Day 1 Reduce Burden**                Day 1 Cut to CLI skeleton + BuildChecker + TestChecker (no Preset, no Pydantic), Preset → D2, Pydantic → D3                                                          Review Suggestion #1

  2                 **Notification downgraded to W1 P1**   When the framework is unstable, receiving notifications will generate noise alarms. W1 implements it but turns it off by default. W2 is officially enabled with CI   Review Recommendation #2

  3                 **OpenAPI→W3**                         Real project OpenAPI spec quality varies, W2 only supports handwritten YAML endpoints, OpenAPI automatic parsing is moved to W3                                      Review Recommendation #3

  4                 **W4 really closes**                   Adapter hook + trend chart is a new feature, contradicts the \"iron law of not adding new\", moved to M2                                                             Review Recommendation #4

  5                 **Self-test strategy**                 D2 starts writing unit tests for parser/threshold/preset detector core module                                                                                        Review Recommendation #5

  6                 **Timeout control**                    timeout_seconds default 300s + max_workers default 4 + TIMEOUT state (different from FAIL)                                                                           Review Recommendation #6

  7                 **Atomic write**                       Baseline/results files use tmp → rename to prevent concurrent write conflicts                                                                                        Review Recommendation #7

  8                 **Distribution of the report**         W2 clearly defined: CI artifact + Slack/Feishu notification with artifact link                                                                                       Review Recommendation #8

  9                 **tomo-qa init**                       W2 new interactive initialization command: automatically detect Preset + generate configuration YAML                                                                 Review Recommendation #9

  10                **Clear stratification criteria**      Tier 1 Selection Criteria: Business Criticality + env_status: ready + Coverage of Multiple Presets                                                                   Review Recommendation #10
  ----------------- -------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------

**Overall delivery confidence** : from\~ 65% (v3.0) →\~ 85% (v4.0) →\~ 90% (v5.0) → \*\*\~ 92% (v5.1, significant reduction in weekly load + reduced execution risk) \*\*.

*\"In the first week, all projects should be run, viewed, and notified uniformly. In one month, quality should be traceable, guarded, and demonstrated.\"*

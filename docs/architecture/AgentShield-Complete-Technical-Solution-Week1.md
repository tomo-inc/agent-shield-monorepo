**AgentShield Complete Technical Solution Week1**

**I. Technology selection**

![](./docx-media/AgentShield-Complete-Technical-Solution-Week1/media/image1.png)

**点击图片可查看完整电子表格**

**II. Directory structure**

The existing skeleton remains unchanged, add packages/cli :

  -----------------------------------------------------------------------
  Plain Text\
  agentshield-monorepo/\
  ├── apps/\
  │ ├── api/ ← 现有，暂不扩展\
  │ └── web/ ← 现有，暂不扩展\
  ├── packages/\
  │ ├── cli/ ← 新建，Week 1 核心\
  │ │ ├── agentshield/\
  │ │ │ ├── \_\_init\_\_.py\
  │ │ │ ├── cli.py ← typer 入口\
  │ │ │ ├── orchestrator.py ← 调度 + 并发 + 超时\
  │ │ │ ├── analyzer/\
  │ │ │ │ ├── scanner.py ← 读取项目文件\
  │ │ │ │ └── ai_client.py ← 调用 LLM API\
  │ │ │ ├── checkers/\
  │ │ │ │ ├── base.py\
  │ │ │ │ ├── build.py\
  │ │ │ │ ├── lint.py\
  │ │ │ │ ├── typecheck.py\
  │ │ │ │ ├── test.py\
  │ │ │ │ └── coverage.py\
  │ │ │ ├── parsers/\
  │ │ │ │ ├── jacoco_xml.py\
  │ │ │ │ ├── pytest_cov_json.py\
  │ │ │ │ └── istanbul_json.py\
  │ │ │ ├── presets/\
  │ │ │ │ ├── registry.py\
  │ │ │ │ ├── infer_monorepo.py\
  │ │ │ │ └── java_maven.py\
  │ │ │ ├── baseline.py ← 读写基线文件\
  │ │ │ ├── reporter.py ← 生成报告\
  │ │ │ └── notifier.py ← 飞书通知\
  │ │ ├── projects/ ← 各项目配置（按 org 分组）\
  │ │ │ └── tomo-inc/\
  │ │ │ └── wallet-service.yaml\
  └── tomo-inc/\
  │ │ ├── pyproject.toml\
  │ │ └── tests/\
  │ │ ├── test_checkers.py\
  │ │ ├── test_parsers.py\
  │ │ └── test_presets.py\
  │ ├── schemas/\
  │ ├── sdk/\
  │ └── ui/\
  ├── .qa-agent/ ← 运行时产出，gitignore\
  │ ├── baselines/\
  │ │ └── tomo-inc_wallet-service.json\
  │ └── runs/\
  │ └── tomo-inc_wallet-service_2026-03-28.json

  -----------------------------------------------------------------------

**III. [CLI command design](https://qsg07xytt12z.sg.larksuite.com/wiki/XTIkwhdIDiWoDrkKuMQlemT5gMd)**

**IV. Project Configuration Schema**

  -----------------------------------------------------------------------
  YAML\
  \# packages/cli/projects/tomo-inc/wallet-service.yaml\
  \
  project:\
  org: tomo-inc\
  name: wallet-service\
  repo_path: ../wallet-service\
  preset: java-maven \# infer-monorepo / java-maven / go / custom\
  \
  \# 只写与 Preset 不同的部分，其余继承默认值\
  commands:\
  lint: \"mvn checkstyle:check\" \# 可选，覆盖 Preset 默认值\
  \
  thresholds:\
  mode: auto \# auto \| manual\
  coverage_tolerance_pct: 5 \# 门禁 = baseline - 5%\
  coverage_floor_pct: 0 \# 兜底，防止门禁变负数\
  lint_max_errors: 0\
  typecheck_max_errors: 0\
  \
  timeouts:\
  build: 300 \# 秒\
  test: 600\
  \
  notify:\
  feishu_webhook: \$FEISHU_WEBHOOK_URL

  -----------------------------------------------------------------------

**Core component design**

**Analyzer (AI scan, only called when init)**

  -----------------------------------------------------------------------
  Plain Text\
  scanner.py 读取目标项目：\
  ├── 目录树（2层深度）\
  ├── package.json / pom.xml / pyproject.toml / go.mod\
  ├── .github/workflows/\*.yml\
  └── README.md 前 100 行\
  \
  ai_client.py 调用 LLM：\
  输入：上述文件内容\
  输出（Pydantic 约束）：\
  {\
  preset: \"java-maven\",\
  commands: { build, lint, typecheck, test, coverage },\
  coverage_parser: \"jacoco-xml\",\
  confidence: 0.95,\
  notes: \"发现自定义 checkstyle 配置\"\
  }

  -----------------------------------------------------------------------

**Checker Pipeline (runs every check)**

  -----------------------------------------------------------------------
  Plain Text\
  每个 Checker 统一接口：\
  \
  class BaseChecker:\
  def run(self, config) -\> CheckResult:\
  \# 执行命令\
  \# 解析输出\
  \# 返回 PASS / FAIL / TIMEOUT / SKIP\
  \
  CheckResult:\
  checker: str\
  status: Literal\[\"pass\", \"fail\", \"timeout\", \"skip\"\]\
  detail: str\
  duration_sec: float

  -----------------------------------------------------------------------

**Orchestrator (scheduling)**

  -----------------------------------------------------------------------
  Plain Text\
  1. 读取 projects/org/project.yaml\
  2. 深合并 Preset 默认值\
  3. Pydantic 校验配置（拼写错误立即报错）\
  4. ThreadPoolExecutor 并发执行各 Checker\
  5. 超时控制\
  6. 汇总结果 → Reporter → Notifier → 写本地文件

  -----------------------------------------------------------------------

**Baseline (base line management)**

  -----------------------------------------------------------------------
  Plain Text\
  首次运行：\
  采集覆盖率 → 写 .qa-agent/baselines/org_project.json\
  \
  后续运行：\
  读 baseline → 计算门禁阈值 = max(baseline - tolerance, floor)\
  对比当前覆盖率 → PASS / FAIL\
  \
  显式更新（需 \--confirm flag）：\
  agentshield baseline update → 人工确认 → 覆盖写入

  -----------------------------------------------------------------------

**AI Analyzer Interaction Design (init process)**

  -----------------------------------------------------------------------
  Plain Text\
  Step 1 扫描（静默）\
  读文件，不需要确认\
  \
  Step 2 确认结构\
  \"识别到 java-maven 项目，是否正确？\[Y/n\]\"\
  \
  Step 3 确认命令\
  展示推断出的命令，可逐条修改\
  \
  Step 4 采集 baseline\
  \"现在执行 mvn test 采集基线，约需 5 分钟 \[Y/n\]\"\
  \
  Step 5 配置通知\
  \"配置飞书 Webhook？\[1\]配置 \[2\]跳过\"\
  \
  Step 6 写入配置\
  生成 projects/tomo-inc/wallet-service.yaml\
  提交 Git

  -----------------------------------------------------------------------

**VII. OneDay Plan**

  -----------------------------------------------------------------------
  Plain Text\
  Day 1 CLI 骨架 + BuildChecker + TestChecker\
  退出标准：1 个项目跑通 build + test，终端输出 PASS/FAIL\
  \
  LintChecker + TypeChecker + Preset 系统\
  + CoverageChecker + 覆盖率解析器\
  + 核心模块单测开始\
  退出标准：全套检查跑通，infer-monorepo + java-maven 可用\
  \
  Orchestrator 并发 + Pydantic 配置校验\
  + Reporter（Markdown）+ Baseline 读写\
  退出标准：check-all 跑通所有项目\
  \
  AI Analyzer（init 命令）\
  + 飞书通知\
  退出标准：init 全流程跑通，通知推送成功\
  \
  全项目适配验证 + CI 接入\
  + buffer（修 bug）\
  退出标准：10+ 项目全量接入，CI 阻断可用

  -----------------------------------------------------------------------

**Week 1 clearly does not do**

  -----------------------------------------------------------------------
  Plain Text\
  ✗ 云上 Server（文件存储够用）\
  ✗ Dashboard\
  ✗ MCP 接口\
  ✗ Go Preset（Week 2）\
  ✗ Smoke Test（Week 2）\
  ✗ 数据库（Month 2）\
  ✗ 回归 baseline 跨 run 对比（Week 3）

  -----------------------------------------------------------------------

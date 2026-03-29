**AgentShield CLI Command Design Documentation**

**Command overview**

![](./docx-media/AgentShield-CLI-Command-Design-Documentation/media/image1.png)

**点击图片可查看完整电子表格**

**First, agentshield check**

**Parameter**

![](./docx-media/AgentShield-CLI-Command-Design-Documentation/media/image2.png)

**点击图片可查看完整电子表格**

**Usage example**

  -----------------------------------------------------------------------
  Bash\
  \# 本地开发者（在项目根目录下执行）\
  cd ../wallet-service\
  agentshield check\
  \
  \# CI 日常检查\
  agentshield check \--no-init \--strict\
  \
  \# 试运行\
  agentshield check \--dry-run

  -----------------------------------------------------------------------

**Execution process**

  -----------------------------------------------------------------------
  Plain Text\
  cd ../wallet-service\
  agentshield check\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 1 查找配置文件 │\
  │ │\
  │ 在当前目录查找 .agentshield/config.yaml │\
  │ │\
  │ 有配置文件 ──────────────────────→ 跳到 Step 4 │\
  │ 无配置文件 ──→ 有 \--no-init flag? │\
  │ 是 → 报错退出 │\
  │ 否 → 进入 Step 2 │\
  └─────────────────────────────────────────────────────┘\
  │（无配置，自动触发 init）\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 2 AI Analyzer 扫描项目结构 │\
  │ │\
  │ \[1/4\] 读取目录树（3 层深度）\... ✓ │\
  │ \[2/4\] 读取关键配置文件\... ✓ │\
  │ \[3/4\] 读取 CI 工作流\... ✓ │\
  │ \[4/4\] AI 分析中\... ✓ 完成 │\
  │ │\
  │ 识别到以下子模块： │\
  │ apps/api Python · FastAPI · pytest │\
  │ apps/web TypeScript · Next.js · vitest │\
  └─────────────────────────────────────────────────────┘\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 3 人工逐模块确认 │\
  │ │\
  │ ── 子模块 1/2：apps/api ── │\
  │ │\
  │ 确认点 1：识别结果是否正确？ │\
  │ Python · FastAPI · pytest · ruff │\
  │ \[Y/n\] │\
  │ │\
  │ 确认点 2：检查命令是否正确？ │\
  │ build: python -m py_compile │\
  │ lint: ruff check . │\
  │ typecheck: pyright │\
  │ test: pytest │\
  │ coverage: pytest \--cov │\
  │ \[1\] 全部确认 \[2\] 修改某条 \[3\] 手动填写 │\
  │ │\
  │ ── 子模块 2/2：apps/web ── │\
  │ │\
  │ 确认点 1：识别结果是否正确？ │\
  │ TypeScript · Next.js · vitest · eslint │\
  │ \[Y/n\] │\
  │ │\
  │ 确认点 2：检查命令是否正确？ │\
  │ build: pnpm build │\
  │ lint: pnpm lint │\
  │ typecheck: pnpm typecheck │\
  │ test: pnpm test │\
  │ coverage: pnpm test \--coverage │\
  │ \[1\] 全部确认 \[2\] 修改某条 \[3\] 手动填写 │\
  │ │\
  │ ── 全局配置 ── │\
  │ │\
  │ 确认点 3：配置通知渠道 │\
  │ \[1\] 配置飞书 Webhook \[2\] 暂时跳过 │\
  │ │\
  │ → 生成 .agentshield/config.yaml │\
  └─────────────────────────────────────────────────────┘\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 4 加载并校验配置 │\
  │ │\
  │ 读取 .agentshield/config.yaml │\
  │ 各子模块深合并 Preset 默认值 │\
  │ Pydantic Schema 校验 │\
  │ ✓ 配置合法 │\
  │ ✗ 字段拼写错误 → 立即报错，不进入检查 │\
  └─────────────────────────────────────────────────────┘\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 5 各子模块并发执行检查 Pipeline │\
  │ │\
  │ ┌─── apps/api（Python）─────────────────────────┐ │\
  │ │ BuildChecker python -m py_compile PASS │ │\
  │ │ LintChecker ruff check . PASS │ │\
  │ │ TypeChecker pyright PASS │ │\
  │ │ TestChecker pytest PASS │ │\
  │ │ CoverageChecker pytest \--cov PASS │ │\
  │ │ PytestCovJSONParser 解析覆盖率数据 │ │\
  │ └────────────────────────────────────────────────┘ │\
  │ │\
  │ ┌─── apps/web（TypeScript）─────────────────────┐ │\
  │ │ BuildChecker pnpm build PASS │ │\
  │ │ LintChecker pnpm lint PASS │ │\
  │ │ TypeChecker pnpm typecheck PASS │ │\
  │ │ TestChecker pnpm test PASS │ │\
  │ │ CoverageChecker pnpm test \--coverage PASS │ │\
  │ │ IstanbulJSONParser 解析覆盖率数据 │ │\
  │ └────────────────────────────────────────────────┘ │\
  │ │\
  │ 两个子模块并发执行，互不阻塞 │\
  └─────────────────────────────────────────────────────┘\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 6 baseline 处理 │\
  │ │\
  │ 各子模块独立维护自己的 baseline： │\
  │ .agentshield/baselines/apps-api.json │\
  │ .agentshield/baselines/apps-web.json │\
  │ │\
  │ 首次运行：自动写入 baseline │\
  │ 非首次：对比当前值，计算门禁阈值 │\
  │ \--dry-run：不写入，只展示对比 │\
  └─────────────────────────────────────────────────────┘\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ Step 7 汇总报告输出 │\
  │ │\
  │ ══════════════════════════════════════════ │\
  │ AgentShield · agent-shield · 2026-03-28 │\
  │ ══════════════════════════════════════════ │\
  │ │\
  │ ── apps/api（Python）── │\
  │ Build ✓ PASS (3.2s) │\
  │ Lint ✓ PASS (2.1s) │\
  │ TypeCheck ✓ PASS (4.5s) │\
  │ Test ✓ PASS 86 passed / 0 failed │\
  │ Coverage ✓ PASS │\
  │ 行覆盖率 81.2% ████████░░ 门禁 ≥ 76.0% │\
  │ │\
  │ ── apps/web（TypeScript）── │\
  │ Build ✓ PASS (12.3s) │\
  │ Lint ✓ PASS (3.4s) │\
  │ TypeCheck ✓ PASS (5.2s) │\
  │ Test ✓ PASS 43 passed / 0 failed │\
  │ Coverage ✗ FAIL │\
  │ 行覆盖率 58.3% ██████░░░░ 门禁 ≥ 67.0% ← 不达标│\
  │ │\
  │ 总耗时 31.2s │\
  │ 整体结论 ✗ FAIL（apps/web Coverage 不达标） │\
  └─────────────────────────────────────────────────────┘\
  │\
  ├── 推送飞书通知：\"agent-shield ✗ FAIL · apps/web 覆盖率不达标\"\
  │\
  ├── \--strict → exit code 1（CI 阻断）\
  └── 非 strict → exit code 0（仅展示，不阻断）

  -----------------------------------------------------------------------

**AgentShield init \--yes (CI dedicated)**

**Parameter**

![](./docx-media/AgentShield-CLI-Command-Design-Documentation/media/image3.png)

**点击图片可查看完整电子表格**

Premise: The target project\'s dependency environment is ready (dependencies are installed and the runtime environment is configured).

**Usage example**

  -----------------------------------------------------------------------
  Bash\
  \# CI 首次接入（在目标项目根目录执行）\
  agentshield init \--yes

  -----------------------------------------------------------------------

**Execution process**

  -----------------------------------------------------------------------
  Plain Text\
  agentshield init \--yes\
  │\
  ▼\
  AI 扫描所有子模块\
  │\
  ▼\
  直接接受所有识别结果，不等人确认\
  │\
  ▼\
  生成 .agentshield/config.yaml\
  │\
  ▼\
  首次采集 baseline（自动执行所有检查命令）\
  │\
  ▼\
  ✓ 初始化完成，配置已写入\
  → 提交 .agentshield/config.yaml 到 Git

  -----------------------------------------------------------------------

**III. AgentShield baseline update**

**Parameter**

![](./docx-media/AgentShield-CLI-Command-Design-Documentation/media/image4.png)

**点击图片可查看完整电子表格**

**Usage example**

  -----------------------------------------------------------------------
  Bash\
  \# 更新所有子模块 baseline\
  agentshield baseline update\
  \
  \# 只更新某个子模块\
  agentshield baseline update \--module apps/api

  -----------------------------------------------------------------------

**Execution process**

  -----------------------------------------------------------------------
  Plain Text\
  agentshield baseline update\
  │\
  ▼\
  ┌─────────────────────────────────────────────────────┐\
  │ 逐模块展示对比 │\
  │ │\
  │ ── apps/api ── │\
  │ 当前 baseline（2026-03-01） 行 72.3% │\
  │ 最新检查结果（2026-03-28） 行 81.5% ↑ +9.2% │\
  │ 更新后门禁阈值 行 ≥ 76.5% │\
  │ │\
  │ ── apps/web ── │\
  │ 当前 baseline（2026-03-01） 行 65.0% │\
  │ 最新检查结果（2026-03-28） 行 71.2% ↑ +6.2% │\
  │ 更新后门禁阈值 行 ≥ 66.2% │\
  │ │\
  │ ⚠ baseline 提升后，低于新阈值将判定 FAIL │\
  │ 确认更新全部？\[y/N\] │\
  └─────────────────────────────────────────────────────┘\
  │ 确认\
  ▼\
  写入各子模块 baseline 文件\
  ✓ baseline 已更新

  -----------------------------------------------------------------------

**Iv. agentshield report**

**Parameter**

![](./docx-media/AgentShield-CLI-Command-Design-Documentation/media/image5.png)

**点击图片可查看完整电子表格**

**Usage example**

  -----------------------------------------------------------------------
  Bash\
  \# 查看最近一次完整报告\
  agentshield report\
  \
  \# 查看最近 5 次\
  agentshield report \--last 5\
  \
  \# 只看 apps/api 的记录\
  agentshield report \--module apps/api \--last 3

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  Plain Text\
  执行流程\
  agentshield report \--last 3\
  ↓\
  读取 .agentshield/runs/ 目录\
  ↓\
  按时间倒序排列，取最近 3 条\
  ↓\
  终端输出历史趋势表格

  -----------------------------------------------------------------------

**Five CI access examples**

  -----------------------------------------------------------------------
  YAML\
  \# .github/workflows/agentshield.yml\
  \
  name: AgentShield QA Gate\
  \
  on: \[push, pull_request\]\
  \
  jobs:\
  \
  \# 首次接入时手动触发一次，之后不再需要\
  init:\
  if: github.event_name == \'workflow_dispatch\'\
  runs-on: ubuntu-latest\
  steps:\
  - uses: actions/checkout@v4\
  - name: Install AgentShield\
  run: pip install agentshield\
  - name: Init（全自动）\
  run: agentshield init \--yes\
  env:\
  AGENTSHIELD_API_KEY: \${{ secrets.AGENTSHIELD_API_KEY }}\
  - name: Commit config\
  run: \|\
  git add .agentshield/\
  git commit -m \"chore: add agentshield config\"\
  git push\
  \
  \# 每次 push 自动触发\
  check:\
  runs-on: ubuntu-latest\
  steps:\
  - uses: actions/checkout@v4\
  - name: Install AgentShield\
  run: pip install agentshield\
  - name: QA Check\
  run: agentshield check \--no-init \--strict\
  env:\
  FEISHU_WEBHOOK_URL: \${{ secrets.FEISHU_WEBHOOK_URL }}\
  AGENTSHIELD_API_KEY: \${{ secrets.AGENTSHIELD_API_KEY }}

  -----------------------------------------------------------------------

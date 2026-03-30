# AgentShield CLI Command Design Documentation

## Command Overview

| Command | User | Description |
|---|---|---|
| `agentshield check` | Local developer | Auto-init if no config, otherwise run checks directly |
| `agentshield init --yes` | CI first-time setup | Fully automated, no interaction, generates config and commits to Git |
| `agentshield check --no-init --strict` | CI daily | Run checks directly, block on failure |
| `agentshield baseline update` | Local developer | Explicitly raise the baseline |
| `agentshield report` | Local developer | View check history |

---

## I. agentshield check

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `--no-init` | Optional | Disable auto-init. CI must include this flag. |
| `--dry-run` | Optional | Trial run — does not write baseline or send notifications |
| `--strict` | Optional | Exit code 1 if any check fails |

> `--project` and `--org` have been removed. The current working directory is the project root; AgentShield identifies it automatically.

### Usage Examples

```bash
# Local developer (run from project root)
cd ../wallet-service
agentshield check

# CI daily check
agentshield check --no-init --strict

# Trial run
agentshield check --dry-run
```

### Execution Flow

```
cd ../wallet-service
agentshield check
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 1  Locate config file                         │
│                                                     │
│  Look for .agentshield/config.yaml in current dir   │
│                                                     │
│  Config found  ──────────────────────→  Skip to 4  │
│  No config  ──→  --no-init flag present?            │
│                   Yes  →  Error, exit               │
│                   No   →  Proceed to Step 2         │
└─────────────────────────────────────────────────────┘
        │ (no config, auto-trigger init)
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 2  AI Analyzer scans project structure        │
│                                                     │
│  [1/4] Reading directory tree (3 levels)...  ✓      │
│  [2/4] Reading key config files...           ✓      │
│  [3/4] Reading CI workflows...               ✓      │
│  [4/4] AI analysis...                        ✓ done │
│                                                     │
│  Detected sub-modules:                              │
│    apps/api   Python · FastAPI · pytest             │
│    apps/web   TypeScript · Next.js · vitest         │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 3  Confirm each sub-module with user          │
│                                                     │
│  ── Sub-module 1/2: apps/api ──                     │
│                                                     │
│  Confirm 1: Is the detection correct?               │
│    Python · FastAPI · pytest · ruff                 │
│    [Y/n]                                            │
│                                                     │
│  Confirm 2: Are the check commands correct?         │
│    build:    python -m py_compile                   │
│    lint:     ruff check .                           │
│    typecheck: pyright                               │
│    test:     pytest                                 │
│    coverage: pytest --cov                           │
│    [1] Confirm all  [2] Edit one  [3] Enter manually│
│                                                     │
│  ── Sub-module 2/2: apps/web ──                     │
│                                                     │
│  Confirm 1: Is the detection correct?               │
│    TypeScript · Next.js · vitest · eslint           │
│    [Y/n]                                            │
│                                                     │
│  Confirm 2: Are the check commands correct?         │
│    build:    pnpm build                             │
│    lint:     pnpm lint                              │
│    typecheck: pnpm typecheck                        │
│    test:     pnpm test                              │
│    coverage: pnpm test --coverage                   │
│    [1] Confirm all  [2] Edit one  [3] Enter manually│
│                                                     │
│  ── Global config ──                                │
│                                                     │
│  Confirm 3: Configure notification channel          │
│    [1] Set up Feishu Webhook  [2] Skip for now      │
│                                                     │
│  → Generate .agentshield/config.yaml                │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 4  Load and validate config                   │
│                                                     │
│  Read .agentshield/config.yaml                      │
│  Deep-merge Preset defaults for each sub-module     │
│  Pydantic Schema validation                         │
│    ✓ Config is valid                                │
│    ✗ Typo in field name → error, abort checks       │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 5  Run check pipeline for all sub-modules     │
│          concurrently                               │
│                                                     │
│  ┌─── apps/api (Python) ─────────────────────────┐ │
│  │  BuildChecker    python -m py_compile  PASS   │ │
│  │  LintChecker     ruff check .          PASS   │ │
│  │  TypeChecker     pyright               PASS   │ │
│  │  TestChecker     pytest                PASS   │ │
│  │  CoverageChecker pytest --cov          PASS   │ │
│  │    PytestCovJSONParser parses coverage data   │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  ┌─── apps/web (TypeScript) ─────────────────────┐ │
│  │  BuildChecker    pnpm build            PASS   │ │
│  │  LintChecker     pnpm lint             PASS   │ │
│  │  TypeChecker     pnpm typecheck        PASS   │ │
│  │  TestChecker     pnpm test             PASS   │ │
│  │  CoverageChecker pnpm test --coverage  PASS   │ │
│  │    IstanbulJSONParser parses coverage data    │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  Both sub-modules run concurrently, non-blocking    │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 6  Baseline handling                          │
│                                                     │
│  Each sub-module maintains its own baseline:        │
│    .agentshield/baselines/apps-api.json             │
│    .agentshield/baselines/apps-web.json             │
│                                                     │
│  First run:  auto-write baseline                    │
│  Subsequent: compare against baseline for gate      │
│  --dry-run:  show comparison only, do not write     │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 7  Aggregate report output                    │
│                                                     │
│  ══════════════════════════════════════════         │
│  AgentShield · agent-shield · 2026-03-28            │
│  ══════════════════════════════════════════         │
│                                                     │
│  ── apps/api (Python) ──                            │
│  Build      ✓ PASS   (3.2s)                        │
│  Lint       ✓ PASS   (2.1s)                        │
│  TypeCheck  ✓ PASS   (4.5s)                        │
│  Test       ✓ PASS   86 passed / 0 failed           │
│  Coverage   ✓ PASS                                 │
│    Line     81.2%  ████████░░  gate >= 76.0%       │
│                                                     │
│  ── apps/web (TypeScript) ──                        │
│  Build      ✓ PASS   (12.3s)                       │
│  Lint       ✓ PASS   (3.4s)                        │
│  TypeCheck  ✓ PASS   (5.2s)                        │
│  Test       ✓ PASS   43 passed / 0 failed           │
│  Coverage   ✗ FAIL                                 │
│    Line     58.3%  ██████░░░░  gate >= 67.0% ← FAIL│
│                                                     │
│  Total time  31.2s                                  │
│  Result      ✗ FAIL (apps/web coverage below gate)  │
└─────────────────────────────────────────────────────┘
        │
        ├── Send Feishu notification: "agent-shield FAIL · apps/web below coverage gate"
        │
        ├── --strict → exit code 1 (CI blocked)
        └── no --strict → exit code 0 (display only, no block)
```

---

## II. agentshield init --yes (CI dedicated)

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `--yes` | Required | Fully automated, skip all confirmations |

Prerequisite: target project dependency environment must be ready (dependencies installed, runtime configured).

### Usage Example

```bash
# CI first-time onboarding (run from project root)
agentshield init --yes
```

### Execution Flow

```
agentshield init --yes
        │
        ▼
  AI scans all sub-modules
        │
        ▼
  Accept all detected results without waiting for confirmation
        │
        ▼
  Generate .agentshield/config.yaml
        │
        ▼
  Collect baseline (auto-run all check commands)
        │
        ▼
  Initialization complete, config written
  → Commit .agentshield/config.yaml to Git
```

---

## III. agentshield baseline update

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `--module` | Optional | Target a specific sub-module. Default: update all. |

### Usage Examples

```bash
# Update baseline for all sub-modules
agentshield baseline update

# Update a specific sub-module only
agentshield baseline update --module apps/api
```

### Execution Flow

```
agentshield baseline update
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Show per-module comparison                         │
│                                                     │
│  ── apps/api ──                                     │
│  Current baseline (2026-03-01)   line 72.3%         │
│  Latest check result (2026-03-28) line 81.5% +9.2%  │
│  New gate threshold               line >= 76.5%     │
│                                                     │
│  ── apps/web ──                                     │
│  Current baseline (2026-03-01)   line 65.0%         │
│  Latest check result (2026-03-28) line 71.2% +6.2%  │
│  New gate threshold               line >= 66.2%     │
│                                                     │
│  WARNING: raising the baseline means future runs    │
│  below the new threshold will be marked FAIL        │
│  Confirm update all? [y/N]                          │
└─────────────────────────────────────────────────────┘
        │ confirmed
        ▼
  Write baseline files for each sub-module
  Baseline updated successfully
```

---

## IV. agentshield report

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `--last` | Optional | Show last N runs. Default: 1 |
| `--module` | Optional | Show a specific sub-module only |

### Usage Examples

```bash
# View the most recent full report
agentshield report

# View the last 5 runs
agentshield report --last 5

# View only apps/api for the last 3 runs
agentshield report --module apps/api --last 3
```

### Execution Flow

```
agentshield report --last 3
        ↓
Read .agentshield/runs/ directory
        ↓
Sort by time descending, take the most recent 3
        ↓
Print history trend table to terminal
```

---

## V. CI Integration Example

```yaml
# .github/workflows/agentshield.yml

name: AgentShield QA Gate

on: [push, pull_request]

jobs:

  # Run once manually on first onboarding — not needed after that
  init:
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install AgentShield
        run: pip install agentshield
      - name: Init (fully automated)
        run: agentshield init --yes
        env:
          AGENTSHIELD_API_KEY: ${{ secrets.AGENTSHIELD_API_KEY }}
      - name: Commit config
        run: |
          git add .agentshield/
          git commit -m "chore: add agentshield config"
          git push

  # Runs automatically on every push
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install AgentShield
        run: pip install agentshield
      - name: QA Check
        run: agentshield check --no-init --strict
        env:
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
          AGENTSHIELD_API_KEY: ${{ secrets.AGENTSHIELD_API_KEY }}
```

# AgentShield CLI

AgentShield CLI is the installable command-line package for running QA gate checks against a target repository.

## Public Commands

```text
agentshield init --yes
agentshield check --strict
```

`init --yes` scans the current repository and writes `.agentshield/config.yaml`.

`check --strict` loads `.agentshield/config.yaml` and runs the configured checks. If the config file is missing, `check` auto-initializes unless `--no-init` is set.

Advanced maintenance commands:

```text
agentshield baseline update
agentshield report --last 5
```

`baseline update` writes per-module baseline files from the latest run record under `.agentshield/baselines/`.

`report` reads recent run history from `.qa-agent/runs/`.

## Install

The commands below work after `agentshield-cli` has been published to PyPI or to your organization's private package index.

### macOS or Windows with `uv`

```bash
uv tool install agentshield-cli
```

### macOS or Windows with `pipx`

```bash
pipx install agentshield-cli
```

### Local Development Install From This Monorepo

```bash
uv tool install --from ./packages/cli agentshield-cli
```

## Usage

From the target repository root:

```bash
agentshield init --yes
agentshield check --strict
```

If the repository already contains `.agentshield/config.yaml`, initialization is not required:

```bash
agentshield check --strict
```

Dry-run validation:

```bash
agentshield check --dry-run
```

Baseline maintenance:

```bash
agentshield baseline update
agentshield baseline update --module apps/api
```

Run history:

```bash
agentshield report
agentshield report --last 5
agentshield report --module apps/api --last 3
```

## Notes

- The public command surface is intentionally small: `check` and `init`.
- `baseline update` and `report` exist for local maintenance and history review.
- The analyzer exists internally, but external users do not need to learn a separate scan command.
- Generated checks prefer `argv` arrays for better macOS and Windows compatibility.

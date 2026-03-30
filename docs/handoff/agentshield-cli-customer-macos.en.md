# AgentShield CLI Customer Installation Guide for macOS

## Goal

This guide shows how a customer or another internal team can install and use the `agentshield` CLI on macOS without cloning the AgentShield source repository and without depending on any local project path.

## Prerequisites

- macOS
- A package source that publishes `agentshield-cli`
- Python 3.11 or newer
- `uv` or `pipx`
- Access to the target repository that will be checked

## Step 1: Install Python 3.11

If Python 3.11 is not already installed:

```bash
brew install python@3.11
```

Confirm the version:

```bash
python3.11 --version
```

## Step 2: Install A Tool Runner

### Option 1: Install `uv`

```bash
brew install uv
```

### Option 2: Install `pipx`

```bash
brew install pipx
pipx ensurepath
exec zsh
```

## Step 3: Install `agentshield-cli`

The default-package-index commands below work after the AgentShield owner has published `agentshield-cli` to PyPI.

### Install From The Default Package Index

With `uv`:

```bash
uv tool install agentshield-cli
```

With `pipx`:

```bash
pipx install --python python3.11 agentshield-cli
```

### Install From A Private Package Index

If your organization publishes the package to a private Python index, use the package index URL provided by the AgentShield owner.

With `uv`:

```bash
uv tool install --index https://<package-index>/simple agentshield-cli
```

With `pipx`:

```bash
pipx install --python python3.11 --pip-args="--index-url https://<package-index>/simple" agentshield-cli
```

## Step 4: Confirm The Command Is Available

```bash
agentshield --help
```

The help output should show only the public commands:

```text
check
init
```

## Step 5: Use AgentShield In The Target Repository

Change into the target repository root:

```bash
cd /path/to/customer-repo
```

For first-time onboarding:

```bash
agentshield init --yes
```

This creates:

```text
.agentshield/config.yaml
```

Then run the quality gate:

```bash
agentshield check --strict
```

For repeat runs in a repository that already contains `.agentshield/config.yaml`:

```bash
agentshield check --strict
```

## Troubleshooting

If `uv` reports cache-permission issues in a restricted environment, use a writable cache directory:

```bash
export UV_CACHE_DIR=/tmp/agentshield-uv-cache
agentshield check --strict
```

## Notes

- The public workflow is intentionally small: `init` and `check`.
- Customers do not need the AgentShield source repository to install or use the CLI.
- Generated checks prefer `argv` arrays for better macOS and Windows compatibility.

# Publishing to GitHub

This guide is for first-time publishing of the local project to GitHub.

## Goal

Publish the local `agent-shield-monorepo` to your own GitHub repository.

## Prerequisites

You need the following on your machine:

- `git`
- `gh` GitHub CLI
- A logged-in GitHub account

Check your setup:

```bash
git --version
gh --version
gh auth status
```

If not logged in:

```bash
gh auth login
```

## Quick Method: Create and Push with One Command

If you have already run `git init` and made the first commit locally, run this from the project root:

```bash
gh repo create agent-shield-monorepo --private --source=. --remote=origin --push
```

To make the repository public, replace `--private` with `--public`.

This command will:

- Create a repository named `agent-shield-monorepo` on GitHub
- Bind the current local directory as `origin`
- Push the current branch automatically

## Step-by-Step Method

### 1. Navigate to the project directory

```bash
cd /Users/admin/tomo_project/agent-shield-monorepo
```

### 2. Initialize the Git repository

```bash
git init
git branch -M main
```

### 3. Check current files

```bash
git status
```

### 4. Make the first commit

```bash
git add .
git commit -m "chore: scaffold agent-shield-monorepo"
```

### 5. Create the repository on GitHub

Option A — via command line:

```bash
gh repo create agent-shield-monorepo --private
```

Option B — via the web:

- Log in to GitHub
- Click `New repository`
- Set the name to `agent-shield-monorepo`
- Do not check auto-generate README
- Click Create

### 6. Link the remote repository

If created via the web, add the remote manually:

```bash
git remote add origin git@github.com:<your-github-username>/agent-shield-monorepo.git
```

Or via HTTPS:

```bash
git remote add origin https://github.com/<your-github-username>/agent-shield-monorepo.git
```

### 7. Push to GitHub

```bash
git push -u origin main
```

## Daily Commit Workflow

After making changes:

```bash
git status
git add .
git commit -m "feat: describe your change"
git push
```

## Common Issues

### Error: not a git repository

You have not run `git init` in the project root yet.

### Error: remote origin already exists

The remote is already configured. Check it:

```bash
git remote -v
```

To replace it:

```bash
git remote remove origin
git remote add origin git@github.com:<your-github-username>/agent-shield-monorepo.git
```

### Error: permission denied

GitHub authentication is not configured correctly.

Check:

```bash
gh auth status
```

If using SSH, confirm your local SSH key has been added to GitHub.

### A repository with the same name already exists on GitHub

Use a different name, or delete the remote repository and recreate it.

## Recommended First-Publish Command

If the local Git is already initialized:

```bash
gh repo create agent-shield-monorepo --private --source=. --remote=origin --push
```

## For New Team Members

Before touching any business logic, read these files first:

- `README.md`
- `AGENTS.md`
- `docs/handoff/team-handoff.md`
- `docs/requirements/qa-automation-scope.md`

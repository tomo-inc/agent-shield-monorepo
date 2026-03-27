# 本地项目发布到 GitHub 操作指南

这份文档面向第一次把本地项目发到 GitHub 的同学。

## 目标

把本地的 `agent-shield-monorepo` 发布到你自己的 GitHub 仓库。

## 先决条件

本机需要有：

- `git`
- `gh` GitHub CLI
- 已登录 GitHub

你可以先检查：

```bash
git --version
gh --version
gh auth status
```

如果还没登录：

```bash
gh auth login
```

## 快速做法：用 gh 一条命令创建远程仓库并推送

如果本地已经完成 `git init` 和首次 commit，可以直接在项目根目录执行：

```bash
gh repo create agent-shield-monorepo --private --source=. --remote=origin --push
```

如果你想公开仓库，把 `--private` 换成 `--public`。

这条命令会做几件事：

- 在 GitHub 上创建一个名为 `agent-shield-monorepo` 的仓库
- 把当前本地目录绑定成 `origin`
- 自动把当前分支推送上去

## 标准做法：一步一步来

### 1. 进入项目目录

```bash
cd /Users/admin/tomo_project/agent-shield-monorepo
```

### 2. 初始化 Git 仓库

```bash
git init
git branch -M main
```

### 3. 查看当前文件

```bash
git status
```

### 4. 提交第一版代码

```bash
git add .
git commit -m "chore: scaffold agent-shield-monorepo"
```

### 5. 在 GitHub 上创建仓库

有两种方式：

方式 A，用命令行：

```bash
gh repo create agent-shield-monorepo --private
```

方式 B，用网页手动创建：

- 登录 GitHub
- 点击 `New repository`
- 仓库名填写 `agent-shield-monorepo`
- 不要勾选自动生成 README
- 创建完成

### 6. 绑定远程仓库

如果是网页创建，需要手动添加远程：

```bash
git remote add origin git@github.com:<你的GitHub用户名>/agent-shield-monorepo.git
```

如果你不用 SSH，也可以用 HTTPS：

```bash
git remote add origin https://github.com/<你的GitHub用户名>/agent-shield-monorepo.git
```

### 7. 推送到 GitHub

```bash
git push -u origin main
```

## 以后日常提交流程

每次改完代码，建议按这个顺序：

```bash
git status
git add .
git commit -m "feat: 描述本次改动"
git push
```

## 常见问题

### 1. 报错：not a git repository

说明你还没有在项目根目录执行 `git init`。

### 2. 报错：remote origin already exists

说明远程已经加过了，可以先查看：

```bash
git remote -v
```

如果要替换：

```bash
git remote remove origin
git remote add origin git@github.com:<你的GitHub用户名>/agent-shield-monorepo.git
```

### 3. 报错：permission denied

通常是 GitHub 认证没配好。

先检查：

```bash
gh auth status
```

如果你走 SSH，需要确认本机 SSH key 已加到 GitHub。

### 4. GitHub 上已经有同名仓库

那就换一个仓库名，或者删掉远程仓库后重新创建。

## 当前项目建议的首次发布命令

如果本地已经初始化好 Git，最省事的是：

```bash
gh repo create agent-shield-monorepo --private --source=. --remote=origin --push
```

## 给组员的建议

组员拿到仓库后，先不要急着改业务逻辑，先看这些文件：

- `README.md`
- `AGENTS.md`
- `docs/handoff/team-handoff.md`
- `docs/requirements/qa-automation-scope.md`

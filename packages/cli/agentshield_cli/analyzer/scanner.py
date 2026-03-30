from __future__ import annotations

from pathlib import Path

from agentshield_cli.models import FileSample, RepoSnapshot


IGNORED_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".qa-agent",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
}

ROOT_FILES = [
    "AGENTS.md",
    "README.md",
    "package.json",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "openapi/openapi.yaml",
    "docs/requirements/qa-automation-scope.md",
]


def _should_skip(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def build_tree(root: Path, *, max_depth: int = 3, max_entries: int = 200) -> list[str]:
    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        if _should_skip(path):
            continue
        relative = path.relative_to(root)
        depth = len(relative.parts)
        if depth > max_depth:
            continue
        suffix = "/" if path.is_dir() else ""
        entries.append(f"{relative}{suffix}")
        if len(entries) >= max_entries:
            break
    return entries


def _sample_file(path: Path, root: Path, *, max_lines: int = 120, max_chars: int = 6000) -> FileSample | None:
    if not path.exists() or not path.is_file() or _should_skip(path):
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    lines = text.splitlines()[:max_lines]
    snippet = "\n".join(lines)[:max_chars]
    return FileSample(path=str(path.relative_to(root)), content=snippet)


def collect_file_samples(root: Path) -> list[FileSample]:
    samples: list[FileSample] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        sample = _sample_file(path, root)
        if sample is not None:
            samples.append(sample)
            seen.add(resolved)

    for relative in ROOT_FILES:
        add(root / relative)

    for pattern in (
        ".github/workflows/*.yml",
        "apps/*/package.json",
        "apps/*/pyproject.toml",
        "packages/*/package.json",
        "packages/*/pyproject.toml",
    ):
        for path in sorted(root.glob(pattern)):
            add(path)

    return samples


def collect_repo_snapshot(root: Path) -> RepoSnapshot:
    return RepoSnapshot(
        root=str(root),
        tree=build_tree(root),
        files=collect_file_samples(root),
    )

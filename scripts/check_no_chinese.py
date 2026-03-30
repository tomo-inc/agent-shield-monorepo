from __future__ import annotations

import re
import sys
from pathlib import Path

CHINESE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef\u3000-\u303f]")

INCLUDE_SUFFIXES = {".md", ".py", ".ts", ".tsx", ".js", ".yaml", ".yml", ".toml", ".json"}

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".venv",
    "__pycache__",
    ".qa-agent",
    "dist",
    "coverage",
}


def check(root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(root.rglob("*")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix not in INCLUDE_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(lines, start=1):
            if CHINESE.search(line):
                violations.append(f"{path}:{lineno}: {line.strip()[:120]}")
    return violations


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = check(root)
    if violations:
        print("Chinese characters found — all source files must be in English:\n")
        for v in violations:
            print(f"  {v}")
        print(f"\n{len(violations)} violation(s) found.")
        return 1
    print("check:chinese passed — no Chinese characters found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

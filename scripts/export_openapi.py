from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
TARGET = ROOT / "openapi" / "openapi.yaml"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402


def render_openapi() -> str:
    spec = app.openapi()
    return yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render_openapi()

    if args.check:
        current = TARGET.read_text(encoding="utf-8")
        if current != rendered:
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile="openapi/openapi.yaml",
                tofile="generated",
                lineterm="",
            )
            print("\n".join(diff))
            return 1
        return 0

    TARGET.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

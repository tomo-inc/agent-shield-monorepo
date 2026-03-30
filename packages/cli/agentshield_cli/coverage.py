from __future__ import annotations

import json
from pathlib import Path
from typing import Literal


CoverageParser = Literal["coverage.py-json", "istanbul-summary"]
DEFAULT_LINE_COVERAGE_GATE = 100.0


def coverage_gate_message(metric: str, value: float, threshold: float) -> str:
    return f"Coverage for {metric} is {value:.1f}%, below the required {threshold:.1f}%."


def parse_coverage_metrics(parser: CoverageParser, coverage_file: Path) -> dict[str, float]:
    if not coverage_file.exists():
        msg = f"Coverage report `{coverage_file}` was not generated."
        raise FileNotFoundError(msg)

    payload = json.loads(coverage_file.read_text(encoding="utf-8"))
    if parser == "coverage.py-json":
        totals = payload.get("totals", {})
        value = totals.get("percent_covered")
        if not isinstance(value, (int, float)):
            msg = f"Coverage report `{coverage_file}` is missing `totals.percent_covered`."
            raise ValueError(msg)
        return {"line": round(float(value), 1)}

    total = payload.get("total", {})
    lines = total.get("lines", {})
    value = lines.get("pct")
    if not isinstance(value, (int, float)):
        msg = f"Coverage report `{coverage_file}` is missing `total.lines.pct`."
        raise ValueError(msg)
    return {"line": round(float(value), 1)}

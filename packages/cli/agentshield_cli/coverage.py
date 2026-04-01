from __future__ import annotations

import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Literal


CoverageParser = Literal["coverage.py-json", "istanbul-summary", "jacoco-xml", "go-coverprofile"]
DEFAULT_LINE_COVERAGE_GATE = 100.0


def coverage_gate_message(metric: str, value: float, threshold: float) -> str:
    return f"Coverage for {metric} is {value:.1f}%, below the required {threshold:.1f}%."


def _resolve_jacoco_reports(report_root: Path) -> list[Path]:
    if report_root.is_file():
        return [report_root]

    aggregate_reports = sorted(report_root.rglob("target/site/jacoco-aggregate/jacoco.xml"))
    if aggregate_reports:
        return aggregate_reports

    standard_reports = sorted(report_root.rglob("target/site/jacoco/jacoco.xml"))
    if standard_reports:
        return standard_reports

    msg = f"Coverage report `{report_root}` was not generated."
    raise FileNotFoundError(msg)


def _parse_jacoco_line_coverage(report_root: Path) -> dict[str, float]:
    covered_total = 0
    missed_total = 0

    for report_path in _resolve_jacoco_reports(report_root):
        xml_root = ET.fromstring(report_path.read_text(encoding="utf-8"))
        counter = xml_root.find("./counter[@type='LINE']")
        if counter is None:
            msg = f"Coverage report `{report_path}` is missing top-level LINE coverage data."
            raise ValueError(msg)
        covered_total += int(counter.attrib.get("covered", "0"))
        missed_total += int(counter.attrib.get("missed", "0"))

    total_lines = covered_total + missed_total
    if total_lines <= 0:
        msg = f"Coverage report `{report_root}` does not contain any executable lines."
        raise ValueError(msg)
    return {"line": round((covered_total / total_lines) * 100, 1)}


def _parse_go_coverprofile(report_path: Path) -> dict[str, float]:
    total_statements = 0
    covered_statements = 0
    lines = report_path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("mode: "):
        msg = f"Coverage report `{report_path}` is not a valid Go coverprofile."
        raise ValueError(msg)

    for raw_line in lines[1:]:
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 3:
            msg = f"Coverage report `{report_path}` contains an invalid Go coverprofile line."
            raise ValueError(msg)
        try:
            statements = int(fields[1])
            count = int(fields[2])
        except ValueError as exc:
            msg = f"Coverage report `{report_path}` contains a non-numeric Go coverprofile entry."
            raise ValueError(msg) from exc
        total_statements += statements
        if count > 0:
            covered_statements += statements

    if total_statements <= 0:
        msg = f"Coverage report `{report_path}` does not contain any covered statements."
        raise ValueError(msg)
    return {"line": round((covered_statements / total_statements) * 100, 1)}


def parse_coverage_metrics(parser: CoverageParser, coverage_file: Path) -> dict[str, float]:
    if not coverage_file.exists():
        msg = f"Coverage report `{coverage_file}` was not generated."
        raise FileNotFoundError(msg)

    if parser == "jacoco-xml":
        return _parse_jacoco_line_coverage(coverage_file)
    if parser == "go-coverprofile":
        return _parse_go_coverprofile(coverage_file)

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

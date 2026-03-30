from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agentshield_cli.analyzer.ai_client import ScanAPIError, run_scan
from agentshield_cli.analyzer.scanner import collect_repo_snapshot
from agentshield_cli.baseline import (
    ensure_initial_baselines,
    load_baseline,
    summarize_baseline,
    update_baselines,
)
from agentshield_cli.bootstrap import initialize_project
from agentshield_cli.config import load_config
from agentshield_cli.history import group_checks_by_module, list_run_reports, latest_run_report, summarize_checks
from agentshield_cli.llm import resolve_llm_settings
from agentshield_cli.models import ScanReport
from agentshield_cli.runner import run_checks

BASELINE_DIR = Path(".agentshield/baselines")
RUN_DIR = Path(".qa-agent/runs")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentshield")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Run the AgentShield Mode 1 quality gate")
    check_parser.add_argument(
        "--config",
        type=Path,
        default=Path(".agentshield/config.yaml"),
        help="Path to the AgentShield YAML config",
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when any check fails",
    )
    check_parser.add_argument(
        "--no-init",
        action="store_true",
        help="Fail when `.agentshield/config.yaml` is missing instead of auto-initializing",
    )
    check_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run checks without writing baselines or sending notifications",
    )

    init_parser = subparsers.add_parser("init", help="Initialize AgentShield config for the current repo")
    init_parser.add_argument(
        "--config",
        type=Path,
        default=Path(".agentshield/config.yaml"),
        help="Path to the AgentShield YAML config",
    )
    init_parser.add_argument(
        "--yes",
        action="store_true",
        help="Run non-interactively and accept analyzer results",
    )

    baseline_parser = subparsers.add_parser("baseline", help="Manage AgentShield baselines")
    baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_command", required=True)
    baseline_update_parser = baseline_subparsers.add_parser(
        "update",
        help="Update baselines from the latest AgentShield run",
    )
    baseline_update_parser.add_argument(
        "--module",
        help="Update only the specified module path, for example `apps/api`",
    )

    report_parser = subparsers.add_parser("report", help="Show AgentShield run history")
    report_parser.add_argument(
        "--last",
        type=int,
        default=1,
        help="Show the most recent N runs",
    )
    report_parser.add_argument(
        "--module",
        help="Show only one module path, for example `apps/api`",
    )
    return parser


def _print_summary(
    report_path: Path,
    used_config_file: bool,
    webhook_sent: bool,
    *,
    dry_run: bool,
    initialized_baselines: list[Path],
) -> None:
    print("AgentShield Clean · Mode 1")
    print(f"Config source: {'file' if used_config_file else 'built-in default'}")
    print(f"Run record: {report_path}")
    print(f"Dry run: {'yes' if dry_run else 'no'}")
    if initialized_baselines:
        print(f"Baselines initialized: {len(initialized_baselines)}")
    print(f"Webhook: {'sent' if webhook_sent else 'skipped'}")


def _print_report(report) -> None:
    print(f"Project: {report.project_name}")
    for check in report.checks:
        status = check.status.upper()
        print(f"- {check.label:<10} {status:<7} {check.duration_sec:>6.2f}s  {check.command}")
        if check.status != "pass":
            for line in check.stderr_tail[-3:]:
                print(f"  stderr: {line}")
            if not check.stderr_tail:
                for line in check.stdout_tail[-3:]:
                    print(f"  stdout: {line}")
    print(f"Result: {report.status.upper()}")


def _write_scan_report(report: ScanReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = Path("unused")
    timestamp_name = report.project_name.replace("/", "-")
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-")
    target = output_dir / f"{timestamp_name}_{timestamp}.json"
    serialized = report.model_dump(mode="json")
    target.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    latest = output_dir / "latest.json"
    latest.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    return target


def _print_scan_report(report: ScanReport, report_path: Path) -> None:
    print("AgentShield Analyzer · Mode 2")
    print(f"Project: {report.project_name}")
    print(f"Project type: {report.project_type}")
    print(f"Provider: {report.provider or 'unknown'}")
    print(f"Model: {report.llm_model or 'unknown'}")
    print(f"Summary: {report.summary}")
    print(f"Scan report: {report_path}")
    for module in report.modules:
        print(
            f"- {module.path}  {module.language}  "
            f"confidence={module.confidence:.2f}  frameworks={', '.join(module.frameworks)}"
        )
        for check in module.recommended_checks:
            print(f"  check[{check.id}]: {check.run}")
        for note in module.notes[:2]:
            print(f"  note: {note}")
    for note in report.global_notes:
        print(f"Global note: {note}")


def _print_init_summary(config_path: Path, report: ScanReport) -> None:
    print("AgentShield Init")
    print(f"Config written: {config_path}")
    print(f"Project: {report.project_name}")
    print(f"Detected modules: {len(report.modules)}")
    for module in report.modules:
        print(
            f"- {module.path}  {module.language}  "
            f"confidence={module.confidence:.2f}  checks={len(module.recommended_checks)}"
        )


def _confirm(prompt: str) -> bool:
    try:
        value = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return value in {"y", "yes"}


def _print_baseline_preview(module: str, current_summary, latest_summary, current_record) -> None:
    print(f"- {module}")
    if current_record is None or current_summary is None:
        print("  Current baseline: none")
    else:
        print(
            "  Current baseline: "
            f"{current_record.source_created_at}  "
            f"pass={current_summary['passed']}/{current_summary['total']}  "
            f"fail={current_summary['failed']}"
        )
    print(
        "  Latest run: "
        f"pass={latest_summary['passed']}/{latest_summary['total']}  "
        f"fail={latest_summary['failed']}  "
        f"status={str(latest_summary['status']).upper()}"
    )


def _handle_baseline_update(module_filter: str | None) -> int:
    try:
        report, _ = latest_run_report(RUN_DIR)
    except FileNotFoundError as exc:
        print(str(exc))
        return 2

    grouped = group_checks_by_module(report)
    modules = [module_filter] if module_filter else list(grouped.keys())
    if module_filter and module_filter not in grouped:
        print(f"Module `{module_filter}` was not present in the latest run.")
        return 2

    print("AgentShield Baseline Update")
    print(f"Source run: {report.run_file}")
    for module in modules:
        current_record = load_baseline(module, BASELINE_DIR)
        current_summary = summarize_baseline(current_record)
        latest_summary = summarize_checks(grouped[module])
        _print_baseline_preview(module, current_summary, latest_summary, current_record)

    prompt = f"Confirm update {module_filter}" if module_filter else "Confirm update all modules"
    if not _confirm(prompt):
        print("Baseline update cancelled.")
        return 1

    written_paths = update_baselines(
        report,
        baseline_dir=BASELINE_DIR,
        module_filter=module_filter,
    )
    print("Baseline updated successfully")
    for path in written_paths:
        print(f"- {path}")
    return 0


def _print_report_history(last: int, module_filter: str | None) -> int:
    if last <= 0:
        print("`--last` must be greater than 0.")
        return 2

    runs = list_run_reports(RUN_DIR, last)
    if not runs:
        print(f"No AgentShield run history found in `{RUN_DIR}`.")
        return 2

    print("AgentShield Report")
    print(f"Runs shown: {len(runs)}")
    if module_filter:
        print(f"Module filter: {module_filter}")

    for report, path in runs:
        print(f"- {report.created_at}  {report.status.upper()}  {path.name}")
        grouped = group_checks_by_module(report)
        if module_filter:
            checks = grouped.get(module_filter)
            if checks is None:
                print("  module: not present in this run")
                continue
            summary = summarize_checks(checks)
            print(
                "  "
                f"pass={summary['passed']}/{summary['total']}  "
                f"fail={summary['failed']}"
            )
            for check in checks:
                print(f"  {check.id}: {check.status.upper()}")
            continue

        for module, checks in grouped.items():
            summary = summarize_checks(checks)
            print(
                "  "
                f"{module}: {str(summary['status']).upper()}  "
                f"pass={summary['passed']}/{summary['total']}  "
                f"fail={summary['failed']}"
            )
    return 0


def _build_internal_scan_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentshield scan")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".agentshield/config.yaml"),
        help="Path to the AgentShield YAML config",
    )
    return parser


def _run_internal_scan(argv: list[str]) -> int:
    parser = _build_internal_scan_parser()
    args = parser.parse_args(argv)
    config, _, _ = load_config(args.config)
    if not config.llm.enabled:
        print("LLM scan is disabled in `.agentshield/config.yaml`.")
        return 2
    llm_settings = resolve_llm_settings(config.llm)
    if not llm_settings.is_configured:
        print("LLM scan is missing `base_url` or `api_key`.")
        return 2

    snapshot = collect_repo_snapshot(config.project_root)
    try:
        report = run_scan(snapshot, config.llm)
    except ScanAPIError as exc:
        print(str(exc))
        return 1
    report.project_name = config.project.name
    report_path = _write_scan_report(report, Path(".qa-agent/scans"))
    _print_scan_report(report, report_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    effective_argv = list(argv) if argv is not None else sys.argv[1:]
    if effective_argv and effective_argv[0] == "scan":
        return _run_internal_scan(effective_argv[1:])

    parser = build_parser()
    args = parser.parse_args(effective_argv)

    if args.command == "init":
        if not args.yes:
            print("Only non-interactive `agentshield init --yes` is supported right now.")
            return 2
        bootstrap_config, config_path, used_config_file = load_config(args.config)
        llm_settings = resolve_llm_settings(bootstrap_config.llm)
        if not llm_settings.is_configured:
            print("LLM initialization is missing `base_url` or `api_key`.")
            return 2
        try:
            _, report = initialize_project(
                bootstrap_config=bootstrap_config,
                config_path=config_path,
                used_config_file=used_config_file,
            )
        except (ScanAPIError, ValueError) as exc:
            print(str(exc))
            return 1
        _print_init_summary(config_path, report)
        return 0

    if args.command == "baseline":
        if args.baseline_command != "update":
            parser.error("unsupported baseline command")
        return _handle_baseline_update(args.module)

    if args.command == "report":
        return _print_report_history(args.last, args.module)

    if args.command != "check":
        parser.error("unsupported command")

    config_exists = args.config.exists()
    if not config_exists:
        if args.no_init:
            print("AgentShield config not found and `--no-init` was set.")
            return 2
        bootstrap_config, config_path, used_config_file = load_config(args.config)
        llm_settings = resolve_llm_settings(bootstrap_config.llm)
        if not llm_settings.is_configured:
            print("LLM initialization is missing `base_url` or `api_key`.")
            return 2
        print("No AgentShield config found. Running analyzer initialization first...")
        try:
            _, init_report = initialize_project(
                bootstrap_config=bootstrap_config,
                config_path=config_path,
                used_config_file=used_config_file,
            )
        except (ScanAPIError, ValueError) as exc:
            print(str(exc))
            return 1
        _print_init_summary(config_path, init_report)

    config, config_path, used_config_file = load_config(args.config)
    llm_settings = resolve_llm_settings(config.llm)

    if config.llm.enabled and not llm_settings.is_configured:
        print("Warning: LLM scan is enabled in config but `base_url` or API key is missing.")

    report, webhook_sent = run_checks(
        config,
        config_path=config_path,
        used_config_file=used_config_file,
        strict=args.strict,
        run_dir=RUN_DIR,
        send_notifications=not args.dry_run,
    )
    initialized_baselines = [] if args.dry_run else ensure_initial_baselines(report, BASELINE_DIR)
    _print_summary(
        Path(report.run_file),
        used_config_file,
        webhook_sent,
        dry_run=args.dry_run,
        initialized_baselines=initialized_baselines,
    )
    _print_report(report)

    if args.strict and report.status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

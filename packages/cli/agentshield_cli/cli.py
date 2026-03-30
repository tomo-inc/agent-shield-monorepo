from __future__ import annotations

import argparse
import json
import shlex
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from agentshield_cli.analyzer.ai_client import ScanAPIError, run_scan
from agentshield_cli.analyzer.scanner import collect_repo_snapshot
from agentshield_cli.baseline import (
    ensure_initial_baselines,
    load_baseline,
    summarize_baseline,
    update_baselines,
)
from agentshield_cli.bootstrap import (
    build_checks_from_scan_module,
    build_config_payload,
    initialize_project,
    normalize_scan_report,
    reviewable_modules,
    write_generated_config,
)
from agentshield_cli.config import AgentShieldConfig, CheckConfig, load_config
from agentshield_cli.history import group_checks_by_module, list_run_reports, latest_run_report, summarize_checks
from agentshield_cli.llm import resolve_llm_settings
from agentshield_cli.models import CheckResult, ScanModuleSuggestion, ScanReport
from agentshield_cli.panel_sync import sync_baselines, sync_project_register, sync_run
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


def _print_check_start(config_path: Path, config: AgentShieldConfig) -> None:
    modules: list[str] = []
    seen: set[str] = set()
    for check in config.checks:
        module_name = check.module or check.label.split(" - ", 1)[0]
        if module_name in seen:
            continue
        seen.add(module_name)
        modules.append(module_name)
    print("AgentShield Check")
    print(f"Config loaded: {config_path}")
    print(f"Running checks for {len(modules)} module(s)...")


def _print_check_progress(result: CheckResult) -> None:
    check_titles = {
        "build": "Build",
        "lint": "Lint",
        "typecheck": "TypeCheck",
        "test": "Test",
        "coverage": "Coverage",
        "custom": "Custom",
    }
    module = result.module or "root"
    title = check_titles.get(result.kind, result.kind.title())
    status = result.status.upper()
    print(f"[{module}] {title:<10} {status:<7} {result.duration_sec:>6.2f}s  {result.command}")
    if result.kind == "coverage" and "line" in result.metrics:
        gate = f"  gate >= {result.gate_target:.1f}%" if result.gate_target is not None else ""
        print(f"  line: {result.metrics['line']:.1f}%{gate}")
    if result.status != "pass":
        details = result.stderr_tail[-1:] or result.stdout_tail[-1:]
        for line in details:
            print(f"  detail: {line}")


def _print_report(report) -> None:
    check_titles = {
        "build": "Build",
        "lint": "Lint",
        "typecheck": "TypeCheck",
        "test": "Test",
        "coverage": "Coverage",
        "custom": "Custom",
    }
    print(f"Project: {report.project_name}")
    grouped = group_checks_by_module(report)
    for module, checks in grouped.items():
        print(f"Module: {module}")
        for check in checks:
            status = check.status.upper()
            title = check_titles.get(check.kind, check.kind.title())
            print(f"- {title:<10} {status:<7} {check.duration_sec:>6.2f}s  {check.command}")
            if check.kind == "coverage" and "line" in check.metrics:
                gate = f"  gate >= {check.gate_target:.1f}%" if check.gate_target is not None else ""
                print(f"  line: {check.metrics['line']:.1f}%{gate}")
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


def _print_init_summary(
    config_path: Path,
    report: ScanReport,
    *,
    configured_checks: list[CheckConfig] | None = None,
    initialized_baselines: int = 0,
    run_record: Path | None = None,
) -> None:
    print("AgentShield Init")
    print(f"Config written: {config_path}")
    if run_record is not None:
        print(f"Initial run record: {run_record}")
    if initialized_baselines:
        print(f"Baselines initialized: {initialized_baselines}")
    print(f"Project: {report.project_name}")
    if configured_checks is None:
        visible_modules = reviewable_modules(report.modules)
        print(f"Detected business modules: {len(visible_modules)}")
        for module in visible_modules:
            print(
                f"- {module.path}  {module.language}  "
                f"confidence={module.confidence:.2f}  checks={len(module.recommended_checks)}"
            )
        return

    configured_by_module: dict[str, int] = {}
    for check in configured_checks:
        if not check.module:
            continue
        configured_by_module.setdefault(check.module, 0)
        configured_by_module[check.module] += 1

    detected_by_path = {module.path: module for module in report.modules}
    print(f"Configured business modules: {len(configured_by_module)}")
    for module_path, count in configured_by_module.items():
        module = detected_by_path.get(module_path)
        if module is None:
            print(f"- {module_path}  checks={count}")
            continue
        print(
            f"- {module.path}  {module.language}  "
            f"confidence={module.confidence:.2f}  checks={count}"
        )


def _print_scan_progress() -> None:
    print("AgentShield Analyzer")
    print("[1/4] Reading directory tree (3 levels)...")
    print("[2/4] Reading key config files...")
    print("[3/4] Reading CI workflows...")
    print("[4/4] AI analysis...")

def _describe_frameworks(module: ScanModuleSuggestion) -> str:
    return ", ".join(module.frameworks) if module.frameworks else "no framework detected"


def _confirm(prompt: str, *, default: bool = False) -> bool:
    default_hint = "[Y/n]" if default else "[y/N]"
    try:
        value = input(f"{prompt} {default_hint}: ").strip().lower()
    except EOFError:
        return default
    if not value:
        return default
    return value in {"y", "yes"}


def _prompt_choice(prompt: str, valid_choices: set[str], default: str) -> str:
    while True:
        try:
            value = input(f"{prompt} ").strip()
        except EOFError:
            return default
        if not value:
            return default
        if value in valid_choices:
            return value
        print(f"Expected one of: {', '.join(sorted(valid_choices))}")


def _prompt_text(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        return default or ""
    if value:
        return value
    return default or ""


def _edit_checks(module: ScanModuleSuggestion, checks: list[CheckConfig]) -> list[CheckConfig]:
    while True:
        print(f"Are the check commands correct for {module.path}?")
        for index, check in enumerate(checks, start=1):
            print(f"  [{index}] {check.kind}: {check.command_display()}")
        choice = _prompt_choice(
            "[1] Confirm all  [2] Edit one  [3] Enter manually  [4] Skip this module",
            {"1", "2", "3", "4"},
            "1",
        )
        if choice == "1":
            return checks
        if choice == "4":
            print(f"Skipping module: {module.path}")
            return []
        if choice == "2":
            edit_index = _prompt_text("Select check number to edit")
            if not edit_index.isdigit():
                print("Expected a numeric check selection.")
                continue
            index = int(edit_index) - 1
            if index < 0 or index >= len(checks):
                print("Check number out of range.")
                continue
            selected = checks[index]
            new_command = _prompt_text("Enter replacement command", selected.command_display())
            checks[index] = selected.model_copy(update={"argv": shlex.split(new_command), "run": None})
            continue

        manual_checks: list[CheckConfig] = []
        for check in checks:
            manual_command = _prompt_text(
                f"Command for {module.path} {check.kind} (leave blank to skip)",
                check.command_display(),
            )
            if not manual_command:
                continue
            manual_checks.append(
                check.model_copy(update={"argv": shlex.split(manual_command), "run": None})
            )
        if manual_checks:
            return manual_checks
        print("No manual checks entered; keeping generated defaults.")


def _configure_notify(bootstrap_config: AgentShieldConfig):
    notify = bootstrap_config.notify
    choice = _prompt_choice(
        "Configure notification channel? [1] Set webhook  [2] Skip for now",
        {"1", "2"},
        "2",
    )
    if choice == "2":
        return notify
    webhook_url = _prompt_text("Webhook URL", notify.webhook_url)
    return notify.model_copy(
        update={
            "enabled": bool(webhook_url),
            "webhook_url": webhook_url or None,
            "send_on": ["always"],
        }
    )


def _run_scan_with_progress(bootstrap_config) -> ScanReport:
    _print_scan_progress()
    snapshot = collect_repo_snapshot(bootstrap_config.project_root)
    report = normalize_scan_report(run_scan(snapshot, bootstrap_config.llm), snapshot)
    report.project_name = bootstrap_config.project.name
    print("AI analysis complete.")
    return report


def _interactive_initialize_project(
    *,
    bootstrap_config: AgentShieldConfig,
    config_path: Path,
    used_config_file: bool,
) -> tuple[AgentShieldConfig, ScanReport]:
    report = _run_scan_with_progress(bootstrap_config)
    chosen_checks: list[CheckConfig] = []
    visible_modules = reviewable_modules(report.modules)
    total_reviewable = len(visible_modules)
    for index, module in enumerate(visible_modules, start=1):
        print(f"Sub-module {index}/{total_reviewable}: {module.path}")
        print(
            f"Detected: {module.language} · {_describe_frameworks(module)}"
        )
        detection_ok = _confirm("Is the detection correct?", default=True)
        generated_checks = build_checks_from_scan_module(module, bootstrap_config.project_root)
        if not detection_ok:
            print("Detection not confirmed. Review or replace the suggested commands for this module.")
        selected_checks = _edit_checks(module, generated_checks)
        chosen_checks.extend(selected_checks)

    updated_bootstrap = bootstrap_config.model_copy(
        update={"notify": _configure_notify(bootstrap_config)}
    )
    generated_config, payload = build_config_payload(
        project_name=report.project_name,
        project_root=bootstrap_config.project_root,
        checks=chosen_checks,
        existing_config=updated_bootstrap,
        include_llm=used_config_file,
        include_notify=True,
    )
    write_generated_config(payload, config_path)
    return generated_config, report


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
    config, _, _ = load_config()
    sync_baselines(
        config,
        baseline_dir=BASELINE_DIR,
        updated_at=datetime.now(timezone.utc),
        module_names=modules,
    )
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
        report = normalize_scan_report(run_scan(snapshot, config.llm), snapshot)
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
            generated_config, report = initialize_project(
                bootstrap_config=bootstrap_config,
                config_path=config_path,
                used_config_file=used_config_file,
            )
        except (ScanAPIError, ValueError) as exc:
            print(str(exc))
            return 1
        run_report, _ = run_checks(
            generated_config,
            config_path=config_path,
            used_config_file=used_config_file,
            strict=True,
            run_dir=RUN_DIR,
            baseline_dir=BASELINE_DIR,
            send_notifications=False,
        )
        initialized_baselines = ensure_initial_baselines(run_report, BASELINE_DIR)
        _print_init_summary(
            config_path,
            report,
            configured_checks=generated_config.checks,
            initialized_baselines=len(initialized_baselines),
            run_record=Path(run_report.run_file),
        )
        registered = sync_project_register(
            generated_config,
            "ready" if run_report.status == "pass" else "blocked",
        )
        if registered and initialized_baselines:
            sync_baselines(
                generated_config,
                baseline_dir=BASELINE_DIR,
                updated_at=datetime.now(timezone.utc),
            )
        if run_report.status != "pass":
            _print_report(run_report)
            return 1
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
            if sys.stdin.isatty():
                generated_config, init_report = _interactive_initialize_project(
                    bootstrap_config=bootstrap_config,
                    config_path=config_path,
                    used_config_file=used_config_file,
                )
            else:
                generated_config, init_report = initialize_project(
                    bootstrap_config=bootstrap_config,
                    config_path=config_path,
                    used_config_file=used_config_file,
                )
        except (ScanAPIError, ValueError) as exc:
            print(str(exc))
            return 1
        _print_init_summary(
            config_path,
            init_report,
            configured_checks=generated_config.checks,
        )

    config, config_path, used_config_file = load_config(args.config)
    llm_settings = resolve_llm_settings(config.llm)

    if config.llm.enabled and not llm_settings.is_configured:
        print("Warning: LLM scan is enabled in config but `base_url` or API key is missing.")

    _print_check_start(config_path, config)
    progress_lock = threading.Lock()

    def _progress_callback(result: CheckResult) -> None:
        with progress_lock:
            _print_check_progress(result)

    report, webhook_sent = run_checks(
        config,
        config_path=config_path,
        used_config_file=used_config_file,
        strict=args.strict,
        run_dir=RUN_DIR,
        baseline_dir=BASELINE_DIR,
        send_notifications=not args.dry_run,
        progress_callback=_progress_callback,
    )
    initialized_baselines = [] if args.dry_run else ensure_initial_baselines(report, BASELINE_DIR)
    if not config_exists and not args.dry_run:
        registered = sync_project_register(
            config,
            "ready" if report.status == "pass" else "blocked",
        )
        if registered and initialized_baselines:
            sync_baselines(
                config,
                baseline_dir=BASELINE_DIR,
                updated_at=datetime.now(timezone.utc),
            )
    _print_summary(
        Path(report.run_file),
        used_config_file,
        webhook_sent,
        dry_run=args.dry_run,
        initialized_baselines=initialized_baselines,
    )
    _print_report(report)
    if not args.dry_run:
        sync_run(config, report, baseline_dir=BASELINE_DIR)

    if args.strict and report.status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

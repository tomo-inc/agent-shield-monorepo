from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agentshield_cli.analyzer.ai_client import ScanAPIError, run_scan
from agentshield_cli.analyzer.scanner import collect_repo_snapshot
from agentshield_cli.bootstrap import initialize_project
from agentshield_cli.config import load_config
from agentshield_cli.llm import resolve_llm_settings
from agentshield_cli.models import ScanReport
from agentshield_cli.runner import run_checks


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
    return parser


def _print_summary(report_path: Path, used_config_file: bool, webhook_sent: bool) -> None:
    print("AgentShield Clean · Mode 1")
    print(f"Config source: {'file' if used_config_file else 'built-in default'}")
    print(f"Run record: {report_path}")
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
        run_dir=Path(".qa-agent/runs"),
    )
    _print_summary(Path(report.run_file), used_config_file, webhook_sent)
    _print_report(report)

    if args.strict and report.status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

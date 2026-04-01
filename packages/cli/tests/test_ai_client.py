from __future__ import annotations

import json
import subprocess

from agentshield_cli.analyzer.ai_client import extract_json_payload, run_scan
from agentshield_cli.config import LLMConfig
from agentshield_cli.models import FileSample, RepoSnapshot


def test_extract_json_payload_from_code_fence() -> None:
    payload = extract_json_payload("```json\n{\"project_name\":\"demo\"}\n```")
    assert payload == "{\"project_name\":\"demo\"}"


def test_run_scan_parses_openai_compatible_response(monkeypatch) -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": """{
  "project_name": "demo",
  "project_type": "monorepo",
  "summary": "demo repo",
  "modules": [
    {
      "name": "apps/api",
      "path": "apps/api",
      "language": "python",
      "frameworks": ["fastapi", "pytest"],
      "confidence": 0.98,
      "evidence": ["apps/api/pyproject.toml"],
      "recommended_checks": [
        {"id": "test", "argv": ["pnpm", "test:api"]}
      ],
      "notes": ["detected FastAPI service"]
    }
  ],
  "global_notes": ["monorepo detected"]
}"""
                }
            }
        ]
    }

    def fake_run(command, input, text, capture_output, check):
        assert command[0] == "curl"
        assert "-X" in command
        assert "POST" in command
        assert "https://example.com/v1/chat/completions" in command
        assert input is not None
        assert "Use logical business modules, not individual source files" in input
        assert "Do not use a single source file path like `src/bin/merchant.rs`" in input
        assert "For every business module, recommend commands for these check kinds in this order when possible" in input
        assert "`build`, `typecheck`, `test`, `coverage`, `lint`" in input
        assert "Set each recommended check `id` to one of those exact values." in input
        assert "Each recommended check must use an `argv` array only." in input
        assert "You are AgentShield Analyzer" not in input
        assert text is True
        assert capture_output is True
        assert check is False
        payload = json.dumps(response) + "\n__HTTP_STATUS__:200"
        return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

    monkeypatch.setattr("agentshield_cli.analyzer.ai_client.subprocess.run", fake_run)
    report = run_scan(
        RepoSnapshot(root=".", tree=["apps/"], files=[FileSample(path="README.md", content="# Demo")]),
        LLMConfig(
            enabled=True,
            model="gpt-5.4",
            base_url="https://example.com/v1",
            api_key="secret",
            timeout_sec=5,
        ),
    )

    assert report.project_type == "monorepo"
    assert report.modules[0].path == "apps/api"
    assert report.modules[0].recommended_checks[0].argv == ["pnpm", "test:api"]
    assert report.llm_model == "gpt-5.4"


def test_run_scan_falls_back_across_models_on_upstream_502(monkeypatch) -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": '{"project_name":"demo","project_type":"monorepo","summary":"demo","modules":[]}'
                }
            }
        ]
    }
    seen_models: list[str] = []

    def fake_run(command, input, text, capture_output, check):
        del text, capture_output, check
        body = json.loads(input)
        model = body["model"]
        seen_models.append(model)
        if model in {"gpt-5.4", "claude-sonnet-4-6"}:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="error code: 502\n__HTTP_STATUS__:502",
                stderr="",
            )
        payload = json.dumps(response) + "\n__HTTP_STATUS__:200"
        return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

    monkeypatch.setattr("agentshield_cli.analyzer.ai_client.subprocess.run", fake_run)
    report = run_scan(
        RepoSnapshot(root=".", tree=["apps/"], files=[FileSample(path="README.md", content="# Demo")]),
        LLMConfig(
            enabled=True,
            model="gpt-5.4",
            base_url="https://example.com/v1",
            api_key="secret",
            timeout_sec=5,
        ),
    )

    assert seen_models == ["gpt-5.4", "claude-sonnet-4-6", "gpt-5.3-codex"]
    assert report.llm_model == "gpt-5.3-codex"


def test_run_scan_raises_last_error_when_all_fallback_models_fail(monkeypatch) -> None:
    seen_models: list[str] = []

    def fake_run(command, input, text, capture_output, check):
        del text, capture_output, check
        body = json.loads(input)
        seen_models.append(body["model"])
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="error code: 502\n__HTTP_STATUS__:502",
            stderr="",
        )

    monkeypatch.setattr("agentshield_cli.analyzer.ai_client.subprocess.run", fake_run)

    try:
        run_scan(
            RepoSnapshot(root=".", tree=["apps/"], files=[FileSample(path="README.md", content="# Demo")]),
            LLMConfig(
                enabled=True,
                model="gpt-5.4",
                base_url="https://example.com/v1",
                api_key="secret",
                timeout_sec=5,
            ),
        )
    except RuntimeError as exc:
        assert str(exc) == "LLM request failed with HTTP 502: error code: 502"
    else:
        raise AssertionError("Expected fallback chain to raise after all models fail")

    assert seen_models == ["gpt-5.4", "claude-sonnet-4-6", "gpt-5.3-codex"]

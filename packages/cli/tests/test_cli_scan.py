from __future__ import annotations

from agentshield_cli.cli import main


def test_scan_returns_clean_error_on_api_failure(monkeypatch, tmp_path) -> None:
    config_dir = tmp_path / ".agentshield"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  name: demo",
                "  root: .",
                "llm:",
                "  enabled: true",
                "  base_url: https://example.com/v1",
                "  api_key: secret",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def fake_run_scan(snapshot, llm_config):
        from agentshield_cli.analyzer.ai_client import ScanAPIError

        raise ScanAPIError("LLM request failed with HTTP 403: forbidden")

    monkeypatch.setattr("agentshield_cli.cli.run_scan", fake_run_scan)

    exit_code = main(["scan"])

    assert exit_code == 1

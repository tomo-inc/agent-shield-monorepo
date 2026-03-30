from __future__ import annotations

from pathlib import Path

from agentshield_cli.config import load_config
from agentshield_cli.llm import resolve_llm_settings


def test_load_config_falls_back_to_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config, path, used_config_file = load_config()

    assert path == Path(".agentshield/config.yaml")
    assert used_config_file is False
    assert [check.id for check in config.checks] == ["lint", "typecheck", "test", "openapi"]


def test_llm_settings_resolve_api_key_from_env(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / ".agentshield" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "\n".join(
            [
                "llm:",
                "  enabled: true",
                "  base_url: https://example.com/v1",
                "  api_key_env: TEST_LLM_KEY",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_LLM_KEY", "secret")

    config, _, used_config_file = load_config(config_path)
    settings = resolve_llm_settings(config.llm)

    assert used_config_file is True
    assert settings.base_url == "https://example.com/v1"
    assert settings.api_key == "secret"
    assert settings.is_configured is True


def test_load_config_reads_dotenv_local(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / ".agentshield"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    env_path = config_dir / ".env.local"
    config_path.write_text(
        "\n".join(
            [
                "llm:",
                "  enabled: true",
                "  base_url_env: TEST_LLM_BASE_URL",
                "  api_key_env: TEST_LLM_KEY",
            ]
        ),
        encoding="utf-8",
    )
    env_path.write_text(
        "\n".join(
            [
                "TEST_LLM_BASE_URL=https://api.example.com/v1",
                "TEST_LLM_KEY=dotenv-secret",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("TEST_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("TEST_LLM_KEY", raising=False)

    config, _, _ = load_config(config_path)
    settings = resolve_llm_settings(config.llm)

    assert settings.base_url == "https://api.example.com/v1"
    assert settings.api_key == "dotenv-secret"

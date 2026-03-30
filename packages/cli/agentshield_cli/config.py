from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


DEFAULT_CONFIG_PATH = Path(".agentshield/config.yaml")
DEFAULT_LLM_BASE_URL = "https://api-infer.agentsey.ai/v1"
DEFAULT_LLM_API_KEY = "sk-infer-l58w9OsyKfe9VqdI8Rt4gA"


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "agent-shield-monorepo"
    root: str = "."


class CheckConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    module: str | None = None
    kind: Literal["build", "lint", "typecheck", "test", "coverage", "custom"] = "custom"
    argv: list[str] | None = None
    run: str | None = None
    cwd: str | None = None
    coverage_parser: Literal["coverage.py-json", "istanbul-summary", "jacoco-xml"] | None = None
    coverage_file: str | None = None
    timeout_sec: int = 1200
    enabled: bool = True

    @model_validator(mode="after")
    def validate_command_source(self) -> "CheckConfig":
        if not self.argv and not self.run:
            msg = "Each check must define either `argv` or `run`."
            raise ValueError(msg)
        if self.kind == "coverage":
            if not self.coverage_parser or not self.coverage_file:
                msg = "Coverage checks must define `coverage_parser` and `coverage_file`."
                raise ValueError(msg)
        if (self.coverage_parser is None) != (self.coverage_file is None):
            msg = "`coverage_parser` and `coverage_file` must be set together."
            raise ValueError(msg)
        return self

    def resolved_argv(self) -> list[str] | None:
        if self.argv:
            return self.argv
        if self.run:
            return shlex.split(self.run)
        return None

    def command_display(self) -> str:
        if self.argv:
            return shlex.join(self.argv)
        if self.run:
            return self.run
        return ""


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    provider: str = "openai-compatible"
    model: str = "gpt-4.1-mini"
    base_url: str | None = DEFAULT_LLM_BASE_URL
    base_url_env: str | None = "AGENTSHIELD_LLM_BASE_URL"
    api_key: str | None = DEFAULT_LLM_API_KEY
    api_key_env: str | None = "AGENTSHIELD_LLM_API_KEY"
    timeout_sec: int = 90

    def resolved_base_url(self) -> str | None:
        if self.base_url_env and os.getenv(self.base_url_env):
            return os.getenv(self.base_url_env)
        if self.base_url:
            return self.base_url
        return None

    def resolved_api_key(self) -> str | None:
        if self.api_key_env and os.getenv(self.api_key_env):
            return os.getenv(self.api_key_env)
        if self.api_key:
            return self.api_key
        return None


class NotifyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    webhook_url: str | None = None
    webhook_url_env: str | None = "AGENTSHIELD_WEBHOOK_URL"
    send_on: list[Literal["failure", "success", "always"]] = Field(default_factory=lambda: ["always"])
    timeout_sec: int = 10

    @model_validator(mode="after")
    def normalize_send_on(self) -> "NotifyConfig":
        if self.enabled and self.send_on == ["failure"]:
            self.send_on = ["always"]
        return self

    def resolved_webhook_url(self) -> str | None:
        if self.webhook_url:
            return self.webhook_url
        if self.webhook_url_env:
            return os.getenv(self.webhook_url_env)
        return None


def default_checks() -> list[CheckConfig]:
    return [
        CheckConfig(id="lint", label="Lint", argv=["pnpm", "lint"], timeout_sec=1200),
        CheckConfig(id="typecheck", label="Typecheck", argv=["pnpm", "typecheck"], timeout_sec=1200),
        CheckConfig(id="test", label="Test", argv=["pnpm", "test"], timeout_sec=1800),
        CheckConfig(id="openapi", label="OpenAPI", argv=["pnpm", "check:openapi"], timeout_sec=600),
    ]


class AgentShieldConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    checks: list[CheckConfig] = Field(default_factory=default_checks)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    notify: NotifyConfig = Field(default_factory=NotifyConfig)

    @property
    def project_root(self) -> Path:
        return Path(self.project.root).resolve()


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, value.strip())


def load_config(config_path: Path | None = None) -> tuple[AgentShieldConfig, Path, bool]:
    path = config_path or DEFAULT_CONFIG_PATH
    _load_env_file(path.parent / ".env.local")
    if not path.exists():
        name = Path.cwd().name
        config = AgentShieldConfig(project=ProjectConfig(name=name, root="."))
        return config, path, False

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    config = AgentShieldConfig.model_validate(raw)
    return config, path, True

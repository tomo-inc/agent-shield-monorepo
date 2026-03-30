from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from agentshield_cli.config import LLMConfig
from agentshield_cli.llm import resolve_llm_settings
from agentshield_cli.models import RepoSnapshot, ScanReport


JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class ScanAPIError(RuntimeError):
    """Raised when the remote scan API call fails."""


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    raise ValueError("Unsupported chat completion content payload")


def extract_json_payload(content: str) -> str:
    match = JSON_BLOCK.search(content)
    if match:
        return match.group(1)

    stripped = content.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return stripped[start : end + 1]
    raise ValueError("No JSON object found in LLM response")


def _build_prompt(snapshot: RepoSnapshot) -> str:
    schema = json.dumps(ScanReport.model_json_schema(), indent=2)
    payload = json.dumps(snapshot.model_dump(mode="json"), indent=2)
    return (
        "Analyze this repository snapshot for AgentShield QA automation.\n"
        "Return exactly one JSON object that matches the provided schema.\n"
        "Recommend check commands that are realistic for the detected stack.\n"
        "Prefer repo-relative paths and existing package-manager commands.\n"
        "Do not include markdown fences or commentary.\n\n"
        f"Target schema:\n{schema}\n\n"
        f"Repository snapshot:\n{payload}\n"
    )


def _post_chat_completion(body: dict[str, Any], llm_config: LLMConfig, api_key: str, endpoint: str) -> str:
    marker = "__HTTP_STATUS__:"
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--location",
        "--max-time",
        str(llm_config.timeout_sec),
        "-X",
        "POST",
        endpoint,
        "-H",
        f"Authorization: Bearer {api_key}",
        "-H",
        "Content-Type: application/json",
        "-H",
        "Accept: application/json",
        "--data-binary",
        "@-",
        "--write-out",
        f"\n{marker}%{{http_code}}",
    ]
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(body),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ScanAPIError("LLM scan requires `curl` to be installed on the system") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ScanAPIError(f"LLM request failed: {detail}")

    payload, separator, status_text = completed.stdout.rpartition(f"\n{marker}")
    if not separator:
        raise ScanAPIError("LLM request failed: missing HTTP status marker in curl response")
    status_code = int(status_text.strip())
    if status_code >= 400:
        detail = payload.strip()[:500]
        raise ScanAPIError(f"LLM request failed with HTTP {status_code}: {detail}")
    return payload


def run_scan(snapshot: RepoSnapshot, llm_config: LLMConfig) -> ScanReport:
    settings = resolve_llm_settings(llm_config)
    if not settings.is_configured or not settings.base_url or not settings.api_key:
        raise ValueError("LLM scan is not configured with base_url and api_key")

    body = {
        "model": settings.model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are AgentShield Analyzer. "
                    "You inspect repository snapshots and return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(snapshot),
            },
        ],
    }
    endpoint = settings.base_url.rstrip("/") + "/chat/completions"
    response_body = _post_chat_completion(body, llm_config, settings.api_key, endpoint)

    parsed = json.loads(response_body)
    content = parsed["choices"][0]["message"]["content"]
    text = _extract_text_content(content)
    json_payload = extract_json_payload(text)
    report = ScanReport.model_validate_json(json_payload)
    report.llm_model = settings.model
    report.provider = settings.provider
    return report

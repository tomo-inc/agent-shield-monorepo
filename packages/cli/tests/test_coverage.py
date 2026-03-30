from __future__ import annotations

from pathlib import Path

from agentshield_cli.coverage import parse_coverage_metrics


def test_parse_jacoco_metrics_from_module_directory(tmp_path: Path) -> None:
    report_path = tmp_path / "ab-wallet-api" / "target" / "site" / "jacoco"
    report_path.mkdir(parents=True)
    (report_path / "jacoco.xml").write_text(
        """
        <report name="demo">
          <counter type="LINE" missed="30" covered="70" />
        </report>
        """,
        encoding="utf-8",
    )

    metrics = parse_coverage_metrics("jacoco-xml", tmp_path)

    assert metrics == {"line": 70.0}

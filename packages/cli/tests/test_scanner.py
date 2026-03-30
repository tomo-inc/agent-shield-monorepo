from __future__ import annotations

from pathlib import Path

from agentshield_cli.analyzer.scanner import build_tree, collect_repo_snapshot


def test_build_tree_skips_runtime_dirs(tmp_path: Path) -> None:
    (tmp_path / "apps" / "api").mkdir(parents=True)
    (tmp_path / ".qa-agent" / "runs").mkdir(parents=True)
    (tmp_path / "apps" / "api" / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / ".qa-agent" / "runs" / "latest.json").write_text("{}", encoding="utf-8")

    tree = build_tree(tmp_path)

    assert "apps/" in tree
    assert "apps/api/" in tree
    assert ".qa-agent/" not in tree


def test_collect_repo_snapshot_reads_key_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "pom.xml").write_text("<project></project>\n", encoding="utf-8")
    (tmp_path / "apps" / "web").mkdir(parents=True)
    (tmp_path / "apps" / "web" / "package.json").write_text("{\"name\":\"web\"}", encoding="utf-8")
    (tmp_path / "apps" / "api").mkdir(parents=True)
    (tmp_path / "apps" / "api" / "pom.xml").write_text("<project></project>\n", encoding="utf-8")

    snapshot = collect_repo_snapshot(tmp_path)

    paths = [sample.path for sample in snapshot.files]
    assert "README.md" in paths
    assert "Cargo.toml" in paths
    assert "pom.xml" in paths
    assert "apps/api/pom.xml" in paths
    assert "apps/web/package.json" in paths

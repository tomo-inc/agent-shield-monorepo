from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Base
from app.db.session import get_engine
from app.schemas.panel import PanelProjectRegisterRequest, PanelProjectModule, PanelRunModule, PanelRunUploadRequest, PanelCheckerResult
from app.services.panel.baseline_upload import upload_baselines
from app.services.panel.project_register import register_project
from app.services.panel.run_upload import upload_run
from app.schemas.panel import PanelBaselineModule, PanelBaselineUploadRequest


def iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def seed_project(session: Session) -> None:
    register_project(
        session,
        PanelProjectRegisterRequest(
            project_key="agent-shield-monorepo",
            project_name="AgentShield Monorepo",
            repo_path="/workspace/agent-shield-monorepo",
            preset="infer-monorepo",
            onboarding_status="ready",
            modules=[
                PanelProjectModule(module_name="apps/api", stack="Python / FastAPI", language="Python"),
                PanelProjectModule(module_name="apps/web", stack="TypeScript / Next.js", language="TypeScript"),
            ],
        ),
    )
    upload_baselines(
        session,
        PanelBaselineUploadRequest(
            project_key="agent-shield-monorepo",
            updated_at=iso("2026-03-30T09:00:00Z"),
            modules=[
                PanelBaselineModule(module_name="apps/api", baseline_pct=81.0),
                PanelBaselineModule(module_name="apps/web", baseline_pct=72.0),
            ],
        ),
    )
    upload_run(
        session,
        PanelRunUploadRequest(
            project_key="agent-shield-monorepo",
            run_key="agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
            source="local-cli",
            git_ref="main",
            git_sha="abc123",
            triggered_by="dawei",
            started_at=iso("2026-03-30T10:00:00Z"),
            finished_at=iso("2026-03-30T10:00:31Z"),
            duration_sec=31.0,
            strict_mode=True,
            status="fail",
            block_reason="apps/web coverage below gate",
            modules=[
                PanelRunModule(
                    module_name="apps/api",
                    stack="Python / FastAPI",
                    language="Python",
                    status="pass",
                    coverage_pct=81.2,
                    baseline_pct=81.0,
                    coverage_gate_pct=76.0,
                    coverage_delta_pct=0.2,
                    coverage_parser="pytest-cov-json",
                    block_reason=None,
                    checker_results=[
                        PanelCheckerResult(checker="build", status="pass", detail="", duration_sec=3.2),
                        PanelCheckerResult(checker="lint", status="pass", detail="", duration_sec=2.1),
                        PanelCheckerResult(checker="typecheck", status="pass", detail="", duration_sec=4.5),
                        PanelCheckerResult(checker="test", status="pass", detail="86 passed / 0 failed", duration_sec=10.0),
                        PanelCheckerResult(checker="coverage", status="pass", detail="Line 81.2%, gate >= 76.0%", duration_sec=1.0),
                    ],
                ),
                PanelRunModule(
                    module_name="apps/web",
                    stack="TypeScript / Next.js",
                    language="TypeScript",
                    status="fail",
                    coverage_pct=58.3,
                    baseline_pct=72.0,
                    coverage_gate_pct=67.0,
                    coverage_delta_pct=-13.7,
                    coverage_parser="istanbul-json",
                    block_reason="coverage below gate",
                    checker_results=[
                        PanelCheckerResult(checker="build", status="pass", detail="", duration_sec=12.3),
                        PanelCheckerResult(checker="lint", status="pass", detail="", duration_sec=3.4),
                        PanelCheckerResult(checker="typecheck", status="pass", detail="", duration_sec=5.2),
                        PanelCheckerResult(checker="test", status="pass", detail="43 passed / 0 failed", duration_sec=8.0),
                        PanelCheckerResult(checker="coverage", status="fail", detail="Line 58.3%, gate >= 67.0%", duration_sec=1.3),
                    ],
                ),
            ],
        ),
    )

    register_project(
        session,
        PanelProjectRegisterRequest(
            project_key="agentpay-sdk-internal",
            project_name="AgentPay SDK Internal",
            repo_path="/workspace/agentpay-sdk-internal",
            preset="agentpay-sdk",
            onboarding_status="pending",
            modules=[
                PanelProjectModule(module_name="sdk/python", stack="Python / SDK", language="Python"),
            ],
        ),
    )
    upload_baselines(
        session,
        PanelBaselineUploadRequest(
            project_key="agentpay-sdk-internal",
            updated_at=iso("2026-03-29T07:00:00Z"),
            modules=[PanelBaselineModule(module_name="sdk/python", baseline_pct=82.0)],
        ),
    )
    upload_run(
        session,
        PanelRunUploadRequest(
            project_key="agentpay-sdk-internal",
            run_key="agentpay-sdk-internal_def456_2026-03-29T08:00:00Z_github-actions",
            source="github-actions",
            git_ref="main",
            git_sha="def456",
            triggered_by="ci-bot",
            started_at=iso("2026-03-29T08:00:00Z"),
            finished_at=iso("2026-03-29T08:00:24Z"),
            duration_sec=24.0,
            strict_mode=True,
            status="pass",
            block_reason=None,
            modules=[
                PanelRunModule(
                    module_name="sdk/python",
                    stack="Python / SDK",
                    language="Python",
                    status="pass",
                    coverage_pct=84.0,
                    baseline_pct=82.0,
                    coverage_gate_pct=77.0,
                    coverage_delta_pct=2.0,
                    coverage_parser="pytest-cov-json",
                    block_reason=None,
                    checker_results=[
                        PanelCheckerResult(checker="build", status="pass", detail="", duration_sec=2.4),
                        PanelCheckerResult(checker="lint", status="pass", detail="", duration_sec=1.9),
                        PanelCheckerResult(checker="typecheck", status="pass", detail="", duration_sec=3.0),
                        PanelCheckerResult(checker="test", status="pass", detail="57 passed / 0 failed", duration_sec=7.2),
                        PanelCheckerResult(checker="coverage", status="pass", detail="Line 84.0%, gate >= 77.0%", duration_sec=0.9),
                    ],
                )
            ],
        ),
    )

    register_project(
        session,
        PanelProjectRegisterRequest(
            project_key="tomo-dashboard",
            project_name="Tomo Dashboard",
            repo_path="/workspace/tomo-dashboard",
            preset="infer-monorepo",
            onboarding_status="blocked",
            modules=[
                PanelProjectModule(module_name="src", stack="TypeScript / Vite", language="TypeScript"),
            ],
        ),
    )
    upload_baselines(
        session,
        PanelBaselineUploadRequest(
            project_key="tomo-dashboard",
            updated_at=iso("2026-03-31T06:00:00Z"),
            modules=[PanelBaselineModule(module_name="src", baseline_pct=65.0)],
        ),
    )
    upload_run(
        session,
        PanelRunUploadRequest(
            project_key="tomo-dashboard",
            run_key="tomo-dashboard_ghi789_2026-03-31T07:00:00Z_github-actions",
            source="github-actions",
            git_ref="main",
            git_sha="ghi789",
            triggered_by="ci-bot",
            started_at=iso("2026-03-31T07:00:00Z"),
            finished_at=iso("2026-03-31T07:00:18Z"),
            duration_sec=18.0,
            strict_mode=True,
            status="blocked",
            block_reason="src typecheck failed",
            modules=[
                PanelRunModule(
                    module_name="src",
                    stack="TypeScript / Vite",
                    language="TypeScript",
                    status="blocked",
                    coverage_pct=61.0,
                    baseline_pct=65.0,
                    coverage_gate_pct=60.0,
                    coverage_delta_pct=-4.0,
                    coverage_parser="istanbul-json",
                    block_reason="typecheck failed",
                    checker_results=[
                        PanelCheckerResult(checker="build", status="pass", detail="", duration_sec=2.2),
                        PanelCheckerResult(checker="lint", status="pass", detail="", duration_sec=1.5),
                        PanelCheckerResult(checker="typecheck", status="fail", detail="14 errors", duration_sec=4.1),
                        PanelCheckerResult(checker="test", status="skip", detail="skipped after typecheck failure", duration_sec=0.0),
                        PanelCheckerResult(checker="coverage", status="skip", detail="coverage skipped due to block", duration_sec=0.0),
                    ],
                )
            ],
        ),
    )

    register_project(
        session,
        PanelProjectRegisterRequest(
            project_key="agent-notes-service",
            project_name="Agent Notes Service",
            repo_path="/workspace/agent-notes-service",
            preset="infer-monorepo",
            onboarding_status="ready",
            modules=[
                PanelProjectModule(module_name="services/api", stack="Python / FastAPI", language="Python"),
            ],
        ),
    )
    upload_baselines(
        session,
        PanelBaselineUploadRequest(
            project_key="agent-notes-service",
            updated_at=iso("2026-03-31T05:30:00Z"),
            modules=[PanelBaselineModule(module_name="services/api", baseline_pct=88.0)],
        ),
    )
    upload_run(
        session,
        PanelRunUploadRequest(
            project_key="agent-notes-service",
            run_key="agent-notes-service_jkl012_2026-03-31T06:20:00Z_local-cli",
            source="local-cli",
            git_ref="main",
            git_sha="jkl012",
            triggered_by="dawei",
            started_at=iso("2026-03-31T06:20:00Z"),
            finished_at=iso("2026-03-31T06:20:22Z"),
            duration_sec=22.0,
            strict_mode=True,
            status="pass",
            block_reason=None,
            modules=[
                PanelRunModule(
                    module_name="services/api",
                    stack="Python / FastAPI",
                    language="Python",
                    status="pass",
                    coverage_pct=91.4,
                    baseline_pct=88.0,
                    coverage_gate_pct=82.0,
                    coverage_delta_pct=3.4,
                    coverage_parser="pytest-cov-json",
                    block_reason=None,
                    checker_results=[
                        PanelCheckerResult(checker="build", status="pass", detail="", duration_sec=1.8),
                        PanelCheckerResult(checker="lint", status="pass", detail="", duration_sec=1.2),
                        PanelCheckerResult(checker="typecheck", status="pass", detail="", duration_sec=2.7),
                        PanelCheckerResult(checker="test", status="pass", detail="64 passed / 0 failed", duration_sec=6.9),
                        PanelCheckerResult(checker="coverage", status="pass", detail="Line 91.4%, gate >= 82.0%", duration_sec=0.8),
                    ],
                )
            ],
        ),
    )


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        seed_project(session)
        session.commit()


if __name__ == "__main__":
    main()

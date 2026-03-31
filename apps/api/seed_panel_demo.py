from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Base
from app.db.session import get_engine
from app.schemas.panel import PanelBaselineModule, PanelBaselineUploadRequest
from app.schemas.panel import PanelCheckerResult, PanelProjectModule, PanelProjectRegisterRequest, PanelRunModule, PanelRunUploadRequest
from app.services.panel.baseline_upload import upload_baselines
from app.services.panel.project_register import register_project
from app.services.panel.run_upload import upload_run


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


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        seed_project(session)
        session.commit()


if __name__ == "__main__":
    main()

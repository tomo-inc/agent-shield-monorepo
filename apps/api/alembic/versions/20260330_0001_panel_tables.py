"""create panel tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260330_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "panel_projects",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project_key", sa.String(), nullable=False),
        sa.Column("project_name", sa.String(), nullable=False),
        sa.Column("repo_path", sa.String(), nullable=False),
        sa.Column("preset", sa.String(), nullable=False),
        sa.Column("onboarding_status", sa.String(), nullable=False),
        sa.Column("commands_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("thresholds_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("timeouts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notify_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("project_key", name="uq_panel_projects_project_key"),
    )
    op.create_table(
        "panel_modules",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("panel_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_name", sa.String(), nullable=False),
        sa.Column("stack", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_panel_modules_project_module", "panel_modules", ["project_id", "module_name"], unique=True)
    op.create_table(
        "panel_baselines",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("panel_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.BigInteger(), sa.ForeignKey("panel_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("baseline_pct", sa.Double(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_panel_baselines_project_module", "panel_baselines", ["project_id", "module_id"], unique=True)
    op.create_table(
        "panel_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("panel_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_key", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("git_ref", sa.String(), nullable=True),
        sa.Column("git_sha", sa.String(), nullable=True),
        sa.Column("triggered_by", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_sec", sa.Double(), nullable=True),
        sa.Column("strict_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("run_key", name="uq_panel_runs_run_key"),
    )
    op.create_index(
        "idx_panel_runs_project_finished_at", "panel_runs", ["project_id", "finished_at", "id"], unique=False
    )
    op.create_table(
        "panel_run_modules",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("panel_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.BigInteger(), sa.ForeignKey("panel_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stack", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("coverage_pct", sa.Double(), nullable=True),
        sa.Column("baseline_pct", sa.Double(), nullable=True),
        sa.Column("coverage_gate_pct", sa.Double(), nullable=True),
        sa.Column("coverage_delta_pct", sa.Double(), nullable=True),
        sa.Column("coverage_parser", sa.String(), nullable=True),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_panel_run_modules_run_module", "panel_run_modules", ["run_id", "module_id"], unique=True)
    op.create_index("idx_panel_run_modules_run_id", "panel_run_modules", ["run_id"], unique=False)
    op.create_table(
        "panel_checker_results",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("panel_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "run_module_id", sa.BigInteger(), sa.ForeignKey("panel_run_modules.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("checker", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("duration_sec", sa.Double(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_panel_checker_results_unique", "panel_checker_results", ["run_module_id", "checker"], unique=True
    )
    op.create_index("idx_panel_checker_results_run_id", "panel_checker_results", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_panel_checker_results_run_id", table_name="panel_checker_results")
    op.drop_index("idx_panel_checker_results_unique", table_name="panel_checker_results")
    op.drop_table("panel_checker_results")
    op.drop_index("idx_panel_run_modules_run_id", table_name="panel_run_modules")
    op.drop_index("idx_panel_run_modules_run_module", table_name="panel_run_modules")
    op.drop_table("panel_run_modules")
    op.drop_index("idx_panel_runs_project_finished_at", table_name="panel_runs")
    op.drop_table("panel_runs")
    op.drop_index("idx_panel_baselines_project_module", table_name="panel_baselines")
    op.drop_table("panel_baselines")
    op.drop_index("idx_panel_modules_project_module", table_name="panel_modules")
    op.drop_table("panel_modules")
    op.drop_table("panel_projects")

"""make panel project preset nullable"""

from alembic import op
import sqlalchemy as sa


revision = "20260330_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("panel_projects", "preset", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.alter_column("panel_projects", "preset", existing_type=sa.String(), nullable=False)

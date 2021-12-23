"""Refactor time_complete to laste_updated on shift_task

Revision ID: e90a807d730c
Revises: b54b6cf2251c
Create Date: 2021-12-19 20:58:16.123416

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e90a807d730c"
down_revision = "b54b6cf2251c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("shift_task", sa.Column("last_updated", sa.DateTime(), nullable=True))
    op.drop_column("shift_task", "time_complete")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "shift_task",
        sa.Column(
            "time_complete", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
    )
    op.drop_column("shift_task", "last_updated")
    # ### end Alembic commands ###
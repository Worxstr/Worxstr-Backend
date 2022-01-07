"""Update long lat

Revision ID: cef33543ad3b
Revises: e2f19badc308
Create Date: 2021-12-28 18:18:01.587330

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "cef33543ad3b"
down_revision = "e2f19badc308"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user_location", sa.Column("latitude", sa.Float(precision=32), nullable=True)
    )
    op.add_column(
        "user_location", sa.Column("longitude", sa.Float(precision=32), nullable=True)
    )
    op.drop_column("user_location", "lat")
    op.drop_column("user_location", "lng")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user_location",
        sa.Column(
            "lng",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "user_location",
        sa.Column(
            "lat",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("user_location", "longitude")
    op.drop_column("user_location", "latitude")
    # ### end Alembic commands ###

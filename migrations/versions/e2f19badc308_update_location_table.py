"""Update location table

Revision ID: e2f19badc308
Revises: c409fbcb411b
Create Date: 2021-12-28 16:18:29.781547

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e2f19badc308"
down_revision = "c409fbcb411b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user_location", sa.Column("accuracy", sa.Float(precision=32), nullable=True)
    )
    op.add_column(
        "user_location", sa.Column("altitude", sa.Float(precision=32), nullable=True)
    )
    op.add_column(
        "user_location",
        sa.Column("altitude_accuracy", sa.Float(precision=32), nullable=True),
    )
    op.add_column(
        "user_location", sa.Column("heading", sa.Float(precision=32), nullable=True)
    )
    op.add_column(
        "user_location", sa.Column("lat", sa.Float(precision=32), nullable=True)
    )
    op.add_column(
        "user_location", sa.Column("lng", sa.Float(precision=32), nullable=True)
    )
    op.add_column(
        "user_location", sa.Column("speed", sa.Float(precision=32), nullable=True)
    )
    op.add_column("user_location", sa.Column("timestamp", sa.DateTime(), nullable=True))
    op.drop_column("user_location", "longitude")
    op.drop_column("user_location", "time")
    op.drop_column("user_location", "latitude")
    op.drop_column("user_location", "precision")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user_location",
        sa.Column("precision", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "user_location",
        sa.Column(
            "latitude",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "user_location",
        sa.Column("time", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "user_location",
        sa.Column(
            "longitude",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("user_location", "timestamp")
    op.drop_column("user_location", "speed")
    op.drop_column("user_location", "lng")
    op.drop_column("user_location", "lat")
    op.drop_column("user_location", "heading")
    op.drop_column("user_location", "altitude_accuracy")
    op.drop_column("user_location", "altitude")
    op.drop_column("user_location", "accuracy")
    # ### end Alembic commands ###
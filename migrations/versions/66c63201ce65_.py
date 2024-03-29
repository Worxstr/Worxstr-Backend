"""empty message

Revision ID: 66c63201ce65
Revises: 6196760e4e73
Create Date: 2021-11-10 22:02:50.119181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "66c63201ce65"
down_revision = "6196760e4e73"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "user", "fs_uniquifier", existing_type=sa.VARCHAR(length=255), nullable=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "user", "fs_uniquifier", existing_type=sa.VARCHAR(length=255), nullable=True
    )
    # ### end Alembic commands ###

"""Add denied flag to payment

Revision ID: 463db72f6333
Revises: a98d65884513
Create Date: 2022-02-11 22:04:45.645545

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "463db72f6333"
down_revision = "a98d65884513"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("payment", sa.Column("denied", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("payment", "denied")
    # ### end Alembic commands ###
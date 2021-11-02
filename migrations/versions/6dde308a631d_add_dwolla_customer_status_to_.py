"""Add Dwolla customer status to organization and contractor

Revision ID: 6dde308a631d
Revises: af784e1ff609
Create Date: 2021-10-27 19:29:34.110681

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6dde308a631d"
down_revision = "af784e1ff609"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "contractor_info",
        sa.Column("dwolla_status", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "organization",
        sa.Column("dwolla_customer_status", sa.String(length=10), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("organization", "dwolla_customer_status")
    op.drop_column("contractor_info", "dwolla_status")
    # ### end Alembic commands ###
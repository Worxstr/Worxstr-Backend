"""Add radius and color

Revision ID: 042d5ac8a66d
Revises: 2744a4bbf16a
Create Date: 2021-08-09 14:33:51.373125

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '042d5ac8a66d'
down_revision = '2744a4bbf16a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job', sa.Column('color', sa.String(length=7), nullable=True))
    op.add_column('job', sa.Column('radius', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('job', 'radius')
    op.drop_column('job', 'color')
    # ### end Alembic commands ###

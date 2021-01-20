"""empty message

Revision ID: c25f79bafa2d
Revises: f84e2dd24f73
Create Date: 2021-01-19 23:03:52.114736

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c25f79bafa2d'
down_revision = 'f84e2dd24f73'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job', sa.Column('latitude', sa.Float(precision=52), nullable=True))
    op.add_column('job', sa.Column('longitude', sa.Float(precision=52), nullable=True))
    op.add_column('time_card', sa.Column('payout_id', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('time_card', 'payout_id')
    op.drop_column('job', 'longitude')
    op.drop_column('job', 'latitude')
    # ### end Alembic commands ###

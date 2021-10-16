"""Add job id to timeclock

Revision ID: 2c5c5c0a074b
Revises: 3c9d0d187051
Create Date: 2021-10-15 18:24:44.867326

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c5c5c0a074b'
down_revision = '3c9d0d187051'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('time_clock', sa.Column('job_id', sa.Integer(), nullable=True))
    op.add_column('time_clock', sa.Column('shift_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'time_clock', 'job', ['job_id'], ['id'])
    op.create_foreign_key(None, 'time_clock', 'schedule_shift', ['shift_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'time_clock', type_='foreignkey')
    op.drop_constraint(None, 'time_clock', type_='foreignkey')
    op.drop_column('time_clock', 'shift_id')
    op.drop_column('time_clock', 'job_id')
    # ### end Alembic commands ###

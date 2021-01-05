"""Added organization id to user

Revision ID: 05dcc3df8e5f
Revises: 9b3493335c8d
Create Date: 2021-01-04 03:05:49.101196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05dcc3df8e5f'
down_revision = '9b3493335c8d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'employee_info', ['ssn'])
    op.add_column('job', sa.Column('consultant_email', sa.String(length=255), nullable=True))
    op.add_column('user', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'organization', ['organization_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'organization_id')
    op.drop_column('job', 'consultant_email')
    op.drop_constraint(None, 'employee_info', type_='unique')
    # ### end Alembic commands ###
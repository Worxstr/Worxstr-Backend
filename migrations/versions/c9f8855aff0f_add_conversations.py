"""Add conversations

Revision ID: c9f8855aff0f
Revises: 1e7e98778744
Create Date: 2021-01-22 18:48:33.619085

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c9f8855aff0f'
down_revision = '1e7e98778744'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('conversation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_conversation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('conversation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('message', sa.Column('conversation_id', sa.Integer(), nullable=True))
    op.drop_constraint('message_recipient_id_fkey', 'message', type_='foreignkey')
    op.create_foreign_key(None, 'message', 'conversation', ['conversation_id'], ['id'])
    op.drop_column('message', 'recipient_id')
    op.drop_column('user', 'last_message_read_time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('last_message_read_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('message', sa.Column('recipient_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'message', type_='foreignkey')
    op.create_foreign_key('message_recipient_id_fkey', 'message', 'user', ['recipient_id'], ['id'])
    op.drop_column('message', 'conversation_id')
    op.drop_table('user_conversation')
    op.drop_table('conversation')
    # ### end Alembic commands ###
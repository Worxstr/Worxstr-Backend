"""Add debit smae day fee field

Revision ID: 7fe461dd1550
Revises: fc841b035bd6
Create Date: 2022-04-03 14:54:19.717761

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.models import SubscriptionTier


# revision identifiers, used by Alembic.
revision = '7fe461dd1550'
down_revision = 'fc841b035bd6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subscription_tier', sa.Column('business_same_day_fee', sa.Numeric(), nullable=True))
    # ### end Alembic commands ###
    conn = op.get_bind()
    session = Session(bind=conn)
    for item in session.query(SubscriptionTier).filter_by(business_same_day_fee=None):
        item.business_same_day_fee = 0.02
    session.commit()

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscription_tier', 'business_same_day_fee')
    # ### end Alembic commands ###

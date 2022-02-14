"""Add tables for invoicing and updated payments

Revision ID: 5faf4f716cc9
Revises: 3c4f12338b5e
Create Date: 2022-02-05 17:11:19.838765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5faf4f716cc9"
down_revision = "3c4f12338b5e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "bank_transfer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=True),
        sa.Column("transaction_type", sa.String(), nullable=True),
        sa.Column("bank_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("status_updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "invoice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("timecard_id", sa.Integer(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("date_created", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["timecard_id"],
            ["time_card.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "invoice_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoice.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=True),
        sa.Column("fee", sa.Numeric(), nullable=True),
        sa.Column("total", sa.Numeric(), nullable=True),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("bank_transfer_id", sa.Integer(), nullable=True),
        sa.Column("date_completed", sa.DateTime(), nullable=True),
        sa.Column("dwolla_payment_transaction_id", sa.String(), nullable=True),
        sa.Column("dwolla_fee_transaction_id", sa.String(), nullable=True),
        sa.Column("sender_dwolla_url", sa.String(), nullable=True),
        sa.Column("receiver_dwolla_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["bank_transfer_id"],
            ["bank_transfer.id"],
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoice.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("payment")
    op.drop_table("invoice_item")
    op.drop_table("invoice")
    op.drop_table("bank_transfer")
    # ### end Alembic commands ###
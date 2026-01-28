"""Add billing tables and columns

Revision ID: 0004_billing_tables
Revises: 0003_create_businesses_table
Create Date: 2026-01-19 23:09:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_billing_tables'
down_revision = '0003_create_businesses_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to businesses table
    op.add_column('businesses', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
    op.add_column('businesses', sa.Column('subscription_status', sa.String(length=50), server_default='active', nullable=True))
    op.add_column('businesses', sa.Column('balance_minutes', sa.Integer(), server_default='0', nullable=True))

    # Create billing_usage_events table
    op.create_table(
        'billing_usage_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], )
    )


def downgrade() -> None:
    op.drop_table('billing_usage_events')
    op.drop_column('businesses', 'balance_minutes')
    op.drop_column('businesses', 'subscription_status')
    op.drop_column('businesses', 'stripe_customer_id')

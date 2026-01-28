"""add usage tracking columns

Revision ID: 0007
Revises: 0006
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '0007_usage_tracking'
down_revision = '0006_phone_tracking'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('businesses', sa.Column('minutes_used', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('businesses', sa.Column('minutes_limit', sa.Integer(), nullable=True, server_default='100'))
    op.add_column('businesses', sa.Column('billing_cycle_start', sa.DateTime(), nullable=True, server_default=sa.func.now()))

def downgrade():
    op.drop_column('businesses', 'billing_cycle_start')
    op.drop_column('businesses', 'minutes_limit')
    op.drop_column('businesses', 'minutes_used')

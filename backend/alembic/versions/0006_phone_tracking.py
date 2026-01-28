"""add phone tracking fields

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_phone_tracking'
down_revision = '0005_users_tables'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('businesses', sa.Column('phone_number_sid', sa.String(length=50), nullable=True))
    op.add_column('businesses', sa.Column('phone_number_status', sa.String(length=50), nullable=True, server_default='pending'))

def downgrade():
    op.drop_column('businesses', 'phone_number_status')
    op.drop_column('businesses', 'phone_number_sid')

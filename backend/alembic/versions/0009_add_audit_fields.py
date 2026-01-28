"""add audit fields

Revision ID: 0009_add_audit_fields
Revises: 0008_create_calls_table
Create Date: 2026-01-21 06:30:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0009_add_audit_fields'
down_revision = '0008_create_calls_table'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('businesses', sa.Column('pending_description', sa.Text(), nullable=True))
    op.add_column('businesses', sa.Column('pending_faqs', sa.JSON(), nullable=True))
    op.add_column('businesses', sa.Column('audit_status', sa.String(length=50), nullable=True, server_default='verified'))
    op.add_column('businesses', sa.Column('audit_report', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('businesses', 'audit_report')
    op.drop_column('businesses', 'audit_status')
    op.drop_column('businesses', 'pending_faqs')
    op.drop_column('businesses', 'pending_description')

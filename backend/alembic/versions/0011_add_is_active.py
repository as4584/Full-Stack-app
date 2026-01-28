"""add is_active to businesses

Revision ID: 0011_add_is_active
Revises: 0010_create_contacts_table
Create Date: 2026-01-21 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_add_is_active'
down_revision = '0010_create_contacts_table'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('businesses', sa.Column('is_active', sa.Integer(), nullable=True, server_default='1'))


def downgrade():
    op.drop_column('businesses', 'is_active')

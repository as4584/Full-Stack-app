"""add owner_email to businesses

Revision ID: 0014_add_owner_email
Revises: 0013_add_receptionist_enabled
Create Date: 2026-01-24 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014_add_owner_email'
down_revision = '0013_add_receptionist_enabled'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add owner_email column to businesses table
    op.add_column('businesses', sa.Column('owner_email', sa.String(length=255), nullable=True))
    
    # Add index for better query performance
    op.create_index('ix_businesses_owner_email', 'businesses', ['owner_email'])


def downgrade() -> None:
    # Remove index and column
    op.drop_index('ix_businesses_owner_email', 'businesses')
    op.drop_column('businesses', 'owner_email')
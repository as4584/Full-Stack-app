"""add receptionist_enabled to businesses

Revision ID: 0013_add_receptionist_enabled
Revises: 0012_add_shadow_testing_fields
Create Date: 2026-01-22 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013_add_receptionist_enabled'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('receptionist_enabled', sa.Boolean(), nullable=True, server_default='1'))


def downgrade():
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_column('receptionist_enabled')

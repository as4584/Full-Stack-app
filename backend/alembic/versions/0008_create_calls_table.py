"""create calls table

Revision ID: 0008_create_calls_table
Revises: 0007_usage_tracking
Create Date: 2026-01-21 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_create_calls_table'
down_revision = '0007_usage_tracking'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'calls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('call_sid', sa.String(length=50), nullable=True),
        sa.Column('from_number', sa.String(length=50), nullable=True),
        sa.Column('to_number', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(length=255), nullable=True),
        sa.Column('appointment_booked', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    )
    op.create_index(op.f('ix_calls_business_id'), 'calls', ['business_id'], unique=False)
    op.create_index(op.f('ix_calls_call_sid'), 'calls', ['call_sid'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_calls_call_sid'), table_name='calls')
    op.drop_index(op.f('ix_calls_business_id'), table_name='calls')
    op.drop_table('calls')

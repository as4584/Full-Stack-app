"""add shadow testing fields

Revision ID: 0012
Revises: 0011_add_is_active
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011_add_is_active'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to calls table
    # Using batch_op for SQLite compatibility if needed
    with op.batch_alter_table('calls') as batch_op:
        batch_op.add_column(sa.Column('conversation_frame', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('shadow_result', sa.Text(), nullable=True))
    
    # Create evaluation_benchmarks table
    op.create_table(
        'evaluation_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('total_calls', sa.Integer(), nullable=True),
        sa.Column('booking_success_rate', sa.Float(), nullable=True),
        sa.Column('avg_turns_per_booking', sa.Float(), nullable=True),
        sa.Column('false_confirmations', sa.Integer(), nullable=True),
        sa.Column('p95_latency_ms', sa.Float(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_benchmarks_version'), 'evaluation_benchmarks', ['version'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_evaluation_benchmarks_version'), table_name='evaluation_benchmarks')
    op.drop_table('evaluation_benchmarks')
    with op.batch_alter_table('calls') as batch_op:
        batch_op.drop_column('shadow_result')
        batch_op.drop_column('conversation_frame')

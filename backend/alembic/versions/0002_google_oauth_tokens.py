"""create google oauth tokens table

Revision ID: 0002_google_oauth_tokens
Revises: 0001_create_schema_version
Create Date: 2025-12-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_google_oauth_tokens'
down_revision = '0001_create_schema_version'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create google_oauth_tokens table for storing encrypted OAuth credentials."""
    op.create_table(
        'google_oauth_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=False),
        sa.Column('token_type', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('is_connected', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_google_oauth_tokens_tenant_id'), 'google_oauth_tokens', ['tenant_id'], unique=True)


def downgrade() -> None:
    """Drop google_oauth_tokens table."""
    op.drop_index(op.f('ix_google_oauth_tokens_tenant_id'), table_name='google_oauth_tokens')
    op.drop_table('google_oauth_tokens')

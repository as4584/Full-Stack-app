"""create businesses table

Revision ID: 0003_create_businesses_table
Revises: 0002_google_oauth_tokens
Create Date: 2026-01-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_create_businesses_table'
down_revision = '0002_google_oauth_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('greeting_style', sa.String(length=50), nullable=True),
        sa.Column('business_hours', sa.String(length=255), nullable=True),
        sa.Column('common_services', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        sa.Column('faqs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('businesses')

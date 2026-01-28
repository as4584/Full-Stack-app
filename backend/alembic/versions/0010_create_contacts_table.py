"""create_contacts_table

Revision ID: 0010
Revises: 0009
Create Date: 2026-01-21 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010_create_contacts_table'
down_revision = '0009_add_audit_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], )
    )
    op.create_index(op.f('ix_contacts_business_id'), 'contacts', ['business_id'], unique=False)
    op.create_index(op.f('ix_contacts_phone_number'), 'contacts', ['phone_number'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_contacts_phone_number'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_business_id'), table_name='contacts')
    op.drop_table('contacts')

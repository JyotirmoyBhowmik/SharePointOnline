"""Add two-factor authentication tables

Revision ID: 002_add_two_factor
Revises: 001_initial_schema
Create Date: 2025-12-05 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_two_factor'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_two_factor table
    op.create_table(
        'user_two_factor',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('totp_secret', sa.String(length=255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('backup_codes_hash', sa.Text(), nullable=True),
        sa.Column('backup_codes_used', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('enabled_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index('ix_user_two_factor_user_id', 'user_two_factor', ['user_id'], unique=False)
    
    # Create trusted_devices table
    op.create_table(
        'trusted_devices',
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_name', sa.String(length=255), nullable=False),
        sa.Column('device_fingerprint', sa.String(length=500), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('device_id')
    )
    op.create_index('ix_trusted_devices_user_id', 'trusted_devices', ['user_id'], unique=False)
    op.create_index('ix_trusted_devices_token_hash', 'trusted_devices', ['token_hash'], unique=False)
    op.create_index('ix_trusted_devices_expires_at', 'trusted_devices', ['expires_at'], unique=False)
    
    # Create setup_wizard_status table
    op.create_table(
        'setup_wizard_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('configuration_version', sa.String(length=50), nullable=True),
        sa.Column('database_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('azure_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ldap_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('security_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('features_configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['completed_by_user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create initial setup wizard status record
    op.execute("""
        INSERT INTO setup_wizard_status (id, is_completed)
        VALUES (gen_random_uuid(), false)
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('setup_wizard_status')
    op.drop_index('ix_trusted_devices_expires_at', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_token_hash', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_user_id', table_name='trusted_devices')
    op.drop_table('trusted_devices')
    op.drop_index('ix_user_two_factor_user_id', table_name='user_two_factor')
    op.drop_table('user_two_factor')

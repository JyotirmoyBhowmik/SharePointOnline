"""Initial schema with all models

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-12-05 13:38:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('site_owner', 'admin', 'auditor', 'compliance_officer', 'executive', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ad_username', sa.String(length=255), nullable=True),
        sa.Column('ad_distinguished_name', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_ad_username'), 'users', ['ad_username'], unique=False)

    # Create sharepoint_sites table
    op.create_table('sharepoint_sites',
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_url', sa.String(length=500), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('classification', sa.Enum('team_connected', 'communication', 'hub', 'legacy', 'private', name='siteclassification'), nullable=False),
        sa.Column('created_date', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('last_discovered', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('storage_used_mb', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('storage_quota_mb', sa.Integer(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('retention_excluded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ms_site_id', sa.String(length=255), nullable=True),
        sa.Column('ms_group_id', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('site_id')
    )
    op.create_index(op.f('ix_sites_site_url'), 'sharepoint_sites', ['site_url'], unique=True)
    op.create_index(op.f('ix_sites_ms_site_id'), 'sharepoint_sites', ['ms_site_id'], unique=True)
    op.create_index('idx_site_classification_active', 'sharepoint_sites', ['classification', 'is_archived'], unique=False)
    op.create_index('idx_site_last_activity', 'sharepoint_sites', ['last_activity'], unique=False)

    # Create site_ownership table
    op.create_table('site_ownership',
        sa.Column('ownership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('ownership_type', sa.String(length=50), nullable=True, server_default='owner'),
        sa.Column('is_primary_owner', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('assigned_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('ownership_id')
    )
    op.create_index('idx_ownership_user', 'site_ownership', ['user_id', 'is_primary_owner'], unique=False)
    op.create_index('idx_ownership_site', 'site_ownership', ['site_id'], unique=False)

    # Create access_matrix table
    op.create_table('access_matrix',
        sa.Column('access_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('permission_level', sa.String(length=100), nullable=False),
        sa.Column('assignment_type', sa.String(length=50), nullable=False),
        sa.Column('group_name', sa.String(length=255), nullable=True),
        sa.Column('is_external_user', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('external_user_email', sa.String(length=255), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('assigned_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_access', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('access_id')
    )
    op.create_index('idx_access_site_user', 'access_matrix', ['site_id', 'user_id'], unique=False)
    op.create_index('idx_access_permission_level', 'access_matrix', ['permission_level'], unique=False)
    op.create_index('idx_access_external', 'access_matrix', ['is_external_user', 'expiry_date'], unique=False)

    # Create access_review_cycles table
    op.create_table('access_review_cycles',
        sa.Column('review_cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cycle_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'overdue', 'cancelled', name='reviewstatus'), nullable=False, server_default='pending'),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certified_date', sa.DateTime(), nullable=True),
        sa.Column('certified_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['certified_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('review_cycle_id')
    )
    op.create_index('idx_review_assigned_status', 'access_review_cycles', ['assigned_to_user_id', 'status'], unique=False)
    op.create_index('idx_review_site_cycle', 'access_review_cycles', ['site_id', 'cycle_number'], unique=False)
    op.create_index('idx_review_due_date', 'access_review_cycles', ['due_date', 'status'], unique=False)

    # Create access_review_items table
    op.create_table('access_review_items',
        sa.Column('review_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=True),
        sa.Column('permission_level', sa.String(length=100), nullable=False),
        sa.Column('assignment_type', sa.String(length=50), nullable=False),
        sa.Column('last_access_date', sa.DateTime(), nullable=True),
        sa.Column('access_status', sa.Enum('approved', 'revoke', 'needs_investigation', 'pending', name='accessdecision'), nullable=False, server_default='pending'),
        sa.Column('reviewer_comments', sa.Text(), nullable=True),
        sa.Column('approved_date', sa.DateTime(), nullable=True),
        sa.Column('removal_requested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('removal_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['review_cycle_id'], ['access_review_cycles.review_cycle_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('review_item_id')
    )
    op.create_index('idx_review_item_cycle', 'access_review_items', ['review_cycle_id'], unique=False)
    op.create_index('idx_review_item_status', 'access_review_items', ['access_status', 'removal_requested'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('event_datetime', sa.DateTime(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('site_url', sa.String(length=500), nullable=True),
        sa.Column('resource_name', sa.String(length=500), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('result_status', sa.String(length=50), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ms_audit_id', sa.String(length=255), nullable=True),
        sa.Column('synced_from_ms365', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('audit_id')
    )
    op.create_index(op.f('ix_audit_ms_audit_id'), 'audit_logs', ['ms_audit_id'], unique=True)
    op.create_index('idx_audit_event_datetime', 'audit_logs', ['event_datetime'], unique=False)
    op.create_index('idx_audit_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_site_id', 'audit_logs', ['site_id'], unique=False)
    op.create_index('idx_audit_operation', 'audit_logs', ['operation'], unique=False)
    op.create_index('idx_audit_site_datetime', 'audit_logs', ['site_id', 'event_datetime'], unique=False)

    # Create admin_action_logs table
    op.create_table('admin_action_logs',
        sa.Column('action_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.Enum('retention_add', 'retention_remove', 'version_cleanup', 'bin_cleanup', 'access_revoke', 'site_archive', 'quota_update', name='adminactiontype'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('performed_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('performed_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('approval_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_date', sa.DateTime(), nullable=True),
        sa.Column('approval_comments', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'executing', 'completed', 'failed', name='adminactionstatus'), nullable=False, server_default='pending'),
        sa.Column('scheduled_date', sa.DateTime(), nullable=True),
        sa.Column('execution_started', sa.DateTime(), nullable=True),
        sa.Column('execution_completed', sa.DateTime(), nullable=True),
        sa.Column('execution_result', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('action_id')
    )
    op.create_index('idx_action_status', 'admin_action_logs', ['status', 'scheduled_date'], unique=False)
    op.create_index('idx_action_site', 'admin_action_logs', ['site_id', 'action_type'], unique=False)
    op.create_index('idx_action_performed_by', 'admin_action_logs', ['performed_by_user_id'], unique=False)

    # Create document_libraries table (Phase 2)
    op.create_table('document_libraries',
        sa.Column('library_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('library_url', sa.String(length=500), nullable=True),
        sa.Column('ms_library_id', sa.String(length=255), nullable=True),
        sa.Column('item_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('version_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_size_mb', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_modified', sa.DateTime(), nullable=True),
        sa.Column('last_scanned', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.PrimaryKeyConstraint('library_id')
    )
    op.create_index('idx_library_site', 'document_libraries', ['site_id'], unique=False)

    # Create recycle_bin_items table (Phase 2)
    op.create_table('recycle_bin_items',
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_name', sa.String(length=500), nullable=False),
        sa.Column('item_path', sa.String(length=1000), nullable=True),
        sa.Column('item_type', sa.String(length=100), nullable=True),
        sa.Column('deleted_by_email', sa.String(length=255), nullable=True),
        sa.Column('deletion_date', sa.DateTime(), nullable=False),
        sa.Column('size_mb', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('stage', sa.String(length=20), nullable=False),
        sa.Column('ms_item_id', sa.String(length=255), nullable=True),
        sa.Column('restored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('restored_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.PrimaryKeyConstraint('item_id')
    )
    op.create_index('idx_bin_site_stage', 'recycle_bin_items', ['site_id', 'stage'], unique=False)
    op.create_index('idx_bin_deletion_date', 'recycle_bin_items', ['deletion_date'], unique=False)

    # Create retention_policies table (Phase 2)
    op.create_table('retention_policies',
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ms_policy_id', sa.String(length=255), nullable=True),
        sa.Column('retention_period_days', sa.Integer(), nullable=True),
        sa.Column('scope', sa.String(length=100), nullable=True),
        sa.Column('exclusion_list', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('policy_id')
    )
    op.create_index(op.f('ix_retention_ms_policy_id'), 'retention_policies', ['ms_policy_id'], unique=True)

    # Create retention_exclusions table (Phase 2)
    op.create_table('retention_exclusions',
        sa.Column('exclusion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('removed_date', sa.DateTime(), nullable=True),
        sa.Column('removed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sharepoint_sites.site_id'], ),
        sa.ForeignKeyConstraint(['policy_id'], ['retention_policies.policy_id'], ),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['removed_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('exclusion_id')
    )
    op.create_index('idx_exclusion_site_policy', 'retention_exclusions', ['site_id', 'policy_id'], unique=False)
   op.create_index('idx_exclusion_status', 'retention_exclusions', ['status'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_exclusion_status', table_name='retention_exclusions')
    op.drop_index('idx_exclusion_site_policy', table_name='retention_exclusions')
    op.drop_table('retention_exclusions')
    
    op.drop_index(op.f('ix_retention_ms_policy_id'), table_name='retention_policies')
    op.drop_table('retention_policies')
    
    op.drop_index('idx_bin_deletion_date', table_name='recycle_bin_items')
    op.drop_index('idx_bin_site_stage', table_name='recycle_bin_items')
    op.drop_table('recycle_bin_items')
    
    op.drop_index('idx_library_site', table_name='document_libraries')
    op.drop_table('document_libraries')
    
    op.drop_index('idx_action_performed_by', table_name='admin_action_logs')
    op.drop_index('idx_action_site', table_name='admin_action_logs')
    op.drop_index('idx_action_status', table_name='admin_action_logs')
    op.drop_table('admin_action_logs')
    
    op.drop_index('idx_audit_site_datetime', table_name='audit_logs')
    op.drop_index('idx_audit_operation', table_name='audit_logs')
    op.drop_index('idx_audit_site_id', table_name='audit_logs')
    op.drop_index('idx_audit_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_event_datetime', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_ms_audit_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_review_item_status', table_name='access_review_items')
    op.drop_index('idx_review_item_cycle', table_name='access_review_items')
    op.drop_table('access_review_items')
    
    op.drop_index('idx_review_due_date', table_name='access_review_cycles')
    op.drop_index('idx_review_site_cycle', table_name='access_review_cycles')
    op.drop_index('idx_review_assigned_status', table_name='access_review_cycles')
    op.drop_table('access_review_cycles')
    
    op.drop_index('idx_access_external', table_name='access_matrix')
    op.drop_index('idx_access_permission_level', table_name='access_matrix')
    op.drop_index('idx_access_site_user', table_name='access_matrix')
    op.drop_table('access_matrix')
    
    op.drop_index('idx_ownership_site', table_name='site_ownership')
    op.drop_index('idx_ownership_user', table_name='site_ownership')
    op.drop_table('site_ownership')
    
    op.drop_index('idx_site_last_activity', table_name='sharepoint_sites')
    op.drop_index('idx_site_classification_active', table_name='sharepoint_sites')
    op.drop_index(op.f('ix_sites_ms_site_id'), table_name='sharepoint_sites')
    op.drop_index(op.f('ix_sites_site_url'), table_name='sharepoint_sites')
    op.drop_table('sharepoint_sites')
    
    op.drop_index(op.f('ix_users_ad_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    sa.Enum(name='adminactionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='adminactiontype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='accessdecision').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='reviewstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='siteclassification').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)

"""Fresh start migration

Revision ID: 46e9c7fd23fa
Revises: 
Create Date: 2025-12-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '46e9c7fd23fa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # --- Users Table ---
    if 'users' not in tables:
        op.create_table('users',
            sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('avatar_path', sa.String(length=500), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('phone')
        )
    
    # --- Auth Providers Table ---
    if 'auth_providers' not in tables:
        op.create_table('auth_providers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('provider_user_id', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.Text(), nullable=True),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user')
        )
        op.create_index('ix_auth_provider_user', 'auth_providers', ['user_id'], unique=False)

    # --- Applications Table ---
    if 'applications' not in tables:
        op.create_table('applications',
            sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('code', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('base_url', sa.String(length=500), nullable=False),
            sa.Column('img_path', sa.String(length=500), nullable=True),
            sa.Column('icon_path', sa.String(length=500), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('single_session', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='If True, only 1 session allowed per device for this app'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_applications_code'), 'applications', ['code'], unique=True)
        op.create_index(op.f('ix_applications_name'), 'applications', ['name'], unique=True)

    # --- User Applications Table ---
    if 'user_applications' not in tables:
        op.create_table('user_applications',
            sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
            sa.Column('application_id', sa.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('user_id', 'application_id')
        )


def downgrade() -> None:
    # Dropping tables in reverse order of dependencies
    op.drop_table('user_applications')
    op.drop_table('applications')
    op.drop_table('auth_providers')
    op.drop_table('users')

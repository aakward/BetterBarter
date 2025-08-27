"""rename users to profiles and update FKs

Revision ID: d21a2a55c852
Revises: 
Create Date: 2025-08-27 12:22:00.875746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd21a2a55c852_add profiles table'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Drop FKs from dependent tables
    op.drop_constraint('offers_user_id_fkey', 'offers', type_='foreignkey')
    op.drop_constraint('requests_user_id_fkey', 'requests', type_='foreignkey')

    # 2. Drop old users table
    op.drop_table('users')

    # 3. Create new profiles table
    op.create_table(
        'profiles',
        sa.Column('id', sa.String(length=36), primary_key=True),  # UUID from Supabase
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False),
        sa.Column('phone_hash', sa.String(length=64), nullable=True),
        sa.Column('share_phone', sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. Update FKs on dependent tables
    op.alter_column('offers', 'user_id', new_column_name='profile_id', type_=sa.String(length=36))
    op.create_foreign_key(
        'offers_profile_id_fkey', 'offers', 'profiles', ['profile_id'], ['id']
    )

    op.alter_column('requests', 'user_id', new_column_name='profile_id', type_=sa.String(length=36))
    op.create_foreign_key(
        'requests_profile_id_fkey', 'requests', 'profiles', ['profile_id'], ['id']
    )

def downgrade():
    # Reverse: drop FKs to profiles
    op.drop_constraint('offers_profile_id_fkey', 'offers', type_='foreignkey')
    op.drop_constraint('requests_profile_id_fkey', 'requests', type_='foreignkey')

    # Rename columns back to user_id and change type back to integer
    op.alter_column('offers', 'profile_id', new_column_name='user_id', type_=sa.Integer())
    op.alter_column('requests', 'profile_id', new_column_name='user_id', type_=sa.Integer())

    # Drop profiles table
    op.drop_table('profiles')

    # Recreate users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('hashed_pw', sa.String(length=255), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )

    # Restore FKs to users
    op.create_foreign_key(
        'offers_user_id_fkey', 'offers', 'users', ['user_id'], ['id']
    )
    op.create_foreign_key(
        'requests_user_id_fkey', 'requests', 'users', ['user_id'], ['id']
    )
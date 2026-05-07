"""add refresh_tokens table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-07 14:00:00.000000

Сессия 22, Блок C1: таблица refresh-токенов для возможности отзыва.
JWT access — 15 мин (без БД, отозвать нельзя), refresh — 30 дней (в БД,
отзываемый при logout/смене пароля).

Хранится SHA-256 хеш токена, не сам токен.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by', sa.String(length=36), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.create_index(
            'ix_refresh_tokens_user_id', ['user_id'], unique=False,
        )
        batch_op.create_index(
            'ix_refresh_tokens_token_hash', ['token_hash'], unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.drop_index('ix_refresh_tokens_token_hash')
        batch_op.drop_index('ix_refresh_tokens_user_id')
    op.drop_table('refresh_tokens')

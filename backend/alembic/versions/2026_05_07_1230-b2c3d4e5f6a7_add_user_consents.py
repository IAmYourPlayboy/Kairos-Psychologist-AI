"""add user_consents table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-07 12:30:00.000000

Сессия 22, Блок B3: таблица согласий пользователя на обработку ПДн.
Хранит 3 типа согласий с аудит-данными (IP, UA, время, версия документа).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_consents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('guest_id', sa.String(length=36), nullable=True),
        sa.Column('consent_type', sa.String(length=40), nullable=False),
        sa.Column('document_version', sa.String(length=20), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('user_consents', schema=None) as batch_op:
        batch_op.create_index(
            'ix_user_consents_user_id', ['user_id'], unique=False,
        )
        batch_op.create_index(
            'ix_user_consents_guest_id', ['guest_id'], unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('user_consents', schema=None) as batch_op:
        batch_op.drop_index('ix_user_consents_guest_id')
        batch_op.drop_index('ix_user_consents_user_id')
    op.drop_table('user_consents')

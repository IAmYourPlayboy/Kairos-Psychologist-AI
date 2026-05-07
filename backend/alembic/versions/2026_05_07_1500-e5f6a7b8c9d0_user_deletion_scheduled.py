"""add deletion_scheduled_at to users

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-07 15:00:00.000000

Сессия 22, поправка к C1: переход с immediate-delete на 7-day grace period.
Пользователь нажимает «удалить» → ставим deletion_scheduled_at = now() + 7 days.
Целевой Celery-таск ежедневно ищет истёкшие и реально удаляет.

До 7 дней пользователь может зайти и отменить (POST /api/auth/me/cancel-deletion).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'deletion_scheduled_at',
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        batch_op.create_index(
            'ix_users_deletion_scheduled_at',
            ['deletion_scheduled_at'],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_deletion_scheduled_at')
        batch_op.drop_column('deletion_scheduled_at')

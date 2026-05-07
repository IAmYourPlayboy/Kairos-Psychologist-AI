"""add anonymization_log to messages

Revision ID: a1b2c3d4e5f6
Revises: d27b817b65b5
Create Date: 2026-05-07 12:00:00.000000

Сессия 22, Блок B1: добавляет поле anonymization_log в messages для аудита
анонимизации ПДн. Хранит JSON с метаданными замен (тип, длина, позиция),
без самих оригиналов.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd27b817b65b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('anonymization_log', sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_column('anonymization_log')

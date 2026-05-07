"""index on perception_json risk_level (postgres only)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-07 13:00:00.000000

Сессия 22, Блок B4: индекс для аналитических запросов вида
«сколько диалогов с risk_level=immediate за месяц». На SQLite не имеет
смысла (JSON-функции медленные, индексировать нечего). На PostgreSQL —
выражение-индекс.

Мы НЕ ломаем SQLite-разработку: миграция проверяет dialect и пропускает
на не-PG.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Functional index на извлечение risk_level из JSON.
        # Используется в админ-аналитике вида:
        #   SELECT count(*) FROM messages
        #   WHERE perception_json::jsonb->>'risk_level' = 'immediate';
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_messages_perception_risk_level "
            "ON messages ((perception_json::jsonb->>'risk_level')) "
            "WHERE perception_json IS NOT NULL"
        )
    # SQLite: ничего не делаем, на dev-объёмах full scan ок.


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_messages_perception_risk_level")

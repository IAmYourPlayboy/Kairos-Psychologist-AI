"""
Хранилище досье пользователя (Storage)
Сохранение и загрузка досье из PostgreSQL
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.user_memory.dossier import UserDossier
from app.data.models import UserDossierModel


class DossierStorage:
    """Хранилище досье пользователя в PostgreSQL"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def load(self, user_id: str) -> Optional[UserDossier]:
        """
        Загрузить досье пользователя из БД

        Args:
            user_id: ID пользователя

        Returns:
            UserDossier или None если досье не найдено
        """
        stmt = select(UserDossierModel).where(UserDossierModel.user_id == user_id)
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()

        if not row:
            return None

        # Десериализовать JSONB в Pydantic модель
        return UserDossier(**row.dossier)

    async def save(self, dossier: UserDossier) -> None:
        """
        Сохранить досье пользователя в БД

        Использует INSERT ... ON CONFLICT DO UPDATE для upsert

        Args:
            dossier: Досье пользователя
        """
        # Обновить timestamp
        dossier.updated_at = datetime.utcnow()
        dossier.version += 1

        # Сериализовать Pydantic модель в dict
        dossier_dict = dossier.model_dump(mode='json')

        # Upsert через INSERT ... ON CONFLICT DO UPDATE
        stmt = insert(UserDossierModel).values(
            user_id=dossier.user_id,
            dossier=dossier_dict,
            created_at=dossier.created_at,
            updated_at=dossier.updated_at,
            version=dossier.version
        ).on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'dossier': dossier_dict,
                'updated_at': dossier.updated_at,
                'version': dossier.version
            }
        )

        await self.db.execute(stmt)
        await self.db.commit()

    async def delete(self, user_id: str) -> bool:
        """
        Удалить досье пользователя

        Args:
            user_id: ID пользователя

        Returns:
            True если досье было удалено, False если не найдено
        """
        stmt = select(UserDossierModel).where(UserDossierModel.user_id == user_id)
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()

        if not row:
            return False

        await self.db.delete(row)
        await self.db.commit()
        return True

    async def exists(self, user_id: str) -> bool:
        """
        Проверить, существует ли досье пользователя

        Args:
            user_id: ID пользователя

        Returns:
            True если досье существует
        """
        stmt = select(UserDossierModel.user_id).where(UserDossierModel.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

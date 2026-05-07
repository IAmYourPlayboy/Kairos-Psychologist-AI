"""Работа с refresh-токенами в БД.

Реализует OWASP-pattern для refresh token rotation:

1. При login — выпускается новый refresh, его SHA-256 хеш записывается в БД.
2. При refresh — проверяется, что хеш есть в БД и не revoked. Старый
   помечается revoked, выпускается новый, в `replaced_by` ставим id нового.
3. При logout — помечаем все активные refresh пользователя как revoked.
4. При попытке использовать **revoked** refresh — это сигнал о компрометации.
   Отзываем ВСЮ цепочку токенов через replaced_by, заставляем перелогиниться.

Защита от replay-атак: если злоумышленник украл refresh, использовал его
один раз — мы выдали новый. Когда легитимный пользователь попытается
обновить свой украденный refresh, он наткнётся на revoked — сработает
detect-and-burn.

В БД хранится **SHA-256 хеш** токена, не сам токен. Если БД утечёт — токены
не вытекут.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.models import RefreshToken


def _aware(dt: datetime) -> datetime:
    """Гарантировать tz-aware datetime.

    SQLite не сохраняет таймзону даже при ``DateTime(timezone=True)`` —
    возвращает naive datetime. PostgreSQL возвращает tz-aware. Чтобы
    логика была одинаковой на обоих БД, нормализуем здесь:
    naive → считаем UTC, aware → как есть.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _hash_token(token: str) -> str:
    """SHA-256 хеш JWT-строки.

    SHA-256 здесь подходит, потому что:
    - Сам JWT уже подписан HMAC-SHA256 → имеет высокую энтропию (это не пароль)
    - Не нужна защита от bruteforce (никто не угадает 256-битную случайную строку)
    - Нужна скорость и детерминированность для индекса БД
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def store_refresh_token(
    db: AsyncSession,
    *,
    token: str,
    jti: str,
    user_id: str,
    user_agent: str | None,
    ip_address: str | None,
) -> RefreshToken:
    """Записать refresh-токен в БД.

    Используется при login и при rotation.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    record = RefreshToken(
        id=jti,
        user_id=user_id,
        token_hash=_hash_token(token),
        expires_at=expires_at,
        created_at=now,
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=ip_address[:45] if ip_address else None,
    )
    db.add(record)
    await db.flush()
    return record


async def find_active_refresh_token(
    db: AsyncSession, *, token: str,
) -> RefreshToken | None:
    """Найти активную (не revoked, не истёкшую) запись по токену.

    Возвращает None если:
    - токена нет в БД
    - токен revoked
    - токен истёк

    Поиск по хешу — O(1) с индексом.
    """
    token_hash = _hash_token(token)

    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    record: RefreshToken | None = result.scalar_one_or_none()

    if record is None:
        return None
    if record.revoked_at is not None:
        return None  # revoked, но запись осталась — найдём, чтобы решить что делать выше
    if _aware(record.expires_at) < datetime.now(timezone.utc):
        return None
    return record


async def find_refresh_token_record(
    db: AsyncSession, *, token: str,
) -> RefreshToken | None:
    """Найти ЛЮБУЮ запись (включая revoked) по токену.

    Используется для детекции replay-атак: если пришёл revoked токен —
    это сигнал о компрометации, нужно burn-ить всю цепочку.
    """
    token_hash = _hash_token(token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_token(
    db: AsyncSession, *, record: RefreshToken,
    replaced_by: str | None = None,
) -> None:
    """Отозвать один токен.

    Если задан `replaced_by` — записываем ссылку на новый токен в цепочке rotation.
    """
    record.revoked_at = datetime.now(timezone.utc)
    if replaced_by is not None:
        record.replaced_by = replaced_by
    await db.flush()


async def revoke_all_user_tokens(
    db: AsyncSession, *, user_id: str,
) -> int:
    """Отозвать все активные refresh-токены пользователя.

    Используется при:
    - Logout (если хотим залогаутить со всех устройств)
    - Смене пароля
    - Подозрении на компрометацию (через replay detection)

    Returns:
        Количество отозванных токенов.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount or 0


async def detect_and_burn_replay(
    db: AsyncSession, *, suspicious_token_record: RefreshToken,
) -> None:
    """OWASP pattern: использован revoked токен → burn всю цепочку.

    Если пришёл refresh, который числится в БД как revoked — это значит:
    1. Либо легитимный пользователь дважды нажал refresh (редко, гонка)
    2. Либо токен украли, использовали (мы тогда revoked'нули старый),
       а теперь легитимный владелец пытается использовать тот же токен
       (или наоборот — атакующий пришёл вторым)

    В обоих случаях правильно — отозвать ВСЕ токены этого пользователя.
    Лучше пользователь перелогинится один раз, чем атакующий получит
    долгосрочный доступ.
    """
    await revoke_all_user_tokens(db, user_id=suspicious_token_record.user_id)

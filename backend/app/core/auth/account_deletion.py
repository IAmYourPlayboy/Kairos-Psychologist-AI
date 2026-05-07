"""Логика soft-delete + финального удаления аккаунта.

Жизненный цикл:

1. **Запрос на удаление** (`schedule_account_deletion`):
   - User.deletion_scheduled_at = now() + 7 дней
   - Все refresh-токены пользователя — revoked (юзер вылетает со всех устройств)
   - User остаётся, его данные тоже. Ничего не удаляется.

2. **Окно ожидания (7 дней)**:
   - Пользователь может залогиниться (login разрешён)
   - НО все защищённые операции возвращают 403 с инструкцией «восстановить или ждать»
   - Кроме `POST /api/auth/me/cancel-deletion`, который снимает scheduled

3. **Отмена** (`cancel_account_deletion`):
   - User.deletion_scheduled_at = NULL
   - Нужно перелогиниться (refresh уже revoked'ы), но email/password те же

4. **Истечение окна** (`finalize_pending_deletions`):
   - Celery-таск (или ручной CLI) ежедневно ищет:
     `WHERE deletion_scheduled_at < now()`
   - Для каждого:
     a. **Сообщения и сессии** — отвязываем от user_id (у них уже анонимизирован
        текст через ReflectionAgent). Это ценные данные для data flywheel.
        Помечаем `chat_sessions.user_id = NULL`. message_id связь сохраняется.
     b. **DossierFact / DossierQuote / DossierCheckpoint** — удаляем (это уже
        не обезличенный контент, а структурированные факты о пользователе).
     c. **UserConsent** — удаляем (по выбору владельца проекта: если юзер
        ушёл — нет смысла хранить аудит-след, нет с кого требовать).
     d. **Subscription** — пока никак не трогаем (Блок F): при удалении
        аккаунта подписка должна быть `cancel_at_period_end=True`, реально
        cancelled когда `current_period_end` истечёт. Это обрабатывается
        в момент schedule_account_deletion (через ЮKassa SDK).
     e. **RefreshToken** — каскад через ORM (FK с CASCADE)
     f. **User** — удаляем

Целостность: вся операция в одной транзакции. Если что-то упало —
ничего не удалилось, попробуем завтра.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.tokens import revoke_all_user_tokens
from app.data.dossier_models import (
    DossierCheckpoint,
    DossierFact,
    DossierQuote,
)
from app.data.models import (
    ChatSession,
    RefreshToken,
    User,
    UserConsent,
)

logger = logging.getLogger(__name__)


# Сколько дней пользователь может передумать
DELETION_GRACE_DAYS = 7


# ============================================================================
# 1. Запросить удаление
# ============================================================================


async def schedule_account_deletion(
    db: AsyncSession, *, user: User,
) -> datetime:
    """Запланировать удаление аккаунта через 7 дней.

    Возвращает дату фактического удаления (когда Celery-таск удалит).
    Сразу отзывает все refresh-токены (юзер вылетает).
    """
    scheduled = datetime.now(timezone.utc) + timedelta(days=DELETION_GRACE_DAYS)
    user.deletion_scheduled_at = scheduled

    # Revoke всех токенов — пусть юзер перелогинится, чтобы отменить
    await revoke_all_user_tokens(db, user_id=user.id)
    await db.flush()

    logger.info(
        "Account deletion scheduled: user=%s at=%s",
        user.id[:8], scheduled.isoformat(),
    )
    return scheduled


# ============================================================================
# 2. Отменить удаление
# ============================================================================


async def cancel_account_deletion(
    db: AsyncSession, *, user: User,
) -> None:
    """Отменить запланированное удаление."""
    user.deletion_scheduled_at = None
    await db.flush()
    logger.info("Account deletion cancelled: user=%s", user.id[:8])


def is_pending_deletion(user: User) -> bool:
    """User попросил удаления и окно отмены ещё не истекло?

    Если `deletion_scheduled_at` не задан — False.
    Если задан и в будущем — True (можно отменить).
    Если задан и в прошлом — True (Celery вот-вот удалит, но пока ещё не).
    """
    return user.deletion_scheduled_at is not None


# ============================================================================
# 3. Финальное удаление (Celery-таск)
# ============================================================================


async def finalize_pending_deletions(db: AsyncSession) -> dict[str, int]:
    """Реально удалить аккаунты, у которых истекло окно ожидания.

    Запускается раз в сутки через Celery-beat. Возвращает статистику —
    сколько аккаунтов удалено, сколько строк затронуто.

    Идемпотентно: повторный запуск с теми же данными ничего не меняет.
    """
    now = datetime.now(timezone.utc)

    # 1. Найти пользователей с истёкшим окном
    result = await db.execute(
        select(User).where(
            User.deletion_scheduled_at.isnot(None),
            User.deletion_scheduled_at < now,
        ),
    )
    expired_users = list(result.scalars().all())

    if not expired_users:
        return {"users_deleted": 0, "sessions_anonymized": 0, "facts_deleted": 0}

    stats = {
        "users_deleted": 0,
        "sessions_anonymized": 0,
        "facts_deleted": 0,
        "consents_deleted": 0,
        "tokens_deleted": 0,
    }

    for user in expired_users:
        user_stats = await _delete_user_data(db, user=user)
        for key, value in user_stats.items():
            stats[key] = stats.get(key, 0) + value
        stats["users_deleted"] += 1

    await db.commit()
    logger.info("Finalized %d account deletions: %s", stats["users_deleted"], stats)
    return stats


async def _delete_user_data(
    db: AsyncSession, *, user: User,
) -> dict[str, int]:
    """Реально удалить данные одного пользователя.

    Порядок важен: связанные объекты сначала, владелец последним.
    """
    user_id = user.id
    stats: dict[str, int] = {}

    # === Сессии чата: ОТВЯЗЫВАЕМ от user_id (не удаляем) ===
    # Тексты сообщений уже анонимизированы через ReflectionAgent. Эти данные
    # ценны для data flywheel и LoRA. Оставляем их как «осиротевшие» сессии
    # без привязки к пользователю.
    result = await db.execute(
        update(ChatSession)
        .where(ChatSession.user_id == user_id)
        .values(user_id=None, guest_id=None),
    )
    stats["sessions_anonymized"] = result.rowcount or 0

    # === Досье: удаляем полностью ===
    # Cascade orm не сработает (DossierFact.user_id — это строка, не FK
    # с onDelete). Удаляем явно.
    # Quotes удалятся каскадом из Fact (см. DossierFact.quotes relationship)
    facts_result = await db.execute(
        select(DossierFact).where(DossierFact.user_id == user_id),
    )
    facts_to_delete = list(facts_result.scalars().all())
    for fact in facts_to_delete:
        # Quotes привязаны через FK → каскадом удалятся с cascade="all, delete-orphan"
        await db.delete(fact)
    stats["facts_deleted"] = len(facts_to_delete)

    # Чекпойнт удаляем явно
    cp_result = await db.execute(
        select(DossierCheckpoint).where(DossierCheckpoint.user_id == user_id),
    )
    for cp in cp_result.scalars().all():
        await db.delete(cp)

    # === Согласия: удаляем (по решению владельца проекта) ===
    consents_result = await db.execute(
        select(UserConsent).where(UserConsent.user_id == user_id),
    )
    consents = list(consents_result.scalars().all())
    for consent in consents:
        await db.delete(consent)
    stats["consents_deleted"] = len(consents)

    # === Refresh-токены: удаляем явно ===
    # FK не имеет ON DELETE CASCADE, поэтому если удалим User раньше — упадёт.
    tokens_result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id),
    )
    tokens = list(tokens_result.scalars().all())
    for token in tokens:
        await db.delete(token)
    stats["tokens_deleted"] = len(tokens)

    # === Subscription: TODO (Блок F) ===
    # Подписки удалять только если current_period_end < now() (то есть
    # деньги уже не списываются). Активные оставляем доживать. На MVP таблица
    # subscriptions ещё не наполняется, поэтому пропускаем.
    # См. ROADMAP блок F.

    # === User: финальное удаление ===
    await db.delete(user)
    await db.flush()

    return stats


# ============================================================================
# 4. Helper для login: проверить статус
# ============================================================================


def deletion_status(user: User) -> dict:
    """Структура для возврата клиенту: запланировано ли удаление и когда."""
    if user.deletion_scheduled_at is None:
        return {"scheduled": False, "scheduled_at": None}
    return {
        "scheduled": True,
        "scheduled_at": user.deletion_scheduled_at.isoformat(),
    }

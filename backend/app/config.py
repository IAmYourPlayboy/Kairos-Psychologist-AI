"""Конфигурация приложения через переменные окружения.

Все настройки тянутся из `.env` (Pydantic Settings).
Шаблон — в `.env.example`.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings

PLACEHOLDER_API_KEYS = {"", "change-me", "your-api-key-here", "<your-api-key>"}


class Settings(BaseSettings):
    """Все настройки приложения. Значения берутся из .env или окружения."""

    # === Основные ===
    app_name: str = "Kairos"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # === Сервер ===
    host: str = "0.0.0.0"
    port: int = 8001

    # === База данных ===
    # По умолчанию — SQLite для разработки (zero-setup).
    # Для продакшена переключаем на postgresql+asyncpg://...
    database_url: str = "sqlite+aiosqlite:///./kairos_dev.db"

    # === Redis (опционально, для Блока 18+) ===
    redis_url: str = "redis://localhost:6379/0"

    # === LLM-провайдер ===
    # Yandex Cloud AI Studio: использует Api-Key авторизацию (см. openai_compat.py).
    llm_provider: str = "yandex"
    llm_base_url: str = "https://llm.api.cloud.yandex.net/v1"
    llm_api_key: str = "change-me"
    # Полный URI модели вида: gpt://<folder_id>/qwen3-14b/latest
    llm_model: str = "gpt://your-folder-id/qwen3-14b/latest"
    # Folder ID отдельно — на случай, если понадобится в других местах
    yandex_folder_id: str = "your-folder-id"

    # === CORS ===
    cors_origins: list[str] = ["http://localhost:3000"]

    # === Слой восприятия (Сессия 18+) ===
    # Celery broker (тот же Redis, что и для Mood, но другая БД для разделения).
    # Для разработки достаточно redis://localhost:6379/{1,2}
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Через сколько секунд после последнего сообщения запускать ReflectionAgent.
    # 15 минут = пользователь точно ушёл, контекст разговора закончился.
    reflection_delay_seconds: int = 15 * 60

    # === Аутентификация (Блок C1, Сессия 22) ===
    # JWT_SECRET_KEY используется для подписи access и refresh токенов.
    # КРИТИЧНО: в production должен быть задан отдельной переменной из .env,
    # минимум 32 символа случайных данных. Сгенерировать: `openssl rand -hex 32`.
    # Если не задан — fallback на secret_key (но в проде это будет ошибка).
    jwt_secret_key: str = ""  # пустой = использовать secret_key
    jwt_algorithm: str = "HS256"  # HS256 на MVP, RS256 — после когда будет масштаб
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # Cookie settings — Secure=True в production (HTTPS).
    # В dev оставляем False, чтобы работало через http://localhost.
    cookie_secure: bool = False  # переопределяется в .env.production
    cookie_domain: str | None = None  # None = использовать domain из запроса
    cookie_samesite: str = "lax"  # lax: безопасно для большинства, защита от CSRF

    @property
    def effective_jwt_secret(self) -> str:
        """Реально используемый JWT-секрет (с fallback на secret_key)."""
        return self.jwt_secret_key or self.secret_key

    @field_validator("llm_api_key")
    @classmethod
    def _validate_llm_api_key(cls, v: str) -> str:
        """LLM_API_KEY не должен быть плейсхолдером.

        Без валидного ключа приложение не сможет вызывать LLM —
        лучше упасть на старте чем тихо отдавать 500 при первом запросе.
        """
        if v in PLACEHOLDER_API_KEYS:
            raise ValueError(
                f"LLM_API_KEY не настроен (текущее значение: '{v}'). "
                "Получи ключ Yandex Cloud AI Studio и пропиши его в backend/.env"
            )
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        """JWT_SECRET_KEY должен быть >= 32 символов в проде.

        Исключение: пустая строка означает "использовать secret_key как fallback"
        (см. effective_jwt_secret). Это допустимо в dev, но не в prod.
        """
        if v == "":
            return v  # fallback на secret_key
        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY слишком короткий ({len(v)} < 32 символов). "
                "Сгенерируй: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        """DATABASE_URL не должен быть пустым."""
        if not v.strip():
            raise ValueError(
                "DATABASE_URL пустой. Пропиши его в backend/.env "
                "(пример: sqlite+aiosqlite:///./kairos_dev.db)"
            )
        return v

    # === Логирование ===
    log_level: str = "info"

    # === Агенты ===
    pubmed_email: str = "kairos@example.com"
    knowledge_base_path: str = "knowledge_base"

    @property
    def is_sqlite(self) -> bool:
        """Возвращает True если используем SQLite (для условной логики)."""
        return self.database_url.startswith("sqlite")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__",
    }


settings = Settings()

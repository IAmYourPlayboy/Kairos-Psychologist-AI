"""Конфигурация приложения через переменные окружения.

Все настройки тянутся из `.env` (Pydantic Settings).
Шаблон — в `.env.example`.
"""

from pydantic_settings import BaseSettings


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

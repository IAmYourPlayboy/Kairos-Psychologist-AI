"""Конфигурация приложения через переменные окружения."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Все настройки приложения. Значения берутся из .env или окружения."""

    # Основные
    app_name: str = "Kairos"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Сервер
    host: str = "0.0.0.0"
    port: int = 8001

    # База данных
    database_url: str = "postgresql+asyncpg://kairos:kairos@localhost:5432/kairos"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    llm_provider: str = "yandex"
    llm_base_url: str = "https://llm.api.cloud.yandex.net/foundationModels/v1"
    llm_api_key: str = "change-me"
    llm_model: str = "yandexgpt-lite"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Логирование
    log_level: str = "info"

    # PubMed API
    pubmed_email: str = "kairos@example.com"

    # Knowledge Base
    knowledge_base_path: str = "knowledge_base"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__",
    }


settings = Settings()

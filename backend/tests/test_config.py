"""Тесты валидаторов настроек приложения.

Цель: упасть на старте с понятной ошибкой если .env содержит плейсхолдеры
или критичные поля пустые. Лучше явная ошибка на старте, чем тихие 500-ки
при первом запросе.
"""

import pytest
from pydantic import ValidationError


def test_llm_api_key_placeholder_raises():
    """LLM_API_KEY = 'change-me' → ValidationError.

    Передаём поля через kwargs Settings(), чтобы не зависеть от .env файла
    (Pydantic Settings читает .env первым, и monkeypatch не переопределяет
    значения из файла надёжно).
    """
    from app.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            llm_api_key="change-me",
            database_url="sqlite+aiosqlite:///./test.db",
            jwt_secret_key="x" * 40,
            _env_file=None,
        )

    assert "LLM_API_KEY" in str(exc_info.value) or "llm_api_key" in str(exc_info.value)


def test_jwt_secret_too_short_raises():
    """JWT_SECRET_KEY длиной < 32 символов → ValidationError."""
    from app.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            llm_api_key="real-api-key-value-here",
            database_url="sqlite+aiosqlite:///./test.db",
            jwt_secret_key="too-short",  # 9 символов
            _env_file=None,
        )

    assert "JWT_SECRET_KEY" in str(exc_info.value) or "jwt_secret_key" in str(exc_info.value)


def test_database_url_empty_raises():
    """DATABASE_URL пустой → ValidationError."""
    from app.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            llm_api_key="real-api-key-value-here",
            database_url="",
            jwt_secret_key="x" * 40,
            _env_file=None,
        )

    assert "DATABASE_URL" in str(exc_info.value) or "database_url" in str(exc_info.value)


def test_valid_config_does_not_raise():
    """Корректная конфигурация — не падает."""
    from app.config import Settings

    settings = Settings(
        llm_api_key="real-api-key-value-here",
        database_url="sqlite+aiosqlite:///./test.db",
        jwt_secret_key="x" * 40,
        _env_file=None,
    )
    assert settings.llm_api_key == "real-api-key-value-here"
    assert settings.jwt_secret_key == "x" * 40

"""Хеширование паролей через Argon2id.

Argon2id — победитель Password Hashing Competition (PHC, 2015) и стандарт OWASP.
Сочетает устойчивость Argon2i (к side-channel атакам) и Argon2d (к GPU/ASIC).

Параметры (по OWASP cheat sheet, май 2026):
    memory_cost: 64 MiB (65536 KiB)
    time_cost:   3 (количество итераций)
    parallelism: 4 (количество потоков)

Эти параметры дают ~50ms на хеш на современном CPU. Это:
- Достаточно медленно для защиты от bruteforce (миллионы попыток в секунду)
- Достаточно быстро для UX логина (нет видимой задержки)

Pwdlib обёртка автоматически:
- Генерирует случайную соль для каждого хеша
- Включает соль и параметры в саму строку хеша (формат: $argon2id$v=19$m=...$...$)
- Проверяет хеш с правильными параметрами при verify

При смене параметров (ужесточении) старые хеши продолжают работать —
формат самодокументирующийся. Можно реализовать «rehash on login» если нужно.
"""

from __future__ import annotations

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Создаём один раз — это безопасно для конкурентного использования.
# Pwdlib стейтлесс под капотом, методы потокобезопасные.
_password_hash = PasswordHash((
    Argon2Hasher(
        memory_cost=65536,   # 64 MiB
        time_cost=3,
        parallelism=4,
    ),
))


def hash_password(password: str) -> str:
    """Захешировать пароль.

    Возвращает PHC-строку вида ``$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>``.
    Длина — около 100 символов. Помещается в `users.password_hash` (String 255).

    Соль генерируется автоматически, новая для каждого вызова.
    Один и тот же пароль даст разные хеши — это by design.
    """
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Проверить пароль против хеша.

    Возвращает True если пароль совпадает с хешем.
    Никогда не бросает исключение даже на битый хеш — всегда False.

    Использует constant-time сравнение, чтобы не утекали тайминги
    (важно: разница между «неправильный пароль» и «нет такого пользователя»
    должна быть незаметна по времени).
    """
    try:
        return _password_hash.verify(password, hashed)
    except Exception:
        # Битый хеш в БД (старый формат, повреждение, инъекция) — не валим.
        # Просто отвечаем «не совпадает».
        return False


# Минимальная политика паролей (валидация на уровне API, не здесь).
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128  # защита от DoS — Argon2 на длинном пароле может тормозить

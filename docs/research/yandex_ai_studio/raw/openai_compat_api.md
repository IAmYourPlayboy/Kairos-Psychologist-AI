# Yandex AI Studio — OpenAI-совместимый API (raw)

> Источник: документация Yandex AI Studio, статья «Интеграция генеративных моделей в Visual Studio Code»
> Сохранено: Сессия 22, Май 2026

---

## 🚨 Правильный base_url

**Из всех источников Yandex для OpenAI SDK / Roo Code / SourceCraft Code Assistant:**

```
https://ai.api.cloud.yandex.net/v1
```

**НЕ:**

```
https://llm.api.cloud.yandex.net/v1   ← старый эндпоинт (LLM-only?)
```

> ⚠️ **ПРОВЕРИТЬ**: у нас в `backend/.env` сейчас стоит `LLM_BASE_URL=https://llm.api.cloud.yandex.net/v1`.
> Возможно это причина почему `400 "Failed to get model"` для Qwen — на старом эндпоинте Qwen не разворачивается, только YandexGPT.
>
> **Hypothesis to test**: сменить base_url на `ai.api.cloud.yandex.net` и попробовать Qwen ещё раз.

---

## URI моделей

Формат:
```
gpt://<идентификатор_каталога>/<идентификатор_модели>/latest
```

Где `<идентификатор_модели>` — например:
- `qwen3-235b-a22b-fp8`
- `gpt-oss-120b`
- `qwen3.6-35b-a3b` ← **БЕЗ `/latest`** согласно release notes

---

## Стандартный workflow для подключения

1. Создать каталог (например, `aistudio`)
2. Создать сервисный аккаунт (например, `ai-model-user`)
3. Назначить ему роль `ai.languageModels.user`
4. Создать **API-ключ** для сервисного аккаунта (НЕ IAM-токен)
5. **Область действия (scope) ключа**: `yc.ai.languageModels.execute`
6. Сохранить идентификатор и секретный ключ

---

## Аутентификация

В OpenAI SDK используется **`api_key`** (не Bearer-токен в явном виде, OpenAI SDK сам ставит header):

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=token,  # секретный ключ от сервисного аккаунта
)
```

> ⚠️ **Сравнение с нашим кодом** (`OpenAICompatProvider`):
>
> Наш `openai_compat.py` использует **`Authorization: Api-Key <key>`** для Yandex base_url.
> Если переходим на `ai.api.cloud.yandex.net` — нужно проверить, не сменился ли формат header.
>
> Возможно, нужен **`Authorization: Bearer <key>`** (как у обычного OpenAI), а не `Api-Key`.
> Это вторая гипотеза для проверки.

---

## Пример использования (streaming)

Из примера ответа модели в статье — рабочий код для Yandex AI Studio:

```python
import sys
from openai import OpenAI

def main():
    if len(sys.argv) != 3:
        print("Usage: python test.py <token> <model_id>")
        return

    token = sys.argv[1]
    model_id = sys.argv[2]

    client = OpenAI(
        base_url="https://ai.api.cloud.yandex.net/v1",
        api_key=token
    )

    stream = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "user", "content": "Напиши стихотворение про Yandex Cloud"}
        ],
        stream=True
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="")

if __name__ == "__main__":
    main()
```

> Это означает: **streaming поддерживается** через `stream=True`. Стандартный OpenAI-формат.

---

## Что НЕ выяснено пока (TODO)

1. ❓ **Точный синтаксис отключения reasoning mode** для Qwen 3.6
2. ❓ Поддерживается ли `response_format: {"type": "json_object"}` для Qwen
3. ❓ Поддерживается ли `tool_use` через `chat.completions.create` для Qwen (или только через Responses API)
4. ❓ Допустимый диапазон `temperature` (везде 0-1 или 0-2?)
5. ❓ Поведение при превышении контекста (truncate? error?)
6. ❓ Как считаются reasoning tokens — отдельно или в составе completion_tokens?

---

## Скоупы API-ключей

> В поле Область действия выберите `yc.ai.languageModels.execute`.

Это специфичный scope для языковых моделей. У нашего ключа в `.env` (`AQVNyrmsrXS3JRGsOPfPp5oog3P4nXh-ABpnZJjT`) — нужно проверить какой scope. Если scope только для одного эндпоинта — это может быть второй причиной ошибки на новом base_url.

Для MCP-серверов есть отдельный scope:
```
yc.serverless.mcpGateways.invoke
```

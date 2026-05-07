# Yandex AI Studio — SDK и интеграции (raw)

> Источник: документация Yandex AI Studio
> Сохранено: Сессия 22, Май 2026

---

## Yandex Cloud Python SDK

**Репозиторий**: https://github.com/yandex-cloud/python-sdk/

### Что это

Официальный SDK для управления **ресурсами** Yandex Cloud от имени сервисного аккаунта (создание/удаление облаков, каталогов, ВМ и т.д.).

Это **не SDK для генерации текста** — это SDK для управления инфраструктурой через gRPC.

### Когда нужен нам

- При деплое (Блок E) — управлять VPS, бакетами Object Storage, Container Registry через код
- При написании MCP-сервера или Cloud Function
- При автоматизации провижининга

### Когда НЕ нужен

- Для собственно генерации текста через `/v1/chat/completions` — там обычный OpenAI SDK работает.

### Пример

```python
import yandexcloud
from yandex.cloud.resourcemanager.v1.cloud_service_pb2 import ListCloudsRequest
from yandex.cloud.resourcemanager.v1.cloud_service_pb2_grpc import CloudServiceStub

def handler(event, context):
    cloud_service = yandexcloud.SDK().client(CloudServiceStub)
    clouds = {}
    for c in cloud_service.List(ListCloudsRequest()).clouds:
        clouds[c.id] = c.name
    return clouds
```

### Версии Python и Cloud Functions

- **python37 / python38**: SDK предустановлен в среде Cloud Functions, можно не указывать в зависимостях
- **python39+**: SDK не предустановлен, нужно добавить в `requirements.txt`

---

## Yandex AI Studio SDK для Python

> *Не путать с Yandex Cloud SDK!*

В тексте про MCP Hub и Search API упоминается:
> Библиотека Yandex AI Studio SDK для Python упрощает работу с Yandex Search API и другими сервисами Yandex AI Studio, предоставляя удобные Python-интерфейсы для всех типов поиска и автоматическую обработку синхронных и асинхронных запросов.

Это, видимо, отдельная библиотека (или часть Cloud SDK) для работы с AI Studio: токенизация, embeddings, classification, fine-tuning, search.

**Ссылка из доки**: «Исходный код и примеры кода доступны в репозитории на GitHub». Точный URL не указан — нужно искать по тегам `yandex-cloud` + `ai-studio` на GitHub.

### Когда нужен

- Если используем **dataset upload + fine-tune** для эмбеддингов / классификаторов
- Если используем **AI Search** (RAG)
- Если используем **MCP Hub**

### Когда НЕ нужен

- Для нашего MVP пайплайна — обычный OpenAI SDK достаточен.

---

## OpenAI SDK для Python

**Это что используем сейчас и должны использовать дальше.**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",  # ← правильный URL!
    api_key="<секретный ключ от сервисного аккаунта>",
)

response = client.chat.completions.create(
    model="gpt://<folder_id>/qwen3.6-35b-a3b",
    messages=[...],
    stream=True,  # опционально
)
```

> ⚠️ У нас сейчас в коде свой `OpenAICompatProvider` через `httpx` — это нормально (тоже OpenAI-совместимый). Мог бы заменить на `openai` SDK, но смысла мало — тесты уже пройдены, код работает.

---

## SourceCraft Code Assistant + Roo Code

Это **VS Code расширения** для использования Yandex моделей как помощника при разработке. Не имеют отношения к runtime нашего продукта.

**Может пригодиться** разработчику для:
- автокомплит
- генерация документации
- объяснение кода
- написание тестов

**Не пригодится** для самого продукта Кайрос.

### Конфигурация

| Поле | Значение |
|---|---|
| Провайдер API | `OpenAI Compatible` |
| Базовый URL | `https://ai.api.cloud.yandex.net/v1` |
| API-ключ | секретный ключ от сервисного аккаунта |
| Модель | `gpt://<folder_id>/qwen3-235b-a22b-fp8` или `gpt-oss-120b` |

> Тариф: оплачивается по обычным правилам генерации текста (см. `pricing.md`).

---

## Object Storage + S3 Select для биллинга

> Yandex Cloud позволяет настроить регулярный экспорт детализации расходов в Object Storage (S3-совместимое хранилище) и запрашивать данные через **S3 Select** (подмножество SQL).

### Когда нам понадобится

В Блоке E (deploy) — для **финмониторинга**:
1. Настраиваем регулярный экспорт детализации в наш бакет
2. Раз в неделю запускаем S3 Select запрос: «сколько потратили на каждый ресурс»
3. Если LLM-расходы скакнули — алерт

### Минимальный пример

```bash
bucket=<имя_бакета>
key=<ключ_объекта>
query="select service_name,resource_id,sku_id,sku_name,\"date\",cost from S3Object where service_name='AI Studio'"

aws --endpoint https://storage.yandexcloud.net s3api select-object-content \
  --bucket $bucket \
  --key $key \
  --expression "$query" \
  --expression-type 'SQL' \
  --input-serialization 'CSV={FileHeaderInfo=USE,FieldDelimiter=,}' \
  --output-serialization 'CSV={}' \
  "output.csv"
```

### Тарификация

В стоимость анализа детализации входит:
- плата за хранение данных в бакете
- операции с бакетом

(см. тарифы Object Storage отдельно — пока не получили)

---

## Карта сервисов Yandex Cloud — что мы используем

### Используем сейчас или будем

| Сервис | Зачем | Этап |
|---|---|---|
| **Yandex AI Studio** (Foundation Models) | LLM генерация | MVP |
| **Yandex Object Storage** | бакет для бэкапов, для billing-экспорта | Блок E |
| **Yandex Cloud Billing** | биллинг и квоты | Блок E |
| **Yandex IAM** | сервисные аккаунты + API-ключи | Блок A3 (уже) |

### Возможно понадобится

| Сервис | Зачем | Этап |
|---|---|---|
| **Yandex Compute Cloud** | если уйдём на свой VPS внутри Yandex Cloud (вместо Timeweb) | Блок E (опц) |
| **Yandex Managed Service for PostgreSQL** | managed Postgres вместо своего | Блок E (опц) |
| **Yandex Managed Service for Valkey** | managed Redis (Valkey = Redis-fork) | Блок E (опц) |
| **Yandex Cloud Logging** | централизованные логи | Блок E5 |
| **Yandex Cloud Functions** | для cron-задач (автосписание подписок) | Блок F |
| **Yandex API Gateway** | если уйдём на serverless вместо Nginx | Блок E (опц) |

### Точно не нужно

См. `unused_services.md`.

---

## Биллинг и контроль расходов

### Концепция

- Один **платёжный аккаунт** на всю организацию (статусы `ACTIVE` или `TRIAL_ACTIVE`)
- Платёжный аккаунт привязан к **облаку**
- В облаке **каталоги** (folders) — наш `b1gsi8fibvna5mkauuu4`
- Расходы группируются по сервисам и SKU (Stock Keeping Unit)

### Как настроить алерты

(нужна отдельная инфа из доки про Cloud Billing — пока не получили)

---

## Open question для тебя

**Из твоего сообщения**: «КЛОД!!! ТУТ СКАЖИ ЧТО ИМЕННО МНЕ ДЛЯ ТЕБЯ ПОСМОТРЕТЬ!»

Я отвечу отдельно ниже. Здесь — фиксирую сам факт.

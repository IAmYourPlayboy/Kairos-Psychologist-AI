# Сессия 22 — Полная сводка для следующего Claude

> **Дата**: Май 2026
> **Назначение**: единый источник правды о том, что сделано в Сессии 22.
> Будущий Claude/разработчик должен прочитать ROADMAP.md → этот файл → код.

---

## Что закрыто

| Блок | Статус | Описание |
|---|---|---|
| **A1** | ✅ | Backend pytest полностью зелёный |
| **A3** | ✅ | Qwen 3.6 35B-A3B подключена + reasoning отключён |
| **B1** | ✅ | Анонимизатор ПДн в ReflectionAgent |
| **B2** | ✅ | Research Export + K-анонимность |
| **B3** | ✅ | Юридические страницы + 3 чекбокса согласия |
| **B4** | ✅ | perception_json полностью логируется + Postgres-индекс |
| **C1** | ✅ | Backend auth (JWT + Argon2 + refresh rotation) |
| **C2** | ✅ | Frontend auth (AuthProvider + auto-refresh) |
| **C3** | ✅ | Sync engine guest → user |
| **C4** | ✅ | Профиль пользователя + soft-delete |
| **D** | ✅ | Скрининг ASQ + PSS-4 + override + UI |

| Блок | Статус | Описание |
|---|---|---|
| **A2** | ⏳ | Ручная проверка кризис-сценариев (за пользователем) |
| **E** | ⏳ | Deploy (после D) |
| **F** | ⏳ | Платежи (после E) |

---

## Метрики

- **Backend pytest**: 257/257 зелёные (было 135 в начале сессии — почти удвоили)
- **Frontend prod build**: чистый, 12 страниц
- **Новых файлов**: ~40 (миграции, модули, тесты, страницы, компоненты)
- **Новых alembic миграций**: 5 (refresh_tokens, user_consents, anonymization_log, perception_index, deletion_scheduled_at)
- **Новых API endpoints**: 12+ (auth/*, sessions/*, consent, /me/cancel-deletion)

---

## Ключевые архитектурные решения Сессии 22

### 1. Qwen 3.6 35B-A3B вместо YandexGPT

**Почему**: YandexGPT имеет встроенную цензуру (отказывается обсуждать суицид/депрессию глубоко). Qwen 3.6 — нет. Цена сопоставимая, плюс есть **cache discount** (0.05 ₽/1К vs 0.2 ₽/1К на повторяющиеся system-промпты).

**Подводный камень**: reasoning mode у Qwen 3.6 включён по умолчанию. На коротких max_tokens модель тратит все токены на размышления, `content` приходит `null`. **Решение**: `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`. Эндпоинты Yandex отвергают top-level `enable_thinking` и `reasoning` — только `chat_template_kwargs.enable_thinking`.

**В коде**: `app/core/llm/extra_body.py` с хелпером `disable_reasoning()`. Везде в `analyzer.py`, `pipeline.py`, `reflection_agent.py` (extract + dedupe) → `extra_body=disable_reasoning()`.

**Реюзабельный smoke-test**: `backend/scripts/check_llm_connectivity.py`. 4 пробы. При смене модели → прогон даст быстрый sanity check.

### 2. Анонимизация в ReflectionAgent, не на горячем пути

**Почему**: контекстная анонимизация лучше regex'а на одном сообщении. Reflection видит весь батч → один и тот же «папа» в разных сообщениях помечается одинаково. Плюс не нагружаем `/api/chat`.

**Юридически**: бекенд в РФ + явное согласие + окно «оригинал в БД» ≤ 15 минут (стандартный интервал Reflection). Бэкапы делаются раз в сутки → окно полностью внутри bucket'а бэкапа, в бэкап попадают уже обезличенные тексты.

**В коде**: `app/data/anonymizer.py` (regex-движок) + `app/core/perception/reflection_agent.py::_anonymize_messages` (вызывает на батче перед update_checkpoint).

### 3. Soft-delete аккаунта с 7-day grace period

**Почему**: пользователи иногда передумывают. Дать 7 дней на отмену — защита от импульсивных решений + бесплатно с точки зрения хранилища.

**Что НЕ удаляется при удалении аккаунта**:
- `chat_sessions` — текст уже обезличен через ReflectionAgent. Это **золото для data flywheel и LoRA**. При удалении аккаунта `user_id = NULL` (отвязываем).
- `messages` — каскадно сохраняются с сессиями.

**Что удаляется**:
- `dossier_facts`, `dossier_quotes`, `dossier_checkpoints` — это структурированные факты о пользователе, не обезличенные.
- `user_consents` — юзер ушёл, аудит-след не нужен.
- `refresh_tokens` — каскадом.
- `users` — последним.

**Что планируется в Блоке F**:
- `subscriptions`: при удалении аккаунта НЕ ставить `cancelled` сразу, а `cancel_at_period_end=True` (это родное для ЮKassa). Реальный `cancelled` ставится когда `current_period_end` истечёт. Так пользователь не теряет оплаченный период.

**В коде**:
- `app/core/auth/account_deletion.py` — три функции: `schedule_account_deletion`, `cancel_account_deletion`, `finalize_pending_deletions`.
- `User.deletion_scheduled_at` — миграция `e5f6a7b8c9d0`.
- `DELETE /api/auth/me` — теперь schedule, не immediate.
- `POST /api/auth/me/cancel-deletion` — отмена.
- `/api/chat` блокируется 403 для pending-deletion пользователей.
- `frontend/components/Auth/PendingDeletionBanner.tsx` — sticky-баннер с обратным отсчётом.

**TODO для Блока E**: подключить Celery beat task `finalize_pending_deletions` (запускать раз в сутки).

### 4. Refresh token rotation с burn-on-replay

**OWASP-pattern**: каждый refresh-вызов выпускает **новый** access+refresh, старый refresh помечается revoked. Если уже-revoked refresh приходит снова — это сигнал о компрометации, отзываем **всю цепочку** токенов user'а.

**В коде**: `app/core/auth/tokens.py::detect_and_burn_replay`.

В БД хранится **SHA-256 хеш** токена (не сам токен). Если БД утечёт — токены наружу не выйдут.

### 5. Auto-refresh на frontend с защитой от race

В `lib/api.ts` любой запрос на 401 автоматически вызывает `POST /api/auth/refresh`. Если refresh успешен — повтор оригинального запроса. Если нет — 401 уходит наружу, AuthProvider снимет user из state.

**Защита от race**: `refreshInFlight` Promise — если параллельно идут 5 запросов и все получили 401, выполнится **один** refresh (остальные ждут его результат).

**Защита от рекурсии**: на сам `/api/auth/refresh` стоит `skipAutoRefresh=true`.

### 7. ASQ-positive override risk_level=immediate (Блок D)

**Почему**: LLM-анализатор может пропустить суицидальные мысли у скрытного пользователя (тот выбирает слова осторожно). ASQ — валидированный 4-вопросный инструмент NIH с прямыми вопросами. Если человек ответил «да» хотя бы на один — это надёжный сигнал, и анализатор не должен иметь возможность его «переубедить».

**Что в коде**:
- `app/core/screening/{asq,pss4,service}.py` — структуры опросников, scoring, сервис
- `app/api/screening.py` — 7 эндпоинтов
- `app/core/perception/pipeline.py` Шаг 2.5 — override блок:
  ```python
  if await has_active_asq_positive(self._db, user_id=..., guest_id=...):
      if report.risk_level != "immediate":
          report.risk_level = "immediate"  # override LLM-анализатор
  ```
- Тестов на D: 47 (44 unit/service/API + 3 e2e override)

**Точные формулировки опросников** — на русском языке в коде. Менять без re-validation **нельзя** (это валидированные инструменты, изменение формулировки = новый инструмент). Если потом захотим перевести вопросы или адаптировать под подростков — это отдельный научный процесс с отдельной валидацией.

**PSS-4 на frontend пока НЕ показывается**: backend готов (структура + API), но в UI выводим только ASQ. Не нагружаем пользователя двумя опросниками в первой сессии. Можно добавить в `/profile` как «как ты сейчас себя чувствуешь?» в G-фазе.

**Frontend**:
- `useShouldOfferASQ()` хук решает когда показывать (3+ сообщений + elevated/high в ленте + backend разрешает + не отклонено в этой сессии)
- `ScreeningOfferCard` (inline в чате) — приглашение
- `ASQDialog` — модалка по одному вопросу за раз
- `ScreeningResultCard` — три тона по interpretation

### 6. K-анонимность на этапе экспорта

При записи в БД ничего не дропается — теряется сигнал. K-анонимность (`k≥5`) применяется только в `app/data/research_export.py` через бакетизацию квазиидентификаторов: `(crisis_level, outcome, duration_bucket)`. Записи с уникальной комбинацией QI → отбрасываются при экспорте.

CLI: `python -m app.data.research_export --output dataset.jsonl --since 2026-01-01 --k 5`.

---

## Структура нового кода

```
backend/
├── alembic/versions/
│   ├── 2026_05_07_1200-..._add_anonymization_log_to_messages.py
│   ├── 2026_05_07_1230-..._add_user_consents.py
│   ├── 2026_05_07_1300-..._index_perception_risk.py
│   ├── 2026_05_07_1400-..._add_refresh_tokens.py
│   └── 2026_05_07_1500-..._user_deletion_scheduled.py
├── app/
│   ├── api/
│   │   ├── auth.py (новый: register, login, refresh, logout, me, DELETE me, cancel-deletion)
│   │   ├── consent.py (новый: POST/GET /api/consent)
│   │   ├── screening.py (новый: 7 эндпоинтов ASQ/PSS-4 + frequency cap)
│   │   └── sessions.py (новый: GET/PATCH/DELETE /api/sessions, POST /sessions/migrate)
│   ├── core/
│   │   ├── auth/ (новый каталог)
│   │   │   ├── __init__.py
│   │   │   ├── account_deletion.py — soft-delete и финальное удаление
│   │   │   ├── cookies.py — httpOnly cookies
│   │   │   ├── dependencies.py — get_current_user, get_optional_user
│   │   │   ├── jwt.py — выпуск/декод JWT
│   │   │   ├── password.py — Argon2id
│   │   │   └── tokens.py — refresh rotation + burn-on-replay
│   │   ├── llm/
│   │   │   └── extra_body.py — disable_reasoning(), merge_extra()
│   │   └── screening/ (новый каталог, Блок D)
│   │       ├── __init__.py
│   │       ├── asq.py — структура ASQ + score_asq
│   │       ├── pss4.py — структура PSS-4 + score_pss4
│   │       └── service.py — ScreeningService + has_active_asq_positive
│   └── data/
│       ├── anonymizer.py (новый)
│       └── research_export.py (новый)
├── scripts/
│   └── check_llm_connectivity.py (новый)
└── tests/
    ├── test_account_deletion.py (новый)
    ├── test_anonymizer.py (новый)
    ├── test_auth_api.py (новый)
    ├── test_chat_with_asq_positive.py (новый — e2e ASQ override)
    ├── test_consent_api.py (новый)
    ├── test_research_export.py (новый)
    ├── test_screening.py (новый)
    └── test_sessions_api.py (новый)

frontend/
├── app/
│   ├── auth/
│   │   ├── login/page.tsx (новый)
│   │   └── register/page.tsx (новый)
│   ├── legal/ (4 страницы новых)
│   │   ├── consent/page.tsx
│   │   ├── offer/page.tsx
│   │   ├── privacy/page.tsx
│   │   └── terms/page.tsx
│   └── profile/page.tsx (расширен)
├── components/
│   ├── Auth/ (новый каталог)
│   │   ├── AuthProvider.tsx
│   │   ├── LoginForm.tsx
│   │   ├── PendingDeletionBanner.tsx
│   │   └── RegisterForm.tsx
│   ├── Legal/ (новый)
│   │   ├── FirstVisitModal.tsx
│   │   └── FooterDisclaimer.tsx
│   ├── Profile/ (новый)
│   │   ├── AccountSection.tsx
│   │   └── SessionsSection.tsx
│   └── Screening/ (новый, Блок D)
│       ├── ASQDialog.tsx
│       ├── ScreeningOfferCard.tsx
│       └── ScreeningResultCard.tsx
├── hooks/
│   ├── useAuth.ts (новый)
│   └── useScreeningOffer.ts (новый — useShouldOfferASQ)
└── lib/
    ├── auth.ts (новый — API клиент)
    ├── sessions.ts (новый)
    ├── screening.ts (новый — ASQ/PSS-4 API)
    └── api.ts (расширен auto-refresh)

docs/
├── research/yandex_ai_studio/ (новая папка)
│   ├── README.md
│   ├── digest/decision_qwen_choice.md
│   └── raw/
│       ├── agents_and_mcp.md
│       ├── fine_tuning.md
│       ├── openai_compat_api.md
│       ├── pricing.md
│       ├── quotas_and_limits.md
│       ├── qwen36_release_notes.md
│       ├── sdks_and_integrations.md
│       ├── speechkit_stt.md
│       ├── tokenizer.md
│       └── unused_services.md
└── sessions/
    └── SESSION_22_SUMMARY.md (этот файл)

В корне:
├── ROADMAP.md (обновлён)
└── LEGAL_REVIEW_CHECKLIST.md (новый — список вопросов к юристу перед публичным MVP)
```

---

## Что должен сделать пользователь руками

1. **A2 — кризис-регресс в браузере**: 4 сценария по уровням crisis_level (normal/elevated/high/immediate). Подробно в ROADMAP.md.

2. **Прокликать новый soft-delete flow**:
   - Создать тестовый аккаунт
   - Войти, нажать «Удалить аккаунт»
   - Подтвердить удаление в Dialog
   - Должен вылететь, попасть на `/chat` как гость
   - Залогиниться обратно — должен увидеть `PendingDeletionBanner` сверху
   - Нажать «Отменить удаление» — баннер должен исчезнуть, /api/chat снова работать

3. **(Опционально) Ручной прогон Celery `finalize_pending_deletions`**:
   - Создать тестовый аккаунт
   - Через SQL: `UPDATE users SET deletion_scheduled_at = '2020-01-01' WHERE email = 'test@...'`
   - Запустить функцию из Python REPL
   - Проверить что user удалён, сессии остались с `user_id=NULL`

---

## Открытые вопросы / TODO

### Блок D (следующий)
- ASQ опросник (4 вопроса + 5-й уточняющий) → принудительный `risk_level=immediate` независимо от текста
- PSS-4 (стресс)
- (Опционально) ОСР Разуваевой
- UI: компонент `ASQForm` в чате после 3-5 сообщений

### Блок E (Deploy)
- Подключить Celery beat задачу `finalize_pending_deletions` (раз в сутки)
- Подключить Celery beat для cleanup истёкших refresh-токенов (раз в неделю)
- Запросить увеличение квоты Yandex AI Studio с 10 до 50 одновременных синхронных генераций перед публичным запуском
- VPS Timeweb Cloud + Docker + Nginx + PostgreSQL + Redis + SSL (Let's Encrypt) + CI/CD (GitHub Actions) + Sentry + UptimeRobot + бэкапы

### Блок F (Платежи)
- ЮKassa с `cancel_at_period_end=True` логикой
- Тарифы: Free / «Поддержка» 499₽ / «Двойник» 1999₽
- Юр.статус — финальное решение по `docs/research/grants.md` (самозанятый vs ИП через соавтора в Москве)

### Блок G (после MVP)
- LoRA на собственных диалогах (через 500+ диалогов)
- ElevenLabs TTS + Цифровой Двойник
- Aniemore как оптимизация (CPU embedding-классификатор + LLM analyzer только при пороге)
- Tauri (десктоп) + Capacitor (мобильки)

---

## Что НЕ переделывать (специально)

- ❌ **Не делать LoRA через Yandex AI Studio для Qwen** — у них доступно только для YandexGPT Lite. Qwen-LoRA — только через self-hosted vLLM.
- ❌ **Не делать immediate-delete вместо soft-delete** — пользователь явно попросил 7-day grace period в Сессии 22.
- ❌ **Не удалять сообщения при удалении аккаунта** — это было решение пользователя сохранить data flywheel.
- ❌ **Не помечать subscriptions = cancelled при удалении аккаунта** — нужно `cancel_at_period_end=True`. Иначе пропадёт оплаченный период.
- ❌ **Не использовать `llm.api.cloud.yandex.net`** — старый эндпоинт, Qwen на нём не работает. Только `ai.api.cloud.yandex.net`.
- ❌ **Не делать rule-based crisis detection** — Сессия 18 удалила всё это. Crisis level определяется через `MessageAnalyzer.PerceptionReport.risk_level`.

---

*Файл создан: Сессия 22, Май 2026.
Цель: дать следующему Claude быстрый онбординг.*

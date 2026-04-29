---
name: project-memory
description: "Adapted from aaron-he-zhu/memory-management. Two-layer memory system for AI-Психолог development context: hot cache (current sprint/decisions) + cold storage (full history). Use when starting a new session, when context seems lost, when user references past decisions, or when recording new architectural/design decisions. Trigger on: 'что мы решили', 'на чём остановились', 'запомни', 'сохрани контекст', 'история решений'."
---

# Project Memory: Двухслойная система контекста

> Адаптация паттерна hot cache + cold storage для AI-Психолога.
> ВАЖНО: Этот скилл ЗАМЕНЯЕТ memory-management (SEO). Если вопрос про SEO — этот скилл НЕ для этого.
> Для поиска по истории чатов → используй remembering-conversations (другой механизм).

## Разграничение с другими скиллами
- **project-memory** (этот) = структурированный контекст ПРОЕКТА (решения, TODO, артефакты, стек)
- **remembering-conversations** = поиск по ИСТОРИИ ЧАТОВ (MCP search agent, «что мы обсуждали?»)

## Hot Cache (~100 строк, всегда загружается)
Файл: PROJECT_KNOWLEDGE_BASE.md → секция «Открытые вопросы (TODO)»
- Текущая фаза разработки (1-5)
- Последние 3-5 ключевых решений
- Активные TODO и блокеры
- Статус скиллов

### Формат записи
```
[ДАТА] РЕШЕНИЕ: [описание]
  Обоснование: [почему]
  Связано с: [какие скиллы/модули]
  Статус: ПРИНЯТО / ОТМЕНЕНО / ПЕРЕСМАТРИВАЕТСЯ
```

## Cold Storage (полная история)
PROJECT_KNOWLEDGE_BASE.md → секция «История ключевых решений»
Дополнительно: drawio файлы, docx документы, тексты скиллов.

## Promotion / Demotion
- Тема упоминается 3+ раза за сессию → promote в hot cache
- Тема не упоминалась 3+ сессий → demote в cold
- Блокер решён → archive «решено [дата]»

## Глоссарий проекта
ППП = Первая Психологическая Помощь. SIX C's = модель Фарчи. PVC = Professional Voice Cloning. SER = Speech Emotion Recognition. RAG = Retrieval-Augmented Generation. ФЗ-152 = закон о персданных. ASQ = суицид-скрининг. PSS-4 = стресс-шкала. ОСР = оценка суицидального риска Разуваевой. Двойник = цифровой двойник умершего. Ветка А/Б = мобилизация/стабилизация.

## При старте сессии
1. Прочитай hot cache. 2. «Продолжаем с [контекст]?» 3. В конце → обнови hot cache + knowledge base.

## Связь с экосистемой
Обновления скиллов → cold storage. Решения по стеку → ai-psychologist-core. Путь пользователя → user-journey-engine. Монетизация → monetization-strategy. Визуальная карта → drawio.

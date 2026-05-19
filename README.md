<div align="center">

# Kairos

**AI-сервис первой психологической поддержки**

Сервис для бережной эмоциональной помощи в моменты, когда человеку нужно выговориться, структурировать состояние и получить мягкую поддержку рядом.

<a href="./README.md"><img alt="RU" src="https://img.shields.io/badge/README-RU-2f80ed?style=for-the-badge"></a>
<a href="./README.en.md"><img alt="EN" src="https://img.shields.io/badge/README-EN-111827?style=for-the-badge"></a>
<a href="./README.zh.md"><img alt="中文" src="https://img.shields.io/badge/README-ZH-d97706?style=for-the-badge"></a>

<br><br>

<img alt="Python" src="https://img.shields.io/badge/Python-73.0%25-3776ab?style=flat-square&logo=python&logoColor=white">
<img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-17.5%25-3178c6?style=flat-square&logo=typescript&logoColor=white">
<img alt="HTML" src="https://img.shields.io/badge/HTML-4.7%25-e34f26?style=flat-square&logo=html5&logoColor=white">
<img alt="CSS" src="https://img.shields.io/badge/CSS-4.2%25-663399?style=flat-square&logo=css">

</div>

## О проекте

**Kairos** — это сервис первой психологической поддержки для российского рынка.

Идея проекта: **не заменять психолога, а закрывать промежуток, когда специалиста нет рядом**. Kairos помогает пользователю описать свое состояние, снизить эмоциональное напряжение и получить бережный, структурированный ответ.

Проект разрабатывается с акцентом на безопасность, понятную архитектуру и реалистичные границы AI-помощи.

## Важно

Kairos не является медицинским сервисом, не ставит диагнозы и не заменяет психолога, психотерапевта или врача.

В кризисной или опасной ситуации необходимо обращаться к экстренным службам или профильным специалистам.

## Возможности

- Чат для первой эмоциональной поддержки.
- Анализ настроения и слоя восприятия пользователя.
- Очередь ReflectionAgent для последующей обработки сообщений.
- База знаний и отдельная архитектура “мозга”.
- Backend API на FastAPI.
- Frontend-интерфейс на Next.js.
- Dev-среда с Redis и SQLite из коробки.

## Технологический стек

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | TypeScript, Next.js |
| Styling | CSS, HTML |
| Runtime services | Redis |
| Dev database | SQLite |
| Infrastructure | Docker Compose |

## Быстрый старт

### Сервисы-зависимости

Redis нужен для слоя восприятия: Mood и очереди ReflectionAgent.

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps

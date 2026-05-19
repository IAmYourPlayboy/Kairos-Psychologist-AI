<div align="center">

# Kairos

**An AI-powered first-line psychological support service**

A careful support space for moments when people need to talk, reflect on their emotional state, and receive structured help.

<a href="./README.md"><img alt="RU" src="https://img.shields.io/badge/README-RU-2f80ed?style=for-the-badge"></a>
<a href="./README.en.md"><img alt="EN" src="https://img.shields.io/badge/README-EN-111827?style=for-the-badge"></a>
<a href="./README.zh.md"><img alt="中文" src="https://img.shields.io/badge/README-ZH-d97706?style=for-the-badge"></a>

</div>

## About

**Kairos** is a first-line psychological support service designed for the Russian market.

The project’s core idea is simple: **it does not replace a psychologist, but helps fill the gap when professional support is not immediately available**.

Kairos helps users describe their emotional state, reduce immediate tension, and receive a careful, structured response.

## Important Notice

Kairos is not a medical service. It does not diagnose conditions and does not replace a psychologist, psychotherapist, psychiatrist, or emergency support.

In a crisis or dangerous situation, users should contact emergency services or qualified professionals.

## Features

- AI chat for first-line emotional support.
- Mood and perception layer.
- ReflectionAgent queue for message processing.
- Knowledge base and dedicated “brain” architecture.
- FastAPI backend.
- Next.js frontend.
- Development setup with Redis and SQLite.

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | TypeScript, Next.js |
| Styling | CSS, HTML |
| Runtime services | Redis |
| Development database | SQLite |
| Infrastructure | Docker Compose |

## Getting Started

### Required services

Redis is required for the perception layer: Mood and ReflectionAgent queue.

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps

<div align="center">

# Kairos

**基于 AI 的第一线心理支持服务**

一个温和的支持空间，帮助用户在需要倾诉、整理情绪和获得结构化回应时得到及时陪伴。

<a href="./README.md"><img alt="RU" src="https://img.shields.io/badge/README-RU-2f80ed?style=for-the-badge"></a>
<a href="./README.en.md"><img alt="EN" src="https://img.shields.io/badge/README-EN-111827?style=for-the-badge"></a>
<a href="./README.zh.md"><img alt="中文" src="https://img.shields.io/badge/README-ZH-d97706?style=for-the-badge"></a>

<br><br>

<img alt="Python" src="https://img.shields.io/badge/Python-73.0%25-3776ab?style=flat-square&logo=python&logoColor=white">
<img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-17.5%25-3178c6?style=flat-square&logo=typescript&logoColor=white">
<img alt="HTML" src="https://img.shields.io/badge/HTML-4.7%25-e34f26?style=flat-square&logo=html5&logoColor=white">
<img alt="CSS" src="https://img.shields.io/badge/CSS-4.2%25-663399?style=flat-square&logo=css">

</div>

## 项目简介

**Kairos** 是一个面向俄罗斯市场的第一线心理支持服务。

项目的核心理念是：**它不替代心理咨询师，而是在专业帮助暂时不在身边时，提供一个安全、温和的支持入口**。

Kairos 帮助用户描述自己的情绪状态，降低即时压力，并获得谨慎、结构化的回应。

## 重要说明

Kairos 不是医疗服务，不提供诊断，也不能替代心理咨询师、心理治疗师、精神科医生或紧急救助服务。

在危机或危险情况下，用户应联系紧急服务或合格的专业人士。

## 功能

- 用于第一线情绪支持的 AI 聊天。
- 情绪与感知层分析。
- ReflectionAgent 消息处理队列。
- 知识库与独立的 “brain” 架构。
- 基于 FastAPI 的后端。
- 基于 Next.js 的前端。
- 使用 Redis 和 SQLite 的开发环境。

## 技术栈

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | TypeScript, Next.js |
| Styling | CSS, HTML |
| Runtime services | Redis |
| Development database | SQLite |
| Infrastructure | Docker Compose |

## 快速开始

### 依赖服务

Redis 用于感知层：Mood 和 ReflectionAgent 队列。

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps

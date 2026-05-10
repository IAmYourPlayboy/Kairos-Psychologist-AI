---
name: ai-psychologist-core
description: "Master context skill for the AI-Психолог (Kairos) project — a Russian-language mental health support system with two modes: PFA-mode (first psychological aid using WHO protocols + SIX C's model by Moshe Farchi — the basic chat where Kairos helps the user out of crisis) and Digital Twin module (grief support via temporary personality replica with fade-out). Use PROACTIVELY whenever the user discusses any aspect of this project: architecture, therapy logic, NLP analysis, voice interface, crisis routing, legal compliance (FZ-152), deployment, or testing. Also trigger when user mentions Кайрос, ППП-режим, цифровой двойник, SIX C's, Farchi, Aniemore, Dusha dataset, ElevenLabs integration, or crisis routing for Russia."
---

# AI-Психолог: Master Project Context

## Project Identity
- **Name**: AI-Психолог (AI-Psychologist)
- **Type**: Mental health support system with AI
- **Target**: Russian market (language, culture, legal framework)
- **Core Philosophy**: Not replacing psychologists — filling the void where psychologists are absent. Accessibility argument: 53% of Russians already use AI for psychological support (Yota, 2024-2025).

## Two Modes, One Product
The system operates as a single product with two modes sharing a common technical core (LLM, emotion recognition, voice interface, crisis routing):

### Mode 1: ППП-режим (PFA mode) — базовый чат Кайроса
First psychological aid for crisis situations.
- **Protocols**: WHO PFA (Look, Listen, Link) + Israeli SIX C's (Farchi, 2012-2013)
- **Screening**: ASQ (suicide risk) + PSS-4 (stress level) + ОСР (Razuvaeva modification)
- **Two branches**: 
  - Branch A (Mobilization): Bot = "Headquarters". SIX C's. Action-oriented.
  - Branch B (Stabilization): Bot = "Instructor". WHO protocols. Grounding, breathing, 5-4-3-2-1.
- **Key neuroscience insight**: In crisis, limbic system blocks cognition (amygdala hijack). Don't ask "what do you feel?" — ask cognitive questions: "How many windows do you see?" This activates prefrontal cortex.
- **Text > Voice in crisis**: Typing is active engagement that grounds. Listening is passive.

### Mode 2: Цифровой Двойник (Digital Twin)
Grief support through temporary personality replica of deceased loved one.
- **Concept**: Winnicott's "transitional object" — helps process grief stages, then fades.
- **Voice cloning**: ElevenLabs Professional Voice Cloning from family-provided audio.
- **Personality profile**: Questionnaire from relatives → system prompt.
- **Fade-out mechanism**: Gradual decrease in response frequency, reminders from deceased's perspective ("it's time for me to go"), shift to memories instead of dialogue. Adaptive timeline based on user's state assessment.
- **After fade-out**: Seamless transition back to therapeutic mode.

## Technical Stack (Recommended)
- **Base LLM**: Qwen 2.5 (72B) + LoRA — Apache 2.0, self-hosted on Russian servers (FZ-152)
- **SER (voice)**: Aniemore / HuBERT fine-tuned on Dusha dataset
- **SER (text)**: Aniemore BERT / CEDR corpus (F1 up to 0.95)
- **TTS + Cloning**: ElevenLabs API (PVC, 32+ languages including Russian)
- **STT**: Whisper / Golos (open-source, Russian)
- **RAG**: ChromaDB / Qdrant over PubMed + Cochrane
- **Crisis module**: NLP classifier + ASQ/PSS-4 + routing to 112/МЧС
- **Infrastructure**: vLLM / Ollama + Docker, GPU A100/H100, Russian servers

## NLP: Two-Layer Analysis
See `nlp-emotion-analysis` skill for full architecture. Summary: Layer 1 (linguistic markers = thermometer of distress) × Layer 2 (thematic categories = diagnosis) → matrix drives dynamic system prompt.

## Onboarding Flow
1. Age bracket question (not exact age) → determines routing priorities and language complexity
2. ASQ screening → crisis check
3. PSS-4 → stress level
4. Branch selection (auto by NLP + user confirmation)
5. Handles Russian slang, profanity, typos — see `therapeutic-prompts` and `nlp-emotion-analysis` skills

## Legal Constraints (Russia)
FZ-152: servers in Russia. Foreign SW ban in government. Potential medical device classification. Solution: self-hosted open-source (Qwen 2.5, Apache 2.0), position as navigator not diagnostic tool.

## Crisis Services
See `crisis-routing` skill for full list and age-based routing logic.

## Design Principles
- Quality over speed: think as long as needed, depth matters
- No fake empathy: clear instructions, not performative compassion  
- Bot's key advantage: "full presence effect" — no judgment, no distraction, pausable
- Text is grounding in crisis; voice is for digital twin and optional breathing exercises
- Every session ends with resource list (verified, free, 24/7 services)
- All AI-generated code must have Russian comments (user is not a coder)

## Skill Ecosystem (все скиллы связаны)
```
КАСТОМНЫЕ (9 скиллов):
ai-psychologist-core ← ВЫ ЗДЕСЬ (мастер-контекст)
├── therapeutic-prompts → промпты SIX C's/ВОЗ → СВЯЗАН С crisis-routing, grief-module
├── nlp-emotion-analysis → 2 слоя NLP → СВЯЗАН С therapeutic-prompts (динамический промпт)
├── elevenlabs-voice → TTS + PVC → СВЯЗАН С grief-module (клонирование)
├── grief-module → цифровой двойник → СВЯЗАН С elevenlabs-voice, therapeutic-prompts, nlp-emotion-analysis
├── crisis-routing → кризис 112/МЧС → СВЯЗАН С nlp-emotion-analysis (детекция)
├── user-journey-engine → все пути пользователя → СВЯЗАН СО ВСЕМИ
├── crossplatform-frontend → React/Next.js → Electron → Capacitor
├── monetization-strategy → бизнес-модель → СВЯЗАН С user-journey-engine
└── project-memory → контекст между сессиями

ЗАГРУЖЕННЫЕ (5 скиллов — установлены пользователем):
├── systematic-debugging → 4-фазная отладка (для ML-багов)
├── remembering-conversations → поиск по истории сессий (НЕ путать с project-memory!)
├── github-repo-management → CI/CD, issues, releases
├── typescript-advanced-types → типизация TypeScript для Next.js фронтенда (717 строк!)
├── webapp-testing → Playwright тесты UI (chat flow, crisis banner)
└── ⚠️ memory-management (SEO) → ЗАМЕНЁН на project-memory. УДАЛИТЬ если мешает.

ВНЕШНИЕ (10 скиллов, установить):
├── HF Model Trainer → LoRA fine-tuning → ДЛЯ nlp-emotion-analysis
├── PEFT → LoRA/QLoRA методы → ДЛЯ nlp-emotion-analysis
├── RAG Architect → чанкинг, embeddings → ДЛЯ therapeutic-prompts (база знаний)
├── Chroma RAG → векторная БД → ДЛЯ RAG Architect
├── Senior Prompt Engineer → оптимизация → ДЛЯ therapeutic-prompts
├── Mistral Security → PII, injection → ДЛЯ crisis-routing (защита данных)
├── Senior DevOps → Docker, CI/CD → ДЛЯ crossplatform-frontend
├── Senior Backend → FastAPI → ДЛЯ crossplatform-frontend
├── TDD (Superpowers) → тесты → ДЛЯ systematic-debugging
└── NeMo Guardrails → безопасность ИИ → ДЛЯ crisis-routing, therapeutic-prompts
```

## Production Architecture (как скиллы → код)
Skills = инструменты разработки (живут в Claude). Продукт = код на серверах.
- therapeutic-prompts → файлы промптов (JSON/YAML) + модуль prompt_engine.py
- nlp-emotion-analysis → модуль emotion_pipeline.py + конфиг маркеров
- elevenlabs-voice → модуль voice_service.py + клиент ElevenLabs API
- grief-module → модуль digital_twin.py + шаблоны анкет
- crisis-routing → модуль crisis_detector.py + JSON с номерами
- crossplatform-frontend → Next.js приложение (веб → Electron → Capacitor)
- Backend: FastAPI + vLLM + Qdrant → Docker Compose → сервер РФ

---
name: nlp-emotion-analysis
description: "Skill for building the two-layer NLP emotion analysis pipeline for AI-Психолог. Covers linguistic marker detection (absolutist lexicon, message patterns, typing speed), thematic categorization (loss, guilt, hopelessness, fear), and the theme×intensity matrix that drives dynamic system prompts. Use when working with Aniemore, Dusha dataset, CEDR corpus, HuBERT models, distress classification, or Russian-language sentiment analysis. Also trigger for fine-tuning emotion models, building crisis classifiers, or designing the validation-before-escalation flow."
---

# NLP Emotion Analysis Pipeline

## Architecture: Two Parallel Classifiers

### Layer 1: Distress Markers (0.0 → 1.0 score)
Detects HOW the person communicates. Linguistic and behavioral signals:

**Lexical markers (Russian-specific)**:
- Absolutist words: "никогда", "всегда", "никто", "ничего", "всё пропало"
- Hopelessness lexicon: "бессмысленно", "невозможно", "конец", "не вижу выхода"  
- Tunnel vision: "тяжёлые" metaphors, extreme qualifiers
- Self-referencing shift: drop from "я" to impersonal forms ("так бывает", "людям плохо")
- Absence of future tense verbs (no temporal perspective)

**Structural markers**:
- Message shortening over time (progressive disengagement)
- Loss of punctuation and capitalization
- ALL CAPS (agitation/panic)
- Increasing typos (psychophysiological exhaustion)
- Response latency changes (long pauses = shutdown; rapid-fire = panic)

**Behavioral markers (chat-specific)**:
- Typing speed acceleration + CAPS = auto-switch to brief instrumental style
- Extended silence after emotional content = check-in trigger
- Repeated phrases = rumination signal

### Layer 2: Thematic Categories
Detects WHAT the person discusses. Categories:
- **Утрата** (Loss) → ACT framework + potential Digital Twin offer
- **Вина** (Guilt) → CBT cognitive restructuring  
- **Одиночество** (Loneliness) → Connection-focused intervention
- **Потеря смысла** (Loss of meaning) → ACT values work
- **Безысходность** (Hopelessness) → HIGH PRIORITY, combine with Layer 1
- **Страх** (Fear) → SIX C's Challenge + grounding
- **Гнев** (Anger) → DBT emotion regulation
- **Тревога** (Anxiety) → Breathing + CBT thought records

### Intersection Matrix
```
Theme × Intensity → Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hopelessness + High (>0.7) → RED ZONE → Crisis routing
Loss + Low (<0.3)          → Normal grief → Gentle ACT
Loss + High (>0.7)         → Acute grief → Stabilization + crisis check
Fear + High (>0.7)         → SIX C's mobilization
Anxiety + Medium (0.3-0.7) → Stabilization branch
Guilt + High (>0.7)        → CBT restructuring + suicide risk check
Loneliness + High (>0.7)   → Connect to live resources + check isolation
Anger + High (>0.7)        → DBT regulation, check for self-harm
Any theme + Score >0.85    → Immediate validation + crisis check
```

## Russian Slang and Typo Tolerance
People in distress write with typos, no punctuation, slang, and profanity.
The model MUST recognize these as distress markers, not noise:
- "пздц", "капец", "мне п***ц" → high distress signal
- "хз что делать" → helplessness marker
- "всё, я больше не могу" without punctuation → same weight as grammatically correct version
- ALL CAPS + rapid messages → panic indicator, switch to brief style
- Emojis used sarcastically ("всё хорошо 🙃") → contradiction signal, elevated monitoring

## Models & Datasets (Russian)

### Speech Emotion Recognition (SER)
- **Aniemore** (recommended): WavLM for voice, BERT-Tiny for text, WavLM+BERT Fusion for multimodal. 7 emotions (anger, disgust, fear, happiness, interest, sadness, neutral). F1 ~75%. Python library, pip install.
- **HuBERT-large-Dusha**: HuggingFace model fine-tuned on Dusha. 5 categories (neutral, angry, positive, sad, other).
- **Dusha dataset**: 350 hours, 300K+ recordings. Acted (pre-training) + real podcasts (fine-tuning). GitHub open.

### Text Emotion Recognition  
- **CEDR** (Corpus for Emotions Detecting in Russian): ~10K sentences, 6 classes. ELMo embeddings → F1 up to 0.95.
- **Aniemore Text**: BERT-Tiny models for Russian text emotion. Ready on HuggingFace.

### Crisis Detection
- **Dreaddit**: ~3500 posts, stress detection (EN, needs translation/adaptation)
- **SDCNL**: Reddit posts for suicide risk classification (EN)
- **Koko**: 500K posts annotated for cognitive distortions (EN)
- Fine-tuning benchmark: 91% emotion classification, 80% mental state detection (Kermani et al., 2025)

## Technical Architecture
Two classifiers run in parallel, not sequentially:
- **Distress classifier**: Lightweight model (rule-based lexicon + BERT-based score). Runs on every message. Output: float 0.0-1.0.
- **Theme classifier**: LLM-based (via system prompt instruction to Qwen 2.5). Runs every 3-5 messages or on significant content change. Output: one of 8 categories + confidence.
- Both outputs feed into the theme×intensity matrix, which updates the dynamic system prompt.
- Distress score also directly controls response style (score > 0.7 → brief instrumental mode).

## Implementation Notes
- Real-time analysis via dynamic system prompt updates every N messages
- Validation before escalation: "Мне кажется, тебе сейчас очень тяжело. Я прав?"
- User confirmation required before crisis routing (except extreme cases)
- All processing must happen on Russian servers (FZ-152)

## Связь с экосистемой
- Выход матрицы → `therapeutic-prompts` (обновляет динамический промпт)
- Красная зона → `crisis-routing` (запускает эскалацию)
- Тема «утрата» → `grief-module` (предложение двойника)
- Баги NLP (неверная классификация) → `systematic-debugging` (4-фазный дебаг)
- Fine-tuning моделей → внешние скиллы HF Model Trainer + PEFT

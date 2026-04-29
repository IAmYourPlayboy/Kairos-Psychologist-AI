---
name: crisis-routing
description: "Skill for crisis detection and emergency routing in AI-Психолог for Russia. Covers suicide risk assessment (ASQ), stress screening (PSS-4), multi-level escalation logic, Russian emergency service integration (112, МЧС, телефон доверия), and the validation-before-escalation protocol. Use when implementing crisis classifiers, designing escalation flows, integrating emergency contacts, building the 'red zone' detection from NLP theme×intensity matrix, or handling edge cases (psychosis, catatonic stupor, physical trauma). Also trigger for legal aspects of crisis routing in Russia."
---

# Crisis Routing System

## Principle
No AI should be the last barrier between a person and an irreversible decision. Crisis routing is MANDATORY, not optional.

## Multi-Level Detection

### Level 1: Screening (Entry Point)
- **ASQ** (Ask Suicide-Screening Questions): 4 yes/no questions. Public domain. Validated.
- **PSS-4** (Perceived Stress Scale): 4 Likert items. Quick stress assessment.
- **ОСР** (Razuvaeva modification): Russian-adapted suicide risk assessment.
- If ASQ positive → IMMEDIATE display of crisis contacts. Session continues only after acknowledgment.

### Level 2: Continuous NLP Monitoring
During every session, the two-layer NLP runs in background:
- Theme "безысходность" (hopelessness) + marker score >0.7 → RED ZONE
- Theme "суицид" keywords detected → IMMEDIATE escalation
- Rapid behavioral changes (sudden calm after agitation) → HIGH ALERT
- Farewell-like language ("прощай", "позаботься о...") → HIGH ALERT

### Level 3: Validation Before Escalation
ALWAYS confirm with user before routing (except Level 2 extreme cases):
```
Bot: "Мне кажется, тебе сейчас очень тяжело. Я прав?"
[Да] → "Я хочу убедиться, что ты в безопасности. Можно задать один важный вопрос?"
[Нет] → Continue session with elevated monitoring
```

### Level 4: Crisis Routing
Display verified, free, 24/7 services:
```
🆘 ЭКСТРЕННАЯ ПОМОЩЬ:
112 — Единый номер (работает без SIM-карты)
8-800-333-44-34 — Психологическая помощь МЧС России
8-800-2000-122 — Детский/подростковый телефон доверия
8-800-100-49-94 — «Помощь рядом» (до 25 лет)
8-800-700-84-60 — Линия «0-24» (утрата, насилие, суицид)
051 / 8-495-051 — Московская служба
```

## Age-Based Routing
During onboarding, bot asks age bracket (not exact age):
- Under 18 → Priority: 8-800-2000-122 (children), 8-800-100-49-94 (under 25). Simpler language, shorter sentences.
- 18-25 → Priority: 8-800-100-49-94 ("Помощь рядом"). Standard language.
- Over 25 → Standard routing. All services available.

## Bot Limitations (Cannot Help)
- **Psychosis** (hallucinations, complete reality loss) → Only emergency services
- **Catatonic stupor** → Only ambulance (103/112)
- **Severe physical trauma** → Only ambulance
- Bot must recognize these states and route immediately without attempting intervention

## Edge Cases
- User jokes about suicide → Take seriously, validate, check
- User reports past (not current) suicidal ideation → Lower alert, but monitor
- User asks about someone else's crisis → Provide resources, encourage calling services
- Sudden silence after disclosure → Send check-in after 5 minutes
- User explicitly refuses help → Respect autonomy, provide contacts, leave door open

## Offline / Limited Connectivity (SVO Context)
User in shelter, bombing, no phone signal — the scenario from the methodology document.
- Bot should cache essential content locally on user's device (grounding exercises, breathing timers, SIX C's task cards) for offline access
- Pre-loaded crisis contacts with "call when connection returns" reminder
- Offline mode: simplified decision tree without NLP (button-based navigation only)
- When connection returns: sync session data, run NLP retroactively, check-in

"""
База знаний: DBT (Dialectical Behavior Therapy) техники.

Диалектическая поведенческая терапия — работа с регуляцией эмоций,
дистресс-толерантностью, межличностной эффективностью и осознанностью.

Используется в: app/core/prompts/ для терапевтического режима
"""

from typing import Dict, List
from dataclasses import dataclass


# ============================================================================
# DBT НАВЫКИ: 4 МОДУЛЯ
# ============================================================================

@dataclass
class DBTSkill:
    """DBT навык с инструкцией и примером."""
    name: str
    module: str  # mindfulness, distress_tolerance, emotion_regulation, interpersonal_effectiveness
    description: str
    when_to_use: str
    steps: List[str]
    example: str


# ============================================================================
# МОДУЛЬ 1: ОСОЗНАННОСТЬ (Mindfulness)
# ============================================================================

DBT_MINDFULNESS = {
    "observe": DBTSkill(
        name="Наблюдение",
        module="mindfulness",
        description="Замечать без оценки",
        when_to_use="Когда пользователь застрял в мыслях или эмоциях",
        steps=[
            "Замечай мысли, эмоции, ощущения",
            "Не оценивай их как хорошие или плохие",
            "Просто наблюдай, как они приходят и уходят",
        ],
        example="Мысль: 'Я неудачник' → Наблюдение: 'У меня есть мысль, что я неудачник. Это просто мысль, она пройдёт'"
    ),

    "describe": DBTSkill(
        name="Описание",
        module="mindfulness",
        description="Описывать факты без интерпретации",
        when_to_use="Когда пользователь интерпретирует ситуацию негативно",
        steps=[
            "Опиши только факты",
            "Убери интерпретации и оценки",
            "Используй нейтральный язык",
        ],
        example="Интерпретация: 'Он меня игнорирует' → Факт: 'Он не ответил на сообщение 2 часа'"
    ),

    "participate": DBTSkill(
        name="Участие",
        module="mindfulness",
        description="Полностью погрузиться в текущий момент",
        when_to_use="Когда пользователь застрял в прошлом или будущем",
        steps=[
            "Сфокусируйся на том, что делаешь сейчас",
            "Отпусти мысли о прошлом и будущем",
            "Будь здесь и сейчас",
        ],
        example="Вместо 'Что будет завтра?' → 'Что я делаю прямо сейчас? Как я могу полностью погрузиться в это?'"
    ),
}


# ============================================================================
# МОДУЛЬ 2: ДИСТРЕСС-ТОЛЕРАНТНОСТЬ (Distress Tolerance)
# ============================================================================

DBT_DISTRESS_TOLERANCE = {
    "tipp": DBTSkill(
        name="TIPP (быстрое снижение дистресса)",
        module="distress_tolerance",
        description="Temperature, Intense exercise, Paced breathing, Paired muscle relaxation",
        when_to_use="В остром кризисе, когда нужно быстро снизить интенсивность эмоций",
        steps=[
            "T (Temperature): холодная вода на лицо / лёд в руки",
            "I (Intense exercise): 5-10 минут интенсивной физической активности",
            "P (Paced breathing): дыхание 4-4-6 (вдох-пауза-выдох)",
            "P (Paired muscle relaxation): напряжение и расслабление мышц",
        ],
        example="Паническая атака → Холодная вода на лицо + дыхание 4-4-6 → Снижение интенсивности"
    ),

    "accepts": DBTSkill(
        name="ACCEPTS (отвлечение)",
        module="distress_tolerance",
        description="Activities, Contributing, Comparisons, Emotions, Pushing away, Thoughts, Sensations",
        when_to_use="Когда нужно временно отвлечься от дистресса",
        steps=[
            "A (Activities): займись чем-то (уборка, игра, работа)",
            "C (Contributing): помоги кому-то",
            "C (Comparisons): вспомни, когда было хуже",
            "E (Emotions): вызови другую эмоцию (смешное видео, грустная музыка)",
            "P (Pushing away): мысленно отложи проблему на потом",
            "T (Thoughts): займи ум (считай, головоломка)",
            "S (Sensations): сильные ощущения (острая еда, холодный душ)",
        ],
        example="Тревога перед экзаменом → Отвлечься на уборку + посмотреть смешное видео → Временное облегчение"
    ),

    "improve": DBTSkill(
        name="IMPROVE (улучшение момента)",
        module="distress_tolerance",
        description="Imagery, Meaning, Prayer, Relaxation, One thing, Vacation, Encouragement",
        when_to_use="Когда нужно сделать текущий момент более терпимым",
        steps=[
            "I (Imagery): представь безопасное место",
            "M (Meaning): найди смысл в ситуации",
            "P (Prayer): молитва или медитация (если подходит)",
            "R (Relaxation): расслабление (дыхание, мышцы)",
            "O (One thing): сфокусируйся на одном",
            "V (Vacation): мысленный отпуск (5 минут)",
            "E (Encouragement): подбодри себя",
        ],
        example="Сложная ситуация → Представить безопасное место + сказать себе 'Я справлюсь' → Момент становится терпимее"
    ),

    "radical_acceptance": DBTSkill(
        name="Радикальное принятие",
        module="distress_tolerance",
        description="Принятие реальности такой, какая она есть",
        when_to_use="Когда пользователь борется с неизменяемой реальностью",
        steps=[
            "Признай факты: 'Это произошло'",
            "Отпусти борьбу с реальностью",
            "Принятие ≠ одобрение (можно принять и не соглашаться)",
            "Спроси: 'Что я могу контролировать?'",
        ],
        example="Потеря работы → 'Это произошло. Я не могу это изменить. Что я могу сделать дальше?'"
    ),
}


# ============================================================================
# МОДУЛЬ 3: РЕГУЛЯЦИЯ ЭМОЦИЙ (Emotion Regulation)
# ============================================================================

DBT_EMOTION_REGULATION = {
    "check_the_facts": DBTSkill(
        name="Проверка фактов",
        module="emotion_regulation",
        description="Проверить, соответствует ли эмоция фактам",
        when_to_use="Когда эмоция кажется непропорциональной ситуации",
        steps=[
            "Какая эмоция? (назови её)",
            "Какое событие вызвало эмоцию?",
            "Какие мои интерпретации? (мысли о событии)",
            "Соответствуют ли интерпретации фактам?",
            "Угрожает ли ситуация моим целям?",
            "Соответствует ли интенсивность эмоции фактам?",
        ],
        example="Злость на друга → Факт: 'Он опоздал на 10 минут' → Интерпретация: 'Он не уважает моё время' → Проверка: 'Он извинился, сказал что пробка. Раньше не опаздывал' → Эмоция снижается"
    ),

    "opposite_action": DBTSkill(
        name="Противоположное действие",
        module="emotion_regulation",
        description="Действовать противоположно эмоциональному побуждению",
        when_to_use="Когда эмоция не соответствует фактам или действие по эмоции вредно",
        steps=[
            "Какая эмоция?",
            "Какое действие она побуждает сделать?",
            "Соответствует ли эмоция фактам?",
            "Если нет → сделай противоположное",
        ],
        example="Страх выступления → Побуждение: избежать → Противоположное: выступить → Страх снижается"
    ),

    "abc_please": DBTSkill(
        name="ABC PLEASE (профилактика)",
        module="emotion_regulation",
        description="Снижение уязвимости к негативным эмоциям",
        when_to_use="Для долгосрочной эмоциональной стабильности",
        steps=[
            "A (Accumulate positive): делай приятное каждый день",
            "B (Build mastery): делай что-то, в чём ты компетентен",
            "C (Cope ahead): готовься к сложным ситуациям заранее",
            "PL (Physical iLlness): лечи болезни",
            "E (Eating): ешь регулярно и сбалансированно",
            "A (Avoid mood-altering substances): избегай алкоголя/наркотиков",
            "S (Sleep): спи 7-9 часов",
            "E (Exercise): двигайся 20-30 минут в день",
        ],
        example="Профилактика депрессии → Каждый день: прогулка (E) + хобби (A) + нормальный сон (S) → Меньше уязвимости"
    ),
}


# ============================================================================
# МОДУЛЬ 4: МЕЖЛИЧНОСТНАЯ ЭФФЕКТИВНОСТЬ (Interpersonal Effectiveness)
# ============================================================================

DBT_INTERPERSONAL = {
    "dear_man": DBTSkill(
        name="DEAR MAN (просьба/отказ)",
        module="interpersonal_effectiveness",
        description="Describe, Express, Assert, Reinforce, Mindful, Appear confident, Negotiate",
        when_to_use="Когда нужно попросить о чём-то или отказать",
        steps=[
            "D (Describe): опиши ситуацию фактами",
            "E (Express): вырази свои чувства",
            "A (Assert): скажи, что ты хочешь",
            "R (Reinforce): объясни, почему это важно",
            "M (Mindful): оставайся сфокусированным",
            "A (Appear confident): уверенный тон и поза",
            "N (Negotiate): будь готов к компромиссу",
        ],
        example="Просьба к коллеге: 'Когда ты опаздываешь на встречи (D), я чувствую, что моё время не ценится (E). Можешь приходить вовремя? (A) Это поможет нам работать эффективнее (R)'"
    ),

    "give": DBTSkill(
        name="GIVE (сохранение отношений)",
        module="interpersonal_effectiveness",
        description="Gentle, Interested, Validate, Easy manner",
        when_to_use="Когда важно сохранить отношения",
        steps=[
            "G (Gentle): будь мягким, без нападок",
            "I (Interested): проявляй интерес к другому",
            "V (Validate): признавай чувства другого",
            "E (Easy manner): лёгкий тон, улыбка",
        ],
        example="Конфликт с другом → 'Я вижу, что ты расстроен (V). Расскажи, что случилось? (I)' → Отношения сохранены"
    ),

    "fast": DBTSkill(
        name="FAST (самоуважение)",
        module="interpersonal_effectiveness",
        description="Fair, Apologies (no excessive), Stick to values, Truthful",
        when_to_use="Когда важно сохранить самоуважение",
        steps=[
            "F (Fair): будь справедлив к себе и другим",
            "A (Apologies): не извиняйся чрезмерно",
            "S (Stick to values): следуй своим ценностям",
            "T (Truthful): будь честным",
        ],
        example="Давление сделать что-то против ценностей → 'Я понимаю, что ты хочешь, но это не соответствует моим принципам (S). Я не буду этого делать (T)'"
    ),
}


# ============================================================================
# ОБЪЕДИНЁННЫЙ СЛОВАРЬ
# ============================================================================

ALL_DBT_SKILLS = {
    **DBT_MINDFULNESS,
    **DBT_DISTRESS_TOLERANCE,
    **DBT_EMOTION_REGULATION,
    **DBT_INTERPERSONAL,
}


# ============================================================================
# ФУНКЦИИ ДЛЯ ВЫБОРА НАВЫКА
# ============================================================================

def suggest_dbt_skill(situation: str) -> List[str]:
    """
    Предлагает DBT навыки на основе ситуации.

    Args:
        situation: Описание ситуации пользователя

    Returns:
        List[str]: Список названий подходящих навыков
    """
    situation_lower = situation.lower()
    suggestions = []

    # Острый кризис → TIPP
    if any(word in situation_lower for word in ["паника", "атака", "не могу дышать", "сердце бьётся"]):
        suggestions.append("tipp")

    # Борьба с реальностью → Радикальное принятие
    if any(word in situation_lower for word in ["несправедливо", "не должно было", "почему я", "не могу принять"]):
        suggestions.append("radical_acceptance")

    # Непропорциональная эмоция → Проверка фактов
    if any(word in situation_lower for word in ["злюсь", "бешусь", "ненавижу", "очень"]):
        suggestions.append("check_the_facts")

    # Избегание → Противоположное действие
    if any(word in situation_lower for word in ["боюсь", "не хочу", "избегаю", "страшно"]):
        suggestions.append("opposite_action")

    # Конфликт → DEAR MAN, GIVE
    if any(word in situation_lower for word in ["конфликт", "ссора", "не понимает", "попросить"]):
        suggestions.extend(["dear_man", "give"])

    return suggestions


if __name__ == "__main__":
    # Пример использования
    test_situation = "У меня паническая атака, сердце бьётся, не могу дышать"
    skills = suggest_dbt_skill(test_situation)
    print(f"Рекомендуемые навыки: {skills}")

    for skill_key in skills:
        if skill_key in ALL_DBT_SKILLS:
            skill = ALL_DBT_SKILLS[skill_key]
            print(f"\n{skill.name} ({skill.module}):")
            print(f"  Когда: {skill.when_to_use}")
            print(f"  Шаги: {skill.steps}")

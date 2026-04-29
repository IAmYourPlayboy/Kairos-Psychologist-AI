"""Сборщик итогового системного промпта из компонентов."""

from typing import Optional, Dict, Any, List, Tuple

from app.core.prompts.base import PROMPT as BASE_PROMPT
from app.core.prompts.branch_a import PROMPT as BRANCH_A_PROMPT
from app.core.prompts.branch_b import PROMPT as BRANCH_B_PROMPT
from app.core.prompts.crisis import CRISIS_PROMPTS

# Импорт модулей базы знаний
from app.core.knowledge.who_pfa import suggest_pfa_technique, get_pfa_technique
from app.core.knowledge.sfbt_mi import suggest_sfbt_technique, get_sfbt_technique, get_mi_by_category
from app.core.knowledge.cbt_techniques import get_distortion_by_keywords, COGNITIVE_DISTORTIONS
from app.core.knowledge.dbt_skills import suggest_dbt_skill, ALL_DBT_SKILLS
from app.core.knowledge.act_processes import suggest_act_process, ACT_PROCESSES

# Импорт динамического маршрутизатора
from app.core.therapy_router import TherapyRouter, TherapyState, TherapyNode

_BRANCH_PROMPTS: dict[str, str] = {
    "A": BRANCH_A_PROMPT,
    "B": BRANCH_B_PROMPT,
}


def build_system_prompt(
    branch: str,
    crisis_level: str = "normal",
    user_message: Optional[str] = None,
    therapy_mode: Optional[str] = None,
    distress_score: Optional[float] = None,
    emotion: Optional[str] = None,
    theme: Optional[str] = None,
    use_router: bool = True,
) -> str:
    """Собрать итоговый системный промпт с динамическими техниками.

    Args:
        branch: "A" (мобилизация, SIX C's) или "B" (стабилизация, ВОЗ PFA).
        crisis_level: "normal", "elevated", "high" или "immediate".
        user_message: Сообщение пользователя для подбора техник (опционально).
        therapy_mode: Режим терапии: "cbt", "dbt", "act", "sfbt" (опционально).
        distress_score: Уровень дистресса 0.0-1.0 (опционально, для router).
        emotion: Текущая эмоция (опционально, для router).
        theme: Тема диалога (опционально, для router).
        use_router: Использовать динамический маршрутизатор (по умолчанию True).

    Returns:
        Полный системный промпт, готовый для отправки в LLM.
    """
    branch = branch.upper()
    if branch not in _BRANCH_PROMPTS:
        raise ValueError(f"Неизвестная ветка: {branch}. Допустимые: A, B")

    parts = [BASE_PROMPT, _BRANCH_PROMPTS[branch]]

    # Добавить кризисный промпт
    crisis_prompt = CRISIS_PROMPTS.get(crisis_level)
    if crisis_prompt:
        parts.append(crisis_prompt)

    # Добавить динамические техники
    if user_message:
        if use_router and distress_score is not None:
            # Использовать динамический маршрутизатор
            dynamic_techniques = _build_router_techniques(
                user_message, distress_score, emotion, theme
            )
        else:
            # Использовать статический подбор техник
            dynamic_techniques = _build_dynamic_techniques(
                user_message, crisis_level, therapy_mode
            )

        if dynamic_techniques:
            parts.append(dynamic_techniques)

    return "\n\n".join(parts)


def _build_dynamic_techniques(
    user_message: str,
    crisis_level: str,
    therapy_mode: Optional[str] = None,
) -> str:
    """Построить блок с рекомендуемыми техниками на основе контекста.

    Args:
        user_message: Сообщение пользователя.
        crisis_level: Уровень кризиса.
        therapy_mode: Режим терапии (если задан).

    Returns:
        Строка с рекомендуемыми техниками или пустая строка.
    """
    techniques = []

    # === КРИЗИСНЫЙ РЕЖИМ: ВОЗ PFA ===
    if crisis_level in ["elevated", "high", "immediate"]:
        pfa_techniques = suggest_pfa_technique(user_message)
        if pfa_techniques:
            techniques.append("## РЕКОМЕНДУЕМЫЕ ТЕХНИКИ (ВОЗ PFA)")
            for tech_name in pfa_techniques[:2]:  # Максимум 2 техники
                tech = get_pfa_technique(tech_name)
                if tech:
                    techniques.append(f"\n### {tech.name}")
                    techniques.append(f"**Когда использовать**: {tech.when_to_use}")
                    techniques.append("**Шаги**:")
                    for step in tech.steps:
                        techniques.append(f"- {step}")
                    techniques.append(f"\n**Пример**: {tech.example}")

    # === ТЕРАПЕВТИЧЕСКИЙ РЕЖИМ ===
    elif therapy_mode or crisis_level == "normal":
        # CBT: Когнитивные искажения
        if therapy_mode == "cbt" or not therapy_mode:
            distortions = get_distortion_by_keywords(user_message)
            if distortions:
                techniques.append("## ОБНАРУЖЕННЫЕ КОГНИТИВНЫЕ ИСКАЖЕНИЯ (CBT)")
                for dist_key in distortions[:2]:  # Максимум 2 искажения
                    dist = COGNITIVE_DISTORTIONS[dist_key]
                    techniques.append(f"\n### {dist.name}")
                    techniques.append(f"**Описание**: {dist.description}")
                    techniques.append(f"**Техника переформулирования**: {dist.reframe_technique}")
                    techniques.append(f"**Пример**: {dist.reframe_example}")

        # DBT: Навыки
        if therapy_mode == "dbt" or not therapy_mode:
            dbt_skills = suggest_dbt_skill(user_message)
            if dbt_skills:
                techniques.append("\n## РЕКОМЕНДУЕМЫЕ НАВЫКИ (DBT)")
                for skill_name in dbt_skills[:2]:  # Максимум 2 навыка
                    skill = ALL_DBT_SKILLS.get(skill_name)
                    if skill:
                        techniques.append(f"\n### {skill.name}")
                        techniques.append(f"**Когда использовать**: {skill.when_to_use}")
                        techniques.append("**Шаги**:")
                        for step in skill.steps:
                            techniques.append(f"- {step}")

        # ACT: Процессы
        if therapy_mode == "act" or not therapy_mode:
            act_processes = suggest_act_process(user_message)
            if act_processes:
                techniques.append("\n## РЕКОМЕНДУЕМЫЕ ПРОЦЕССЫ (ACT)")
                for proc_name in act_processes[:2]:  # Максимум 2 процесса
                    proc = ACT_PROCESSES.get(proc_name)
                    if proc:
                        techniques.append(f"\n### {proc.name}")
                        techniques.append(f"**Когда использовать**: {proc.when_to_use}")
                        techniques.append(f"**Метафора**: {proc.metaphor}")

        # SFBT: Техники
        if therapy_mode == "sfbt" or not therapy_mode:
            sfbt_techniques = suggest_sfbt_technique(user_message)
            if sfbt_techniques:
                techniques.append("\n## РЕКОМЕНДУЕМЫЕ ТЕХНИКИ (SFBT)")
                for tech_name in sfbt_techniques[:1]:  # Максимум 1 техника
                    tech = get_sfbt_technique(tech_name)
                    if tech:
                        techniques.append(f"\n### {tech.name}")
                        techniques.append(f"**Когда использовать**: {tech.when_to_use}")
                        techniques.append(f"**Пример вопроса**: {tech.example_question}")

    return "\n".join(techniques) if techniques else ""


def _build_router_techniques(
    user_message: str,
    distress_score: float,
    emotion: Optional[str] = None,
    theme: Optional[str] = None,
) -> str:
    """Построить блок с техниками через динамический маршрутизатор.

    Args:
        user_message: Сообщение пользователя.
        distress_score: Уровень дистресса (0.0-1.0).
        emotion: Текущая эмоция.
        theme: Тема диалога.

    Returns:
        Строка с маршрутом терапевтических техник.
    """
    # Создать маршрутизатор
    router = TherapyRouter()

    # Создать начальное состояние
    initial_state = TherapyState(
        distress_score=distress_score,
        emotion=emotion,
        theme=theme,
        current_goal=None,
        history=[],
        attempts=0,
        max_attempts=5,
    )

    # Построить маршрут
    route = router.route(initial_state, user_message)

    if not route:
        return ""

    # Форматировать маршрут для промпта
    techniques = []
    techniques.append("## РЕКОМЕНДУЕМЫЙ МАРШРУТ ТЕРАПЕВТИЧЕСКИХ ТЕХНИК")
    techniques.append(
        f"\n**Текущее состояние**: distress={distress_score:.2f}, "
        f"эмоция={emotion or 'не определена'}, тема={theme or 'не определена'}"
    )
    techniques.append(f"**Цель**: {initial_state.current_goal.value if initial_state.current_goal else 'определяется динамически'}")
    techniques.append("\n**Маршрут** (применять последовательно, оценивая эффективность после каждой):")

    for i, (technique_id, node) in enumerate(route, 1):
        techniques.append(f"\n### {i}. {node.name} ({node.category.value.upper()})")
        techniques.append(f"**Цели**: {', '.join([g.value for g in node.goals])}")

        # Получить детали техники из базы знаний
        details = _get_technique_details(technique_id, node.category.value)
        if details:
            techniques.append(f"**Как применить**: {details}")

    techniques.append(
        "\n**Важно**: После каждой техники оцени, снизился ли дистресс. "
        "Если цель не достигнута — переходи к следующей технике в маршруте. "
        "Если техника не подходит пользователю — адаптируй или предложи альтернативу из того же узла графа."
    )

    return "\n".join(techniques)


def _get_technique_details(technique_id: str, category: str) -> Optional[str]:
    """Получить детали техники из базы знаний.

    Args:
        technique_id: ID техники.
        category: Категория (pfa, cbt, dbt, act, sfbt).

    Returns:
        Строка с деталями техники или None.
    """
    # Маппинг ID техник на функции получения деталей
    if category == "pfa":
        # Извлечь имя техники из ID (например, "pfa_5_4_3_2_1" -> "5_4_3_2_1")
        tech_name = technique_id.replace("pfa_", "")
        tech = get_pfa_technique(tech_name)
        if tech:
            return f"{tech.when_to_use}. Шаги: {', '.join(tech.steps[:3])}..."

    elif category == "dbt":
        tech_name = technique_id.replace("dbt_", "")
        tech = ALL_DBT_SKILLS.get(tech_name)
        if tech:
            return f"{tech.when_to_use}. Шаги: {', '.join(tech.steps[:3])}..."

    elif category == "act":
        tech_name = technique_id.replace("act_", "")
        tech = ACT_PROCESSES.get(tech_name)
        if tech:
            return f"{tech.when_to_use}. Метафора: {tech.metaphor[:100]}..."

    elif category == "cbt":
        return "Помочь пользователю выявить когнитивное искажение и переформулировать мысль."

    elif category == "sfbt":
        tech_name = technique_id.replace("sfbt_", "")
        tech = get_sfbt_technique(tech_name)
        if tech:
            return f"{tech.when_to_use}. Пример вопроса: {tech.example_question[:100]}..."

    return None


def get_suggested_techniques(
    user_message: str,
    crisis_level: str = "normal",
    therapy_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Получить рекомендуемые техники без построения промпта.

    Полезно для API-ответов или логирования.

    Args:
        user_message: Сообщение пользователя.
        crisis_level: Уровень кризиса.
        therapy_mode: Режим терапии (если задан).

    Returns:
        Словарь с рекомендуемыми техниками по категориям.
    """
    result = {
        "crisis_level": crisis_level,
        "therapy_mode": therapy_mode,
        "techniques": {},
    }

    # Кризисный режим
    if crisis_level in ["elevated", "high", "immediate"]:
        result["techniques"]["pfa"] = suggest_pfa_technique(user_message)

    # Терапевтический режим
    else:
        if therapy_mode == "cbt" or not therapy_mode:
            result["techniques"]["cbt_distortions"] = get_distortion_by_keywords(user_message)

        if therapy_mode == "dbt" or not therapy_mode:
            result["techniques"]["dbt_skills"] = suggest_dbt_skill(user_message)

        if therapy_mode == "act" or not therapy_mode:
            result["techniques"]["act_processes"] = suggest_act_process(user_message)

        if therapy_mode == "sfbt" or not therapy_mode:
            result["techniques"]["sfbt"] = suggest_sfbt_technique(user_message)

    return result

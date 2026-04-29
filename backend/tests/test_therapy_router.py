"""
Тестовый скрипт для проверки динамического маршрутизатора терапевтических техник.

Запуск: python test_therapy_router.py
"""

from app.core.therapy_router import TherapyRouter, TherapyState
from app.core.prompts.builder import build_system_prompt


def test_router_basic():
    """Тест базовой работы маршрутизатора."""
    print("=== ТЕСТ 1: Базовая работа маршрутизатора ===\n")

    # Создать маршрутизатор
    router = TherapyRouter()

    # Начальное состояние: высокий дистресс, паника
    initial_state = TherapyState(
        distress_score=0.85,
        emotion="паника",
        theme="безысходность",
        current_goal=None,
        history=[],
        attempts=0,
        max_attempts=5,
    )

    # Построить маршрут
    route = router.route(initial_state, "мне плохо, всё бессмысленно, не могу дышать")

    # Вывести маршрут
    print("Начальное состояние:")
    print(f"  Distress: {0.85:.2f}")
    print(f"  Эмоция: паника")
    print(f"  Тема: безысходность")
    print()

    print("Маршрут терапевтических техник:")
    for i, (technique_id, node) in enumerate(route, 1):
        print(f"{i}. {node.name} ({node.category.value.upper()})")
        print(f"   Цели: {', '.join([g.value for g in node.goals])}")
        print(f"   Эффективность: {node.effectiveness_weight}")
        print()

    print(f"Финальный distress (симуляция): {initial_state.distress_score:.2f}")
    print()


def test_router_with_prompt():
    """Тест интеграции маршрутизатора с builder.py."""
    print("=== ТЕСТ 2: Интеграция с builder.py ===\n")

    # Построить промпт с использованием маршрутизатора
    prompt = build_system_prompt(
        branch="B",
        crisis_level="high",
        user_message="паника, не могу дышать, сердце выпрыгивает",
        distress_score=0.85,
        emotion="паника",
        theme="безысходность",
        use_router=True,
    )

    # Вывести только блок с маршрутом (последние 1000 символов)
    print("Фрагмент системного промпта (блок с маршрутом):")
    print("-" * 80)
    print(prompt[-1500:])
    print("-" * 80)
    print()


def test_router_different_states():
    """Тест маршрутизатора с разными состояниями."""
    print("=== ТЕСТ 3: Разные состояния пользователя ===\n")

    router = TherapyRouter()

    # Сценарий 1: Средний дистресс, когнитивные искажения
    print("Сценарий 1: Средний дистресс, когнитивные искажения")
    state1 = TherapyState(
        distress_score=0.55,
        emotion="грусть",
        theme="вина",
        current_goal=None,
        history=[],
        attempts=0,
    )
    route1 = router.route(state1, "я всегда всё порчу, я неудачник")
    print(f"Маршрут: {' → '.join([node.name for _, node in route1])}")
    print()

    # Сценарий 2: Низкий дистресс, застрял в проблеме
    print("Сценарий 2: Низкий дистресс, застрял в проблеме")
    state2 = TherapyState(
        distress_score=0.35,
        emotion="растерянность",
        theme="застрял",
        current_goal=None,
        history=[],
        attempts=0,
    )
    route2 = router.route(state2, "не знаю, что делать с работой, всё плохо")
    print(f"Маршрут: {' → '.join([node.name for _, node in route2])}")
    print()

    # Сценарий 3: Борьба с эмоцией
    print("Сценарий 3: Борьба с эмоцией")
    state3 = TherapyState(
        distress_score=0.60,
        emotion="тревога",
        theme="борьба",
        current_goal=None,
        history=[],
        attempts=0,
    )
    route3 = router.route(state3, "я борюсь с тревогой, не могу от неё избавиться")
    print(f"Маршрут: {' → '.join([node.name for _, node in route3])}")
    print()


def test_goal_determination():
    """Тест определения цели на основе состояния."""
    print("=== ТЕСТ 4: Определение цели ===\n")

    router = TherapyRouter()

    test_cases = [
        (0.85, "паника", "безысходность", "REDUCE_DISTRESS"),
        (0.65, "страх", "диссоциация", "GROUND"),
        (0.50, "грусть", "вина", "REFRAME_COGNITION"),
        (0.40, "растерянность", "застрял", "FIND_SOLUTION"),
        (0.55, "тревога", "борьба", "ACCEPT_EMOTION"),
    ]

    for distress, emotion, theme, expected_goal in test_cases:
        state = TherapyState(
            distress_score=distress,
            emotion=emotion,
            theme=theme,
            current_goal=None,
            history=[],
            attempts=0,
        )
        goal = router.determine_goal(state)
        status = "✓" if goal.value == expected_goal.lower() else "✗"
        print(f"{status} distress={distress:.2f}, тема={theme:15s} → {goal.value:20s} (ожидалось: {expected_goal.lower()})")

    print()


if __name__ == "__main__":
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ ДИНАМИЧЕСКОГО МАРШРУТИЗАТОРА ТЕРАПЕВТИЧЕСКИХ ТЕХНИК")
    print("=" * 80)
    print()

    try:
        test_router_basic()
        test_router_with_prompt()
        test_router_different_states()
        test_goal_determination()

        print("=" * 80)
        print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

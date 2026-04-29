"""
Динамический маршрутизатор терапевтических техник.

Концепция: граф возможных терапевтических путей, где система:
1. Определяет цель (снизить дистресс, изменить когницию, найти решение)
2. Выбирает инструмент из доступных узлов графа
3. Применяет инструмент
4. Оценивает эффективность
5. Если цель не достигнута — меняет инструмент
6. Повторяет до достижения цели или исчерпания попыток

Похоже на маршрутизацию в Tor — динамический выбор пути через узлы.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.core.knowledge.who_pfa import suggest_pfa_technique, get_pfa_technique
from app.core.knowledge.sfbt_mi import suggest_sfbt_technique, get_sfbt_technique
from app.core.knowledge.cbt_techniques import get_distortion_by_keywords, COGNITIVE_DISTORTIONS
from app.core.knowledge.dbt_skills import suggest_dbt_skill, ALL_DBT_SKILLS
from app.core.knowledge.act_processes import suggest_act_process, ACT_PROCESSES


# ============================================================================
# ТИПЫ ЦЕЛЕЙ И ИНСТРУМЕНТОВ
# ============================================================================

class TherapyGoal(Enum):
    """Возможные цели терапевтического вмешательства."""
    REDUCE_DISTRESS = "reduce_distress"          # Снизить дистресс (0.8 → 0.5)
    GROUND = "ground"                            # Заземлить (диссоциация → присутствие)
    REFRAME_COGNITION = "reframe_cognition"      # Переформулировать мысли (искажение → реалистичность)
    FIND_SOLUTION = "find_solution"              # Найти решение (застрял → направление)
    ACCEPT_EMOTION = "accept_emotion"            # Принять эмоцию (борьба → принятие)
    REGULATE_EMOTION = "regulate_emotion"        # Регулировать эмоцию (интенсивность → контроль)


class TechniqueCategory(Enum):
    """Категории терапевтических техник."""
    PFA = "pfa"           # Первая психологическая помощь (ВОЗ)
    CBT = "cbt"           # Когнитивно-поведенческая терапия
    DBT = "dbt"           # Диалектическая поведенческая терапия
    ACT = "act"           # Терапия принятия и ответственности
    SFBT = "sfbt"         # Ориентированная на решение краткосрочная терапия
    MI = "mi"             # Мотивационное консультирование


@dataclass
class TherapyNode:
    """Узел в графе терапевтических техник."""
    technique_id: str                    # Уникальный ID техники
    category: TechniqueCategory          # Категория (PFA, CBT, DBT, ACT, SFBT)
    name: str                            # Название техники
    goals: List[TherapyGoal]             # Какие цели может достичь
    prerequisites: List[str]             # Требования (например, "distress < 0.7")
    next_nodes: List[str]                # Возможные следующие техники
    effectiveness_weight: float          # Базовая эффективность (0.0-1.0)


@dataclass
class TherapyState:
    """Текущее состояние пользователя и терапевтического процесса."""
    distress_score: float                # Уровень дистресса (0.0-1.0)
    emotion: Optional[str]               # Текущая эмоция
    theme: Optional[str]                 # Тема (утрата, вина, безысходность, etc.)
    current_goal: Optional[TherapyGoal]  # Текущая цель
    history: List[str]                   # История использованных техник
    attempts: int                        # Количество попыток
    max_attempts: int = 5                # Максимум попыток


# ============================================================================
# ГРАФ ТЕРАПЕВТИЧЕСКИХ ТЕХНИК
# ============================================================================

THERAPY_GRAPH: Dict[str, TherapyNode] = {
    # === PFA (Первая психологическая помощь) ===
    "pfa_5_4_3_2_1": TherapyNode(
        technique_id="pfa_5_4_3_2_1",
        category=TechniqueCategory.PFA,
        name="Заземление 5-4-3-2-1",
        goals=[TherapyGoal.GROUND, TherapyGoal.REDUCE_DISTRESS],
        prerequisites=["distress >= 0.6"],
        next_nodes=["pfa_box_breathing", "dbt_tipp", "act_present_moment"],
        effectiveness_weight=0.8,
    ),

    "pfa_box_breathing": TherapyNode(
        technique_id="pfa_box_breathing",
        category=TechniqueCategory.PFA,
        name="Дыхание по квадрату",
        goals=[TherapyGoal.REDUCE_DISTRESS, TherapyGoal.REGULATE_EMOTION],
        prerequisites=["distress >= 0.5"],
        next_nodes=["pfa_5_4_3_2_1", "dbt_tipp", "act_acceptance"],
        effectiveness_weight=0.75,
    ),

    # === DBT (Диалектическая поведенческая терапия) ===
    "dbt_tipp": TherapyNode(
        technique_id="dbt_tipp",
        category=TechniqueCategory.DBT,
        name="TIPP (быстрое снижение дистресса)",
        goals=[TherapyGoal.REDUCE_DISTRESS, TherapyGoal.REGULATE_EMOTION],
        prerequisites=["distress >= 0.7"],
        next_nodes=["pfa_box_breathing", "act_acceptance", "dbt_radical_acceptance"],
        effectiveness_weight=0.85,
    ),

    "dbt_radical_acceptance": TherapyNode(
        technique_id="dbt_radical_acceptance",
        category=TechniqueCategory.DBT,
        name="Радикальное принятие",
        goals=[TherapyGoal.ACCEPT_EMOTION],
        prerequisites=["distress < 0.7"],
        next_nodes=["act_acceptance", "sfbt_coping_question"],
        effectiveness_weight=0.7,
    ),

    # === ACT (Терапия принятия и ответственности) ===
    "act_acceptance": TherapyNode(
        technique_id="act_acceptance",
        category=TechniqueCategory.ACT,
        name="Принятие",
        goals=[TherapyGoal.ACCEPT_EMOTION],
        prerequisites=["distress < 0.7"],
        next_nodes=["act_defusion", "sfbt_scaling"],
        effectiveness_weight=0.75,
    ),

    "act_defusion": TherapyNode(
        technique_id="act_defusion",
        category=TechniqueCategory.ACT,
        name="Когнитивная дефузия",
        goals=[TherapyGoal.REFRAME_COGNITION],
        prerequisites=["distress < 0.6"],
        next_nodes=["cbt_reframe", "sfbt_exceptions"],
        effectiveness_weight=0.8,
    ),

    "act_present_moment": TherapyNode(
        technique_id="act_present_moment",
        category=TechniqueCategory.ACT,
        name="Контакт с настоящим моментом",
        goals=[TherapyGoal.GROUND],
        prerequisites=["distress >= 0.5"],
        next_nodes=["pfa_5_4_3_2_1", "act_acceptance"],
        effectiveness_weight=0.7,
    ),

    # === CBT (Когнитивно-поведенческая терапия) ===
    "cbt_reframe": TherapyNode(
        technique_id="cbt_reframe",
        category=TechniqueCategory.CBT,
        name="Переформулирование когнитивных искажений",
        goals=[TherapyGoal.REFRAME_COGNITION],
        prerequisites=["distress < 0.6"],
        next_nodes=["act_defusion", "sfbt_scaling"],
        effectiveness_weight=0.75,
    ),

    # === SFBT (Ориентированная на решение краткосрочная терапия) ===
    "sfbt_miracle_question": TherapyNode(
        technique_id="sfbt_miracle_question",
        category=TechniqueCategory.SFBT,
        name="Вопрос о чуде",
        goals=[TherapyGoal.FIND_SOLUTION],
        prerequisites=["distress < 0.5"],
        next_nodes=["sfbt_scaling", "sfbt_exceptions"],
        effectiveness_weight=0.7,
    ),

    "sfbt_scaling": TherapyNode(
        technique_id="sfbt_scaling",
        category=TechniqueCategory.SFBT,
        name="Шкалирование",
        goals=[TherapyGoal.FIND_SOLUTION],
        prerequisites=["distress < 0.6"],
        next_nodes=["sfbt_miracle_question", "sfbt_coping_question"],
        effectiveness_weight=0.75,
    ),

    "sfbt_exceptions": TherapyNode(
        technique_id="sfbt_exceptions",
        category=TechniqueCategory.SFBT,
        name="Исключения",
        goals=[TherapyGoal.FIND_SOLUTION, TherapyGoal.REFRAME_COGNITION],
        prerequisites=["distress < 0.6"],
        next_nodes=["sfbt_scaling", "cbt_reframe"],
        effectiveness_weight=0.7,
    ),

    "sfbt_coping_question": TherapyNode(
        technique_id="sfbt_coping_question",
        category=TechniqueCategory.SFBT,
        name="Вопрос о совладании",
        goals=[TherapyGoal.FIND_SOLUTION],
        prerequisites=["distress < 0.7"],
        next_nodes=["sfbt_scaling", "act_acceptance"],
        effectiveness_weight=0.75,
    ),
}


# ============================================================================
# МАРШРУТИЗАТОР
# ============================================================================

class TherapyRouter:
    """Динамический маршрутизатор терапевтических техник."""

    def __init__(self):
        self.graph = THERAPY_GRAPH

    def determine_goal(self, state: TherapyState) -> TherapyGoal:
        """
        Определить цель на основе текущего состояния.

        Args:
            state: Текущее состояние пользователя

        Returns:
            TherapyGoal: Цель терапевтического вмешательства
        """
        # Высокий дистресс → снизить дистресс
        if state.distress_score >= 0.7:
            return TherapyGoal.REDUCE_DISTRESS

        # Средний дистресс + тема "безысходность" → заземление
        if state.distress_score >= 0.5 and state.theme in ["безысходность", "диссоциация"]:
            return TherapyGoal.GROUND

        # Когнитивные искажения → переформулирование
        if state.theme in ["вина", "самокритика", "катастрофизация"]:
            return TherapyGoal.REFRAME_COGNITION

        # Застрял в проблеме → найти решение
        if state.theme in ["застрял", "не знаю что делать", "тупик"]:
            return TherapyGoal.FIND_SOLUTION

        # Борьба с эмоцией → принятие
        if state.theme in ["борьба", "не могу избавиться"]:
            return TherapyGoal.ACCEPT_EMOTION

        # По умолчанию → снизить дистресс
        return TherapyGoal.REDUCE_DISTRESS

    def choose_technique(
        self,
        state: TherapyState,
        goal: TherapyGoal,
        previous_technique: Optional[str] = None,
    ) -> Optional[str]:
        """
        Выбрать следующую технику на основе цели и состояния.

        Args:
            state: Текущее состояние
            goal: Цель
            previous_technique: Предыдущая техника (если есть)

        Returns:
            str: ID выбранной техники или None, если нет подходящих
        """
        # Если есть предыдущая техника — выбрать из её next_nodes
        if previous_technique and previous_technique in self.graph:
            candidates = [
                self.graph[node_id]
                for node_id in self.graph[previous_technique].next_nodes
                if node_id in self.graph
            ]
        else:
            # Иначе — выбрать из всех техник
            candidates = list(self.graph.values())

        # Фильтр 1: Техника должна подходить для цели
        candidates = [node for node in candidates if goal in node.goals]

        # Фильтр 2: Техника не должна быть в истории (избегаем повторов)
        candidates = [node for node in candidates if node.technique_id not in state.history]

        # Фильтр 3: Проверка prerequisites
        candidates = [
            node for node in candidates
            if self._check_prerequisites(node, state)
        ]

        if not candidates:
            return None

        # Выбрать технику с максимальной эффективностью
        best_technique = max(candidates, key=lambda n: n.effectiveness_weight)
        return best_technique.technique_id

    def _check_prerequisites(self, node: TherapyNode, state: TherapyState) -> bool:
        """
        Проверить, выполнены ли prerequisites для техники.

        Args:
            node: Узел техники
            state: Текущее состояние

        Returns:
            bool: True если prerequisites выполнены
        """
        for prereq in node.prerequisites:
            # Простая проверка через eval (в продакшене — более безопасный парсер)
            try:
                distress = state.distress_score
                if not eval(prereq):
                    return False
            except:
                return False
        return True

    def evaluate_effectiveness(
        self,
        technique_id: str,
        old_state: TherapyState,
        new_state: TherapyState,
    ) -> float:
        """
        Оценить эффективность применённой техники.

        Args:
            technique_id: ID техники
            old_state: Состояние до применения
            new_state: Состояние после применения

        Returns:
            float: Оценка эффективности (0.0-1.0)
        """
        # Базовая оценка: насколько снизился дистресс
        distress_reduction = old_state.distress_score - new_state.distress_score

        # Нормализация: 0.2 снижения = 1.0 эффективность
        effectiveness = min(distress_reduction / 0.2, 1.0)

        return max(effectiveness, 0.0)

    def route(
        self,
        initial_state: TherapyState,
        user_message: str,
    ) -> List[Tuple[str, TherapyNode]]:
        """
        Построить маршрут терапевтических техник.

        Args:
            initial_state: Начальное состояние
            user_message: Сообщение пользователя

        Returns:
            List[Tuple[str, TherapyNode]]: Список (technique_id, node)
        """
        route = []
        state = initial_state
        previous_technique = None

        while state.attempts < state.max_attempts:
            # Определить цель
            goal = self.determine_goal(state)
            state.current_goal = goal

            # Выбрать технику
            technique_id = self.choose_technique(state, goal, previous_technique)

            if not technique_id:
                # Нет подходящих техник — завершить
                break

            # Добавить в маршрут
            node = self.graph[technique_id]
            route.append((technique_id, node))

            # Обновить состояние
            state.history.append(technique_id)
            state.attempts += 1
            previous_technique = technique_id

            # Симуляция: предполагаем, что техника снизила дистресс на 0.15
            # В реальности — это будет оценка после применения
            state.distress_score = max(state.distress_score - 0.15, 0.0)

            # Если цель достигнута — завершить
            if self._goal_achieved(goal, state):
                break

        return route

    def _goal_achieved(self, goal: TherapyGoal, state: TherapyState) -> bool:
        """
        Проверить, достигнута ли цель.

        Args:
            goal: Цель
            state: Текущее состояние

        Returns:
            bool: True если цель достигнута
        """
        if goal == TherapyGoal.REDUCE_DISTRESS:
            return state.distress_score < 0.5

        if goal == TherapyGoal.GROUND:
            return state.distress_score < 0.6

        if goal in [TherapyGoal.REFRAME_COGNITION, TherapyGoal.FIND_SOLUTION, TherapyGoal.ACCEPT_EMOTION]:
            return state.distress_score < 0.5

        return False


# ============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ============================================================================

if __name__ == "__main__":
    # Создать маршрутизатор
    router = TherapyRouter()

    # Начальное состояние пользователя
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
    print("=== МАРШРУТ ТЕРАПЕВТИЧЕСКИХ ТЕХНИК ===\n")
    for i, (technique_id, node) in enumerate(route, 1):
        print(f"{i}. {node.name} ({node.category.value})")
        print(f"   Цель: {node.goals[0].value}")
        print(f"   Эффективность: {node.effectiveness_weight}")
        print()

    print(f"Финальный distress: {initial_state.distress_score:.2f}")

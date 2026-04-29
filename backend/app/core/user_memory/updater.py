"""
Обновление досье пользователя (Updater)
Применение извлечённых фактов к досье
"""

from typing import List, Dict, Any
from datetime import datetime

from app.core.user_memory.dossier import (
    UserDossier,
    BasicInfo,
    Relationships,
    Work,
    Health,
    CurrentChallenge,
    CopingStrategies,
    TherapySession,
    Preferences,
    ChallengeSeverity,
    ChallengeStatus,
    RelationshipStatus,
)


class DossierUpdater:
    """Обновление досье пользователя на основе извлечённых фактов"""

    def __init__(self, dossier: UserDossier):
        self.dossier = dossier

    def apply_facts(self, facts: List[Dict[str, Any]]) -> None:
        """
        Применить список фактов к досье

        Args:
            facts: Список фактов в формате:
                [
                    {
                        "category": "basic_info",
                        "field": "name",
                        "value": "Иван",
                        "confidence": 0.95
                    },
                    ...
                ]
        """
        for fact in facts:
            category = fact.get("category")
            confidence = fact.get("confidence", 1.0)

            # Пропустить факты с низкой уверенностью
            if confidence < 0.7:
                continue

            # Применить факт к соответствующей категории
            if category == "basic_info":
                self._update_basic_info(fact)
            elif category == "life_stages":
                self._update_life_stages(fact)
            elif category == "relationships":
                self._update_relationships(fact)
            elif category == "work":
                self._update_work(fact)
            elif category == "health":
                self._update_health(fact)
            elif category == "current_challenges":
                self._update_current_challenges(fact)
            elif category == "goals":
                self._update_goals(fact)
            elif category == "values":
                self._update_values(fact)
            elif category == "coping_strategies":
                self._update_coping_strategies(fact)
            elif category == "preferences":
                self._update_preferences(fact)

        # Обновить timestamp
        self.dossier.updated_at = datetime.utcnow()

    def _update_basic_info(self, fact: Dict[str, Any]) -> None:
        """Обновить базовую информацию"""
        field = fact.get("field")
        value = fact.get("value")

        if field == "name":
            self.dossier.basic_info.name = value
        elif field == "age":
            self.dossier.basic_info.age = int(value)
        elif field == "gender":
            self.dossier.basic_info.gender = value
        elif field == "location":
            self.dossier.basic_info.location = value
        elif field == "occupation":
            self.dossier.basic_info.occupation = value

    def _update_life_stages(self, fact: Dict[str, Any]) -> None:
        """Обновить жизненные этапы"""
        stage = fact.get("field")  # "childhood", "adolescence", "adulthood"
        value = fact.get("value")

        if stage not in self.dossier.life_stages:
            self.dossier.life_stages[stage] = []

        # Добавить факт, если его ещё нет
        if value not in self.dossier.life_stages[stage]:
            self.dossier.life_stages[stage].append(value)

    def _update_relationships(self, fact: Dict[str, Any]) -> None:
        """Обновить отношения"""
        field = fact.get("field")
        value = fact.get("value")

        if field == "current_status":
            # Преобразовать строку в enum
            try:
                self.dossier.relationships.current_status = RelationshipStatus(value)
            except ValueError:
                pass
        elif field == "friends":
            self.dossier.relationships.friends = value
        # Можно добавить обработку ex_spouse, family и т.д.

    def _update_work(self, fact: Dict[str, Any]) -> None:
        """Обновить работу"""
        field = fact.get("field")
        value = fact.get("value")

        if field == "current_job":
            self.dossier.work.current_job = value
        elif field == "experience":
            self.dossier.work.experience = value
        elif field == "satisfaction":
            self.dossier.work.satisfaction = value
        elif field == "challenges":
            self.dossier.work.challenges = value

    def _update_health(self, fact: Dict[str, Any]) -> None:
        """Обновить здоровье"""
        field = fact.get("field")
        value = fact.get("value")

        if field == "physical":
            if value not in self.dossier.health.physical:
                self.dossier.health.physical.append(value)
        elif field == "mental":
            if value not in self.dossier.health.mental:
                self.dossier.health.mental.append(value)
        elif field == "medications":
            self.dossier.health.medications = value

    def _update_current_challenges(self, fact: Dict[str, Any]) -> None:
        """Обновить текущие проблемы"""
        value = fact.get("value")

        if not isinstance(value, dict):
            return

        challenge_text = value.get("challenge")
        severity = value.get("severity", "medium")

        # Проверить, есть ли уже такая проблема
        existing = next(
            (c for c in self.dossier.current_challenges if c.challenge == challenge_text),
            None
        )

        if existing:
            # Обновить существующую проблему
            existing.severity = ChallengeSeverity(severity)
            existing.status = ChallengeStatus.ACTIVE
        else:
            # Добавить новую проблему
            new_challenge = CurrentChallenge(
                challenge=challenge_text,
                severity=ChallengeSeverity(severity),
                started=datetime.utcnow(),
                status=ChallengeStatus.ACTIVE
            )
            self.dossier.current_challenges.append(new_challenge)

    def _update_goals(self, fact: Dict[str, Any]) -> None:
        """Обновить цели"""
        value = fact.get("value")

        if value not in self.dossier.goals:
            self.dossier.goals.append(value)

    def _update_values(self, fact: Dict[str, Any]) -> None:
        """Обновить ценности"""
        value = fact.get("value")

        if value not in self.dossier.values:
            self.dossier.values.append(value)

    def _update_coping_strategies(self, fact: Dict[str, Any]) -> None:
        """Обновить стратегии совладания"""
        field = fact.get("field")  # "what_works" или "what_doesnt_work"
        value = fact.get("value")

        if field == "what_works":
            if value not in self.dossier.coping_strategies.what_works:
                self.dossier.coping_strategies.what_works.append(value)
        elif field == "what_doesnt_work":
            if value not in self.dossier.coping_strategies.what_doesnt_work:
                self.dossier.coping_strategies.what_doesnt_work.append(value)

    def _update_preferences(self, fact: Dict[str, Any]) -> None:
        """Обновить предпочтения"""
        field = fact.get("field")
        value = fact.get("value")

        if field == "communication_style":
            self.dossier.preferences.communication_style = value
        elif field == "language":
            self.dossier.preferences.language = value
        elif field == "tone":
            self.dossier.preferences.tone = value

    def add_therapy_session(
        self,
        session_id: str,
        approach: str,
        outcome: str,
        distress_before: float = None,
        distress_after: float = None
    ) -> None:
        """
        Добавить запись о терапевтической сессии

        Args:
            session_id: ID сессии
            approach: Подход (PFA, CBT, DBT, ACT, SFBT)
            outcome: Результат сессии
            distress_before: Уровень дистресса до сессии (0.0-1.0)
            distress_after: Уровень дистресса после сессии (0.0-1.0)
        """
        session = TherapySession(
            date=datetime.utcnow(),
            session_id=session_id,
            approach=approach,
            outcome=outcome,
            distress_before=distress_before,
            distress_after=distress_after
        )
        self.dossier.therapy_history.append(session)

    def resolve_challenge(self, challenge_text: str) -> bool:
        """
        Отметить проблему как решённую

        Args:
            challenge_text: Текст проблемы

        Returns:
            True если проблема найдена и отмечена как решённая
        """
        for challenge in self.dossier.current_challenges:
            if challenge.challenge == challenge_text:
                challenge.status = ChallengeStatus.RESOLVED
                return True
        return False

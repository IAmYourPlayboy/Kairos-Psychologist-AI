"""
Сжатие досье в промпт (Compressor)
Преобразование досье в компактный промпт для системного промпта
"""

from typing import List
from app.core.user_memory.dossier import UserDossier, ChallengeStatus


class DossierCompressor:
    """Сжатие досье пользователя в компактный промпт"""

    def __init__(self, dossier: UserDossier):
        self.dossier = dossier

    def compress(self, max_tokens: int = 1000) -> str:
        """
        Сжать досье в компактный промпт

        Приоритет информации:
        1. Текущие активные проблемы (самое важное)
        2. Базовая информация
        3. Что работает/не работает (для персонализации подхода)
        4. Цели
        5. Отношения
        6. Здоровье
        7. История терапии (последние 3 сессии)

        Args:
            max_tokens: Максимальное количество токенов (~500-1000)

        Returns:
            Компактный промпт в формате markdown
        """
        sections = []

        # 1. Текущие активные проблемы (КРИТИЧНО)
        active_challenges = [
            c for c in self.dossier.current_challenges
            if c.status == ChallengeStatus.ACTIVE
        ]
        if active_challenges:
            challenges_text = ", ".join([
                f"{c.challenge} ({c.severity.value})"
                for c in active_challenges[:3]  # Максимум 3 проблемы
            ])
            sections.append(f"**Текущие проблемы**: {challenges_text}")

        # 2. Базовая информация
        info_parts = []
        if self.dossier.basic_info.name:
            info_parts.append(f"Имя: {self.dossier.basic_info.name}")
        if self.dossier.basic_info.age:
            info_parts.append(f"Возраст: {self.dossier.basic_info.age}")
        if self.dossier.basic_info.occupation:
            info_parts.append(f"Работа: {self.dossier.basic_info.occupation}")
        if info_parts:
            sections.append("**Базовая информация**: " + ", ".join(info_parts))

        # 3. Что работает/не работает (для персонализации)
        if self.dossier.coping_strategies.what_works:
            works = ", ".join(self.dossier.coping_strategies.what_works[:3])
            sections.append(f"**Помогает**: {works}")
        if self.dossier.coping_strategies.what_doesnt_work:
            doesnt_work = ", ".join(self.dossier.coping_strategies.what_doesnt_work[:3])
            sections.append(f"**Не помогает**: {doesnt_work}")

        # 4. Цели
        if self.dossier.goals:
            goals = ", ".join(self.dossier.goals[:3])
            sections.append(f"**Цели**: {goals}")

        # 5. Отношения
        if self.dossier.relationships.current_status:
            sections.append(f"**Отношения**: {self.dossier.relationships.current_status.value}")

        # 6. Ментальное здоровье
        if self.dossier.health.mental:
            mental = ", ".join(self.dossier.health.mental[:3])
            sections.append(f"**Ментальное здоровье**: {mental}")

        # 7. История терапии (последние 3 сессии)
        if self.dossier.therapy_history:
            recent_sessions = self.dossier.therapy_history[-3:]
            history_parts = []
            for session in recent_sessions:
                outcome_short = session.outcome[:50] if len(session.outcome) > 50 else session.outcome
                history_parts.append(f"{session.approach}: {outcome_short}")
            sections.append(f"**История терапии**: {'; '.join(history_parts)}")

        # 8. Предпочтения в общении
        if self.dossier.preferences.communication_style:
            sections.append(f"**Стиль общения**: {self.dossier.preferences.communication_style}")

        # Объединить секции
        prompt = "\n".join(sections)

        # Если промпт слишком длинный, обрезать менее важные секции
        if len(prompt) > max_tokens * 4:  # Примерно 4 символа на токен
            # Оставить только критичные секции (1-4)
            prompt = "\n".join(sections[:4])

        return prompt

    def compress_for_crisis(self) -> str:
        """
        Сжать досье для кризисной ситуации

        В кризисе нужна только самая критичная информация:
        - Текущие проблемы
        - Что работает/не работает
        - История суицидальных мыслей (если есть)

        Returns:
            Минимальный промпт для кризиса
        """
        sections = []

        # Текущие активные проблемы
        active_challenges = [
            c for c in self.dossier.current_challenges
            if c.status == ChallengeStatus.ACTIVE
        ]
        if active_challenges:
            challenges_text = ", ".join([c.challenge for c in active_challenges[:2]])
            sections.append(f"**Проблемы**: {challenges_text}")

        # Что работает (для быстрой стабилизации)
        if self.dossier.coping_strategies.what_works:
            works = ", ".join(self.dossier.coping_strategies.what_works[:2])
            sections.append(f"**Помогает**: {works}")

        # История суицидальных мыслей
        suicidal_history = [
            c for c in self.dossier.current_challenges
            if "суицид" in c.challenge.lower() or "самоубийство" in c.challenge.lower()
        ]
        if suicidal_history:
            sections.append("**⚠️ История суицидальных мыслей**")

        return "\n".join(sections) if sections else ""

    def get_summary_stats(self) -> dict:
        """
        Получить статистику досье

        Returns:
            Словарь со статистикой
        """
        return {
            "total_challenges": len(self.dossier.current_challenges),
            "active_challenges": len([
                c for c in self.dossier.current_challenges
                if c.status == ChallengeStatus.ACTIVE
            ]),
            "resolved_challenges": len([
                c for c in self.dossier.current_challenges
                if c.status == ChallengeStatus.RESOLVED
            ]),
            "therapy_sessions": len(self.dossier.therapy_history),
            "goals": len(self.dossier.goals),
            "values": len(self.dossier.values),
            "coping_strategies_works": len(self.dossier.coping_strategies.what_works),
            "coping_strategies_doesnt_work": len(self.dossier.coping_strategies.what_doesnt_work),
        }

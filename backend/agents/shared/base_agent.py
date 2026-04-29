"""Базовый класс для всех агентов Кайроса."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Базовый класс автономного агента.

    Каждый агент — отдельный исполнитель задачи.
    Агенты общаются через Orchestrator.
    """

    def __init__(self, name: str, priority: int = 5) -> None:
        """
        Args:
            name: Уникальное имя агента
            priority: Приоритет (1-10, меньше = выше)
        """
        self.name = name
        self.priority = priority
        self._is_active = False
        self._last_run: Optional[str] = None

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """Выполнить задачу.

        Args:
            context: Контекст от Orchestrator (задание + данные)

        Returns:
            Результат выполнения для передачи следующему агенту
        """
        ...

    def activate(self) -> None:
        """Активировать агента."""
        self._is_active = True
        logger.info(f"Агент {self.name} активирован")

    def deactivate(self) -> None:
        """Деактивировать агента."""
        self._is_active = False
        logger.info(f"Агент {self.name} деактивирован")

    @property
    def is_active(self) -> bool:
        """Проверить активность агента."""
        return self._is_active

    def get_status(self) -> dict:
        """Получить статус агента."""
        return {
            "name": self.name,
            "priority": self.priority,
            "is_active": self._is_active,
            "last_run": self._last_run,
        }
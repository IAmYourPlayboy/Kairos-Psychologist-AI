"""Кризисная инфраструктура.

После Сессии 18 здесь только статичные контакты — rule-based детекция
заменена слоем восприятия (см. core/perception/).
"""

from app.core.crisis.contacts import CrisisContact, get_crisis_contacts

__all__ = ["CrisisContact", "get_crisis_contacts"]

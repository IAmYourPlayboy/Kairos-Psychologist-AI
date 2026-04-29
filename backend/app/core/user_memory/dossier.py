"""
Модель досье пользователя (User Dossier)
Структурированная база знаний о пользователе
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class RelationshipStatus(str, Enum):
    """Статус отношений"""
    SINGLE = "одинок"
    DATING = "встречается"
    MARRIED = "женат/замужем"
    DIVORCED = "разведён"
    WIDOWED = "вдовец/вдова"


class ChallengeSeverity(str, Enum):
    """Серьёзность проблемы"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChallengeStatus(str, Enum):
    """Статус проблемы"""
    ACTIVE = "активный"
    RESOLVED = "решён"
    ONGOING = "продолжается"


class BasicInfo(BaseModel):
    """Базовая информация о пользователе"""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None


class ExSpouse(BaseModel):
    """Информация о бывшем супруге"""
    name: Optional[str] = None
    duration: Optional[str] = None
    reason_for_breakup: Optional[str] = None


class Family(BaseModel):
    """Информация о семье"""
    mother: Optional[str] = None
    father: Optional[str] = None
    siblings: Optional[str] = None


class Relationships(BaseModel):
    """Отношения"""
    current_status: Optional[RelationshipStatus] = None
    ex_spouse: Optional[ExSpouse] = None
    family: Optional[Family] = None
    friends: Optional[str] = None


class Work(BaseModel):
    """Работа и карьера"""
    current_job: Optional[str] = None
    experience: Optional[str] = None
    satisfaction: Optional[str] = None
    challenges: Optional[str] = None


class Health(BaseModel):
    """Здоровье"""
    physical: List[str] = Field(default_factory=list)
    mental: List[str] = Field(default_factory=list)
    medications: Optional[str] = None


class CurrentChallenge(BaseModel):
    """Текущая проблема"""
    challenge: str
    severity: ChallengeSeverity
    started: datetime
    status: ChallengeStatus
    progress: Optional[str] = None


class CopingStrategies(BaseModel):
    """Стратегии совладания"""
    what_works: List[str] = Field(default_factory=list)
    what_doesnt_work: List[str] = Field(default_factory=list)


class TherapySession(BaseModel):
    """Сессия терапии"""
    date: datetime
    session_id: str
    approach: str
    outcome: str
    distress_before: Optional[float] = None
    distress_after: Optional[float] = None


class Preferences(BaseModel):
    """Предпочтения пользователя"""
    communication_style: Optional[str] = None
    language: str = "русский"
    tone: Optional[str] = None


class UserDossier(BaseModel):
    """Досье пользователя"""
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    # Основные разделы
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    life_stages: Dict[str, List[str]] = Field(default_factory=dict)
    relationships: Relationships = Field(default_factory=Relationships)
    work: Work = Field(default_factory=Work)
    health: Health = Field(default_factory=Health)
    current_challenges: List[CurrentChallenge] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)
    coping_strategies: CopingStrategies = Field(default_factory=CopingStrategies)
    therapy_history: List[TherapySession] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_compact_prompt(self) -> str:
        """
        Сжать досье в компактный промпт (~500-1000 токенов)
        для загрузки в системный промпт
        """
        sections = []

        # Базовая информация
        if self.basic_info.name or self.basic_info.age:
            info_parts = []
            if self.basic_info.name:
                info_parts.append(f"Имя: {self.basic_info.name}")
            if self.basic_info.age:
                info_parts.append(f"Возраст: {self.basic_info.age}")
            if self.basic_info.occupation:
                info_parts.append(f"Работа: {self.basic_info.occupation}")
            sections.append("**Базовая информация**: " + ", ".join(info_parts))

        # Текущие проблемы
        if self.current_challenges:
            active = [c for c in self.current_challenges if c.status == ChallengeStatus.ACTIVE]
            if active:
                challenges_text = ", ".join([c.challenge for c in active])
                sections.append(f"**Текущие проблемы**: {challenges_text}")

        # Отношения
        if self.relationships.current_status:
            sections.append(f"**Отношения**: {self.relationships.current_status}")

        # Здоровье
        if self.health.mental:
            sections.append(f"**Ментальное здоровье**: {', '.join(self.health.mental)}")

        # Что работает/не работает
        if self.coping_strategies.what_works:
            sections.append(f"**Помогает**: {', '.join(self.coping_strategies.what_works[:3])}")
        if self.coping_strategies.what_doesnt_work:
            sections.append(f"**Не помогает**: {', '.join(self.coping_strategies.what_doesnt_work[:3])}")

        # Цели
        if self.goals:
            sections.append(f"**Цели**: {', '.join(self.goals[:3])}")

        return "\n".join(sections)

"""
База кризисных ситуаций для AI-Психолог.

Структурированная база из 300+ кризисных ситуаций, с которыми Кайрос помогает справляться.
Организовано по категориям для удобного поиска и маршрутизации.

Используется в: app/core/therapy_router.py для определения темы и выбора подхода
"""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# КАТЕГОРИИ КРИЗИСНЫХ СИТУАЦИЙ
# ============================================================================

class CrisisCategory(Enum):
    """Основные категории кризисных ситуаций."""
    LOSS_DEATH = "loss_death"                    # Утрата и смерть
    TRAUMA_VIOLENCE = "trauma_violence"          # Травма и насилие
    RELATIONSHIPS = "relationships"              # Отношения и разрывы
    HEALTH = "health"                            # Здоровье и болезни
    WORK_CAREER = "work_career"                  # Работа и карьера
    IDENTITY_MEANING = "identity_meaning"        # Идентичность и смысл
    SOCIAL_ISOLATION = "social_isolation"        # Социальная изоляция
    FINANCIAL = "financial"                      # Финансовые кризисы
    EXISTENTIAL = "existential"                  # Экзистенциальные кризисы
    ADDICTION = "addiction"                      # Зависимости
    FAMILY_CHILDREN = "family_children"          # Семья и дети
    LEGAL_JUSTICE = "legal_justice"              # Правовые проблемы
    NATURAL_DISASTERS = "natural_disasters"      # Стихийные бедствия
    TECHNOLOGY_DIGITAL = "technology_digital"    # Цифровые кризисы
    # Новые категории для специфичных групп
    MEDICAL_WORKERS = "medical_workers"          # Медработники
    TEACHERS = "teachers"                        # Учителя
    MILITARY = "military"                        # Военные и контрактники
    POLICE_RESCUE = "police_rescue"              # Полиция и спасатели
    MIGRANTS = "migrants"                        # Мигранты и беженцы
    MOBILIZATION = "mobilization"                # Мобилизация (СВО)
    CONTRACT_SERVICE = "contract_service"        # Контрактная служба
    WAR_EMIGRATION = "war_emigration"            # Эмиграция из-за войны
    POLITICAL_REPRESSION = "political_repression" # Политические репрессии


@dataclass
class CrisisSituation:
    """Описание кризисной ситуации."""
    id: str                          # Уникальный ID
    category: CrisisCategory         # Категория
    title: str                       # Краткое название
    description: str                 # Описание ситуации
    severity: str                    # Тяжесть: low, medium, high, critical
    recommended_approach: List[str]  # Рекомендуемые подходы (PFA, CBT, DBT, ACT, SFBT)
    keywords: List[str]              # Ключевые слова для детекции


# ============================================================================
# БАЗА КРИЗИСНЫХ СИТУАЦИЙ (300+ ситуаций)
# ============================================================================

CRISIS_SITUATIONS: Dict[str, CrisisSituation] = {
    # ========================================================================
    # КАТЕГОРИЯ 1: УТРАТА И СМЕРТЬ (25 ситуаций)
    # ========================================================================
    "loss_001": CrisisSituation(
        id="loss_001",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть родителя",
        description="Смерть матери или отца",
        severity="high",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умер", "умерла", "мама", "папа", "родитель", "похороны", "потерял маму", "потерял папу"],
    ),

    "loss_002": CrisisSituation(
        id="loss_002",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть ребёнка",
        description="Смерть ребёнка (любого возраста)",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умер ребёнок", "умерла дочь", "умер сын", "потерял ребёнка", "смерть ребёнка"],
    ),

    "loss_003": CrisisSituation(
        id="loss_003",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть супруга/супруги",
        description="Смерть мужа или жены",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умер муж", "умерла жена", "вдова", "вдовец", "потерял жену", "потерял мужа"],
    ),

    "loss_004": CrisisSituation(
        id="loss_004",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть брата/сестры",
        description="Смерть брата или сестры",
        severity="high",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умер брат", "умерла сестра", "потерял брата", "потерял сестру"],
    ),

    "loss_005": CrisisSituation(
        id="loss_005",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть бабушки/дедушки",
        description="Смерть бабушки или дедушки",
        severity="medium",
        recommended_approach=["ACT", "grief_module"],
        keywords=["умерла бабушка", "умер дедушка", "потерял бабушку", "потерял дедушку"],
    ),

    "loss_006": CrisisSituation(
        id="loss_006",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть лучшего друга",
        description="Смерть лучшего друга или подруги",
        severity="high",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умер друг", "умерла подруга", "потерял друга", "смерть друга"],
    ),

    "loss_007": CrisisSituation(
        id="loss_007",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть домашнего животного",
        description="Смерть собаки, кошки или другого питомца",
        severity="medium",
        recommended_approach=["ACT", "grief_module"],
        keywords=["умерла собака", "умер кот", "умерла кошка", "питомец умер", "потерял собаку"],
    ),

    "loss_008": CrisisSituation(
        id="loss_008",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть питомца от несчастного случая",
        description="Питомца сбила машина или другой несчастный случай",
        severity="high",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["сбила машина", "собаку сбило", "кошку сбило", "несчастный случай с питомцем"],
    ),

    "loss_009": CrisisSituation(
        id="loss_009",
        category=CrisisCategory.LOSS_DEATH,
        title="Внезапная смерть близкого",
        description="Внезапная смерть от инфаркта, инсульта",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["внезапно умер", "инфаркт", "инсульт", "неожиданно умер"],
    ),

    "loss_010": CrisisSituation(
        id="loss_010",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть от суицида близкого",
        description="Близкий человек покончил с собой",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["покончил с собой", "суицид", "самоубийство", "повесился", "отравился"],
    ),

    "loss_011": CrisisSituation(
        id="loss_011",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть от передозировки",
        description="Смерть близкого от передозировки наркотиками или алкоголем",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["передозировка", "передоз", "наркотики", "умер от наркотиков"],
    ),

    "loss_012": CrisisSituation(
        id="loss_012",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть в ДТП",
        description="Смерть близкого в дорожно-транспортном происшествии",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["дтп", "авария", "сбила машина", "погиб в аварии"],
    ),

    "loss_013": CrisisSituation(
        id="loss_013",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть от убийства",
        description="Близкого убили",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["убили", "убийство", "убит", "убита"],
    ),

    "loss_014": CrisisSituation(
        id="loss_014",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть на войне",
        description="Смерть близкого на СВО или в результате мобилизации",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["погиб на войне", "сво", "мобилизация", "погиб в бою"],
    ),

    "loss_015": CrisisSituation(
        id="loss_015",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть от болезни",
        description="Смерть от рака, COVID или другой болезни",
        severity="high",
        recommended_approach=["ACT", "grief_module"],
        keywords=["умер от рака", "умер от ковида", "умер от болезни"],
    ),

    "loss_016": CrisisSituation(
        id="loss_016",
        category=CrisisCategory.LOSS_DEATH,
        title="Выкидыш",
        description="Потеря беременности (выкидыш)",
        severity="high",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["выкидыш", "потеря беременности", "потерял ребёнка"],
    ),

    "loss_017": CrisisSituation(
        id="loss_017",
        category=CrisisCategory.LOSS_DEATH,
        title="Мертворождение",
        description="Ребёнок родился мёртвым",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["мертворождение", "ребёнок родился мёртвым"],
    ),

    "loss_018": CrisisSituation(
        id="loss_018",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть во время родов",
        description="Смерть матери или ребёнка во время родов",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умерла при родах", "умер при родах", "смерть при родах"],
    ),

    "loss_019": CrisisSituation(
        id="loss_019",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть от медицинской ошибки",
        description="Близкий умер из-за ошибки врачей",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["медицинская ошибка", "врачи виноваты", "умер из-за врачей"],
    ),

    "loss_020": CrisisSituation(
        id="loss_020",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть от несчастного случая",
        description="Смерть от утопления, пожара, падения",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["утонул", "сгорел", "упал", "несчастный случай"],
    ),

    "loss_021": CrisisSituation(
        id="loss_021",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть коллеги",
        description="Смерть коллеги по работе",
        severity="medium",
        recommended_approach=["ACT", "grief_module"],
        keywords=["умер коллега", "коллега умер", "смерть коллеги"],
    ),

    "loss_022": CrisisSituation(
        id="loss_022",
        category=CrisisCategory.LOSS_DEATH,
        title="Смерть учителя/наставника",
        description="Смерть значимого учителя или наставника",
        severity="medium",
        recommended_approach=["ACT", "grief_module"],
        keywords=["умер учитель", "умер наставник", "смерть учителя"],
    ),

    "loss_023": CrisisSituation(
        id="loss_023",
        category=CrisisCategory.LOSS_DEATH,
        title="Множественная утрата",
        description="Смерть нескольких близких за короткий период",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умерли все", "потерял всех", "все умирают"],
    ),

    "loss_024": CrisisSituation(
        id="loss_024",
        category=CrisisCategory.LOSS_DEATH,
        title="Годовщина смерти",
        description="Годовщина смерти близкого человека",
        severity="medium",
        recommended_approach=["ACT", "grief_module"],
        keywords=["годовщина смерти", "год как умер", "прошёл год"],
    ),

    "loss_025": CrisisSituation(
        id="loss_025",
        category=CrisisCategory.LOSS_DEATH,
        title="Неопознанное тело",
        description="Близкий пропал, тело не найдено",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["пропал", "не нашли тело", "без вести пропал"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 2: ТРАВМА И НАСИЛИЕ (30 ситуаций)
    # ========================================================================
    "trauma_001": CrisisSituation(
        id="trauma_001",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Изнасилование",
        description="Изнасилование (взрослый)",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["изнасиловали", "изнасилование", "насилие"],
    ),

    "trauma_002": CrisisSituation(
        id="trauma_002",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Изнасилование в детстве",
        description="Изнасилование в детстве (воспоминания)",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["изнасиловали в детстве", "насилие в детстве"],
    ),

    "trauma_003": CrisisSituation(
        id="trauma_003",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Домашнее насилие",
        description="Физическое или психологическое насилие от партнёра",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["бьёт муж", "бьёт жена", "домашнее насилие", "избивает"],
    ),

    "trauma_004": CrisisSituation(
        id="trauma_004",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Избиение",
        description="Избиение партнёром или родителями",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["избили", "побили", "избиение"],
    ),

    "trauma_005": CrisisSituation(
        id="trauma_005",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Свидетель убийства",
        description="Видел, как убивают человека",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["видел убийство", "видел как убивают", "свидетель убийства"],
    ),

    "trauma_006": CrisisSituation(
        id="trauma_006",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Участие в боевых действиях",
        description="Участие в СВО или других боевых действиях",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["был на войне", "сво", "боевые действия", "птср"],
    ),

    "trauma_007": CrisisSituation(
        id="trauma_007",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Плен",
        description="Был в плену (военном или террористическом)",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["был в плену", "плен", "пленили"],
    ),

    "trauma_008": CrisisSituation(
        id="trauma_008",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Пытки",
        description="Подвергался пыткам",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["пытали", "пытки", "истязания"],
    ),

    "trauma_009": CrisisSituation(
        id="trauma_009",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Нападение на улице",
        description="Грабёж, избиение на улице",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["напали на улице", "ограбили", "избили на улице"],
    ),

    "trauma_010": CrisisSituation(
        id="trauma_010",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Сталкинг",
        description="Преследование, сталкинг",
        severity="high",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["преследует", "сталкинг", "следит за мной"],
    ),

    "trauma_011": CrisisSituation(
        id="trauma_011",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Угрозы убийством",
        description="Угрозы убийством от партнёра или других лиц",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["угрожает убить", "убью тебя", "угрозы убийством"],
    ),

    "trauma_012": CrisisSituation(
        id="trauma_012",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Попытка убийства",
        description="Пережил попытку убийства",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["пытались убить", "покушение", "попытка убийства"],
    ),

    "trauma_013": CrisisSituation(
        id="trauma_013",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Сексуальные домогательства на работе",
        description="Сексуальные домогательства от коллег или начальства",
        severity="high",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["домогательства", "сексуальные домогательства", "харассмент"],
    ),

    "trauma_014": CrisisSituation(
        id="trauma_014",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Буллинг в школе (физический)",
        description="Физическая травля в школе",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["бьют в школе", "избивают в школе", "буллинг"],
    ),

    "trauma_015": CrisisSituation(
        id="trauma_015",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Буллинг в школе (психологический)",
        description="Психологическая травля в школе",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["травят в школе", "издеваются в школе", "буллинг"],
    ),

    "trauma_016": CrisisSituation(
        id="trauma_016",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Кибербуллинг",
        description="Травля в интернете",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["кибербуллинг", "травля в интернете", "троллинг", "хейт"],
    ),

    "trauma_017": CrisisSituation(
        id="trauma_017",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Травля на работе (моббинг)",
        description="Систематическая травля на работе",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["травля на работе", "моббинг", "травят на работе"],
    ),

    "trauma_018": CrisisSituation(
        id="trauma_018",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Свидетель ДТП с жертвами",
        description="Видел ДТП с погибшими или ранеными",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["видел дтп", "видел аварию", "свидетель дтп"],
    ),

    "trauma_019": CrisisSituation(
        id="trauma_019",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Свидетель теракта",
        description="Был свидетелем теракта",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["видел теракт", "свидетель теракта", "был при теракте"],
    ),

    "trauma_020": CrisisSituation(
        id="trauma_020",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Свидетель пожара с жертвами",
        description="Видел пожар с погибшими",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["видел пожар", "люди сгорели", "свидетель пожара"],
    ),

    "trauma_021": CrisisSituation(
        id="trauma_021",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Свидетель насилия над ребёнком",
        description="Видел насилие над ребёнком",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["видел насилие над ребёнком", "бьют ребёнка"],
    ),

    "trauma_022": CrisisSituation(
        id="trauma_022",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="ПТСР после службы в армии",
        description="Посттравматическое стрессовое расстройство после армии",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["птср", "армия", "после армии", "военная травма"],
    ),

    "trauma_023": CrisisSituation(
        id="trauma_023",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Травма от медицинского вмешательства",
        description="Травма от операции, родов или другого медицинского вмешательства",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["травма от операции", "травма от родов", "медицинская травма"],
    ),

    "trauma_024": CrisisSituation(
        id="trauma_024",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Заложничество",
        description="Был заложником",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["был заложником", "заложничество", "захват"],
    ),

    "trauma_025": CrisisSituation(
        id="trauma_025",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Групповое изнасилование",
        description="Групповое изнасилование",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["групповое изнасилование", "изнасиловали несколько"],
    ),

    "trauma_026": CrisisSituation(
        id="trauma_026",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Изнасилование знакомым",
        description="Изнасилование знакомым или партнёром",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["изнасиловал знакомый", "изнасиловал партнёр", "насилие в отношениях"],
    ),

    "trauma_027": CrisisSituation(
        id="trauma_027",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Домашнее насилие (экономическое)",
        description="Экономическое насилие от партнёра",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["экономическое насилие", "не даёт денег", "контролирует деньги"],
    ),

    "trauma_028": CrisisSituation(
        id="trauma_028",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Избиение родителями в детстве",
        description="Физическое насилие от родителей в детстве",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["били родители", "насилие в детстве", "избивали в детстве"],
    ),

    "trauma_029": CrisisSituation(
        id="trauma_029",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Свидетель суицида",
        description="Видел, как человек покончил с собой",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["видел суицид", "видел самоубийство", "свидетель суицида"],
    ),

    "trauma_030": CrisisSituation(
        id="trauma_030",
        category=CrisisCategory.TRAUMA_VIOLENCE,
        title="Газлайтинг в отношениях",
        description="Психологическое насилие через газлайтинг",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["газлайтинг", "манипуляция", "сомневаюсь в себе"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 3: ОТНОШЕНИЯ И РАЗРЫВЫ (25 ситуаций)
    # ========================================================================
    "rel_001": CrisisSituation(
        id="rel_001",
        category=CrisisCategory.RELATIONSHIPS,
        title="Развод после многих лет брака",
        description="Развод после 10+, 20+, 30+ лет брака",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["развод", "разводимся", "ушла жена", "ушёл муж"],
    ),

    "rel_002": CrisisSituation(
        id="rel_002",
        category=CrisisCategory.RELATIONSHIPS,
        title="Измена супруга",
        description="Измена мужа или жены",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["изменил", "изменила", "измена", "изменяет"],
    ),

    "rel_003": CrisisSituation(
        id="rel_003",
        category=CrisisCategory.RELATIONSHIPS,
        title="Расставание",
        description="Расставание с долгосрочным партнёром",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["расстались", "расставание", "бросил", "бросила"],
    ),

    "rel_004": CrisisSituation(
        id="rel_004",
        category=CrisisCategory.RELATIONSHIPS,
        title="Конфликт с родителями",
        description="Разрыв отношений с родителями",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с родителями", "не общаюсь с родителями"],
    ),

    "rel_005": CrisisSituation(
        id="rel_005",
        category=CrisisCategory.RELATIONSHIPS,
        title="Потеря дружбы",
        description="Предательство друга, потеря дружбы",
        severity="medium",
        recommended_approach=["ACT", "CBT"],
        keywords=["предал друг", "потерял друга", "конфликт с другом"],
    ),

    "rel_006": CrisisSituation(
        id="rel_006",
        category=CrisisCategory.RELATIONSHIPS,
        title="Токсичные отношения",
        description="Невозможность уйти из токсичных отношений",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["токсичные отношения", "не могу уйти", "абьюз"],
    ),

    "rel_007": CrisisSituation(
        id="rel_007",
        category=CrisisCategory.RELATIONSHIPS,
        title="Эмоциональная зависимость от партнёра",
        description="Эмоциональная зависимость, невозможность быть без партнёра",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от партнёра", "не могу без него", "эмоциональная зависимость"],
    ),

    "rel_008": CrisisSituation(
        id="rel_008",
        category=CrisisCategory.RELATIONSHIPS,
        title="Абьюзивные отношения",
        description="Абьюзивные отношения с партнёром",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["абьюз", "абьюзивные отношения", "насилие в отношениях"],
    ),

    "rel_009": CrisisSituation(
        id="rel_009",
        category=CrisisCategory.RELATIONSHIPS,
        title="Ревность партнёра",
        description="Патологическая ревность партнёра",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["ревность", "патологическая ревность", "контролирует"],
    ),

    "rel_010": CrisisSituation(
        id="rel_010",
        category=CrisisCategory.RELATIONSHIPS,
        title="Невозможность найти партнёра",
        description="Длительное одиночество, невозможность найти партнёра",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["не могу найти партнёра", "никто не нужен", "одиночество"],
    ),

    "rel_011": CrisisSituation(
        id="rel_011",
        category=CrisisCategory.RELATIONSHIPS,
        title="Нежелательная беременность",
        description="Нежелательная беременность, конфликт с партнёром",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["нежелательная беременность", "не хочу ребёнка", "беременность"],
    ),

    "rel_012": CrisisSituation(
        id="rel_012",
        category=CrisisCategory.RELATIONSHIPS,
        title="Аборт",
        description="Аборт, конфликт с партнёром или родителями",
        severity="high",
        recommended_approach=["ACT", "grief_module"],
        keywords=["аборт", "сделала аборт", "прервала беременность"],
    ),

    "rel_013": CrisisSituation(
        id="rel_013",
        category=CrisisCategory.RELATIONSHIPS,
        title="Бесплодие",
        description="Бесплодие, конфликт в паре",
        severity="high",
        recommended_approach=["ACT", "grief_module"],
        keywords=["бесплодие", "не могу забеременеть", "не можем иметь детей"],
    ),

    "rel_014": CrisisSituation(
        id="rel_014",
        category=CrisisCategory.RELATIONSHIPS,
        title="Сексуальная несовместимость",
        description="Сексуальная несовместимость в паре",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["сексуальная несовместимость", "нет секса", "проблемы в постели"],
    ),

    "rel_015": CrisisSituation(
        id="rel_015",
        category=CrisisCategory.RELATIONSHIPS,
        title="Финансовые конфликты в паре",
        description="Финансовые конфликты с партнёром",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["конфликт из-за денег", "финансовые проблемы в паре"],
    ),

    "rel_016": CrisisSituation(
        id="rel_016",
        category=CrisisCategory.RELATIONSHIPS,
        title="Конфликт из-за родителей партнёра",
        description="Конфликт из-за свекрови, тёщи",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["свекровь", "тёща", "конфликт с родителями партнёра"],
    ),

    "rel_017": CrisisSituation(
        id="rel_017",
        category=CrisisCategory.RELATIONSHIPS,
        title="Развод с детьми",
        description="Развод при наличии детей",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["развод с детьми", "дети при разводе"],
    ),

    "rel_018": CrisisSituation(
        id="rel_018",
        category=CrisisCategory.RELATIONSHIPS,
        title="Измена с лучшим другом",
        description="Измена супруга с лучшим другом/подругой",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["изменил с другом", "изменила с подругой"],
    ),

    "rel_019": CrisisSituation(
        id="rel_019",
        category=CrisisCategory.RELATIONSHIPS,
        title="Расставание из-за переезда",
        description="Расставание из-за переезда в другой город/страну",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["расстались из-за переезда", "переезд", "расстояние"],
    ),

    "rel_020": CrisisSituation(
        id="rel_020",
        category=CrisisCategory.RELATIONSHIPS,
        title="Расставание из-за разных взглядов на детей",
        description="Расставание из-за разных взглядов на детей",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["расстались из-за детей", "не хочет детей", "хочу детей"],
    ),

    "rel_021": CrisisSituation(
        id="rel_021",
        category=CrisisCategory.RELATIONSHIPS,
        title="Конфликт с детьми",
        description="Отчуждение от детей, конфликт",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с детьми", "дети не общаются", "отчуждение"],
    ),

    "rel_022": CrisisSituation(
        id="rel_022",
        category=CrisisCategory.RELATIONSHIPS,
        title="Конфликт с братьями/сёстрами",
        description="Конфликт с братьями или сёстрами",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с братом", "конфликт с сестрой"],
    ),

    "rel_023": CrisisSituation(
        id="rel_023",
        category=CrisisCategory.RELATIONSHIPS,
        title="Конфликт с лучшим другом",
        description="Конфликт с лучшим другом/подругой",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с другом", "поссорились с другом"],
    ),

    "rel_024": CrisisSituation(
        id="rel_024",
        category=CrisisCategory.RELATIONSHIPS,
        title="Расставание по инициативе партнёра",
        description="Неожиданное расставание по инициативе партнёра",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["бросил меня", "бросила меня", "ушёл", "ушла"],
    ),

    "rel_025": CrisisSituation(
        id="rel_025",
        category=CrisisCategory.RELATIONSHIPS,
        title="Измена во время беременности",
        description="Измена партнёра во время беременности",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["изменил во время беременности", "изменила беременной"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 4: ЗДОРОВЬЕ И БОЛЕЗНИ (25 ситуаций)
    # ========================================================================
    "health_001": CrisisSituation(
        id="health_001",
        category=CrisisCategory.HEALTH,
        title="Диагноз рак",
        description="Диагноз рак (себе или близкому)",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["рак", "онкология", "диагноз рак", "опухоль"],
    ),

    "health_002": CrisisSituation(
        id="health_002",
        category=CrisisCategory.HEALTH,
        title="Диагноз ВИЧ",
        description="Диагноз ВИЧ",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["вич", "спид", "диагноз вич"],
    ),

    "health_003": CrisisSituation(
        id="health_003",
        category=CrisisCategory.HEALTH,
        title="Инвалидность",
        description="Инвалидность после ДТП или инсульта",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["инвалидность", "инвалид", "потерял ногу", "потерял руку"],
    ),

    "health_004": CrisisSituation(
        id="health_004",
        category=CrisisCategory.HEALTH,
        title="Хроническая боль",
        description="Хроническая боль",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["хроническая боль", "постоянная боль", "боль не проходит"],
    ),

    "health_005": CrisisSituation(
        id="health_005",
        category=CrisisCategory.HEALTH,
        title="Панические атаки",
        description="Панические атаки",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["паническая атака", "панические атаки", "па"],
    ),

    "health_006": CrisisSituation(
        id="health_006",
        category=CrisisCategory.HEALTH,
        title="Депрессия",
        description="Клиническая депрессия",
        severity="high",
        recommended_approach=["CBT", "ACT"],
        keywords=["депрессия", "депрессивное расстройство"],
    ),

    "health_007": CrisisSituation(
        id="health_007",
        category=CrisisCategory.HEALTH,
        title="Тревожное расстройство",
        description="Тревожное расстройство",
        severity="high",
        recommended_approach=["CBT", "DBT"],
        keywords=["тревожное расстройство", "генерализованная тревога"],
    ),

    "health_008": CrisisSituation(
        id="health_008",
        category=CrisisCategory.HEALTH,
        title="ОКР",
        description="Обсессивно-компульсивное расстройство",
        severity="high",
        recommended_approach=["CBT", "DBT"],
        keywords=["окр", "обсессии", "компульсии", "навязчивые мысли"],
    ),

    "health_009": CrisisSituation(
        id="health_009",
        category=CrisisCategory.HEALTH,
        title="Расстройство пищевого поведения",
        description="Анорексия, булимия, компульсивное переедание",
        severity="critical",
        recommended_approach=["DBT", "crisis_contacts"],
        keywords=["анорексия", "булимия", "переедание", "рпп"],
    ),

    "health_010": CrisisSituation(
        id="health_010",
        category=CrisisCategory.HEALTH,
        title="Зависимость от лекарств",
        description="Зависимость от лекарств после лечения",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["зависимость от лекарств", "бензодиазепины", "опиоиды"],
    ),

    "health_011": CrisisSituation(
        id="health_011",
        category=CrisisCategory.HEALTH,
        title="Послеродовая депрессия",
        description="Послеродовая депрессия",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["послеродовая депрессия", "после родов", "не могу с ребёнком"],
    ),

    "health_012": CrisisSituation(
        id="health_012",
        category=CrisisCategory.HEALTH,
        title="Менопауза",
        description="Тяжёлая менопауза",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["менопауза", "климакс", "приливы"],
    ),

    "health_013": CrisisSituation(
        id="health_013",
        category=CrisisCategory.HEALTH,
        title="Диагноз неизлечимой болезни",
        description="Диагноз БАС, рассеянный склероз, другие неизлечимые болезни",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["неизлечимая болезнь", "бас", "рассеянный склероз"],
    ),

    "health_014": CrisisSituation(
        id="health_014",
        category=CrisisCategory.HEALTH,
        title="Инвалидность после инсульта",
        description="Инвалидность после инсульта",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["инсульт", "после инсульта", "парализовало"],
    ),

    "health_015": CrisisSituation(
        id="health_015",
        category=CrisisCategory.HEALTH,
        title="Потеря конечности",
        description="Потеря руки или ноги",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["потерял ногу", "потерял руку", "ампутация"],
    ),

    "health_016": CrisisSituation(
        id="health_016",
        category=CrisisCategory.HEALTH,
        title="Потеря зрения",
        description="Потеря зрения",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["потерял зрение", "ослеп", "слепота"],
    ),

    "health_017": CrisisSituation(
        id="health_017",
        category=CrisisCategory.HEALTH,
        title="Потеря слуха",
        description="Потеря слуха",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["потерял слух", "оглох", "глухота"],
    ),

    "health_018": CrisisSituation(
        id="health_018",
        category=CrisisCategory.HEALTH,
        title="Диагноз деменции",
        description="Диагноз деменции (себе или близкому)",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["деменция", "альцгеймер", "забываю всё"],
    ),

    "health_019": CrisisSituation(
        id="health_019",
        category=CrisisCategory.HEALTH,
        title="Диагноз диабета",
        description="Диагноз диабета",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["диабет", "сахарный диабет", "инсулин"],
    ),

    "health_020": CrisisSituation(
        id="health_020",
        category=CrisisCategory.HEALTH,
        title="Диагноз сердечно-сосудистого заболевания",
        description="Диагноз сердечно-сосудистого заболевания",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["болезнь сердца", "сердечно-сосудистое", "инфаркт"],
    ),

    "health_021": CrisisSituation(
        id="health_021",
        category=CrisisCategory.HEALTH,
        title="Импотенция",
        description="Импотенция, сексуальная дисфункция",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["импотенция", "эректильная дисфункция", "не встаёт"],
    ),

    "health_022": CrisisSituation(
        id="health_022",
        category=CrisisCategory.HEALTH,
        title="Хроническая усталость",
        description="Хроническая усталость, выгорание",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["хроническая усталость", "постоянно устал", "нет сил"],
    ),

    "health_023": CrisisSituation(
        id="health_023",
        category=CrisisCategory.HEALTH,
        title="Диагноз психического расстройства",
        description="Диагноз шизофрении, биполярного расстройства",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["шизофрения", "биполярное расстройство", "психоз"],
    ),

    "health_024": CrisisSituation(
        id="health_024",
        category=CrisisCategory.HEALTH,
        title="Проблемы со сном",
        description="Хроническая бессонница",
        severity="medium",
        recommended_approach=["CBT", "DBT"],
        keywords=["бессонница", "не могу спать", "проблемы со сном"],
    ),

    "health_025": CrisisSituation(
        id="health_025",
        category=CrisisCategory.HEALTH,
        title="Диагноз гепатита",
        description="Диагноз гепатита B или C",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["гепатит", "гепатит б", "гепатит ц"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 5: РАБОТА И КАРЬЕРА (20 ситуаций)
    # ========================================================================
    "work_001": CrisisSituation(
        id="work_001",
        category=CrisisCategory.WORK_CAREER,
        title="Увольнение",
        description="Неожиданное увольнение",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["уволили", "увольнение", "потерял работу"],
    ),

    "work_002": CrisisSituation(
        id="work_002",
        category=CrisisCategory.WORK_CAREER,
        title="Банкротство бизнеса",
        description="Банкротство собственного бизнеса",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["банкротство", "бизнес обанкротился", "разорился"],
    ),

    "work_003": CrisisSituation(
        id="work_003",
        category=CrisisCategory.WORK_CAREER,
        title="Выгорание",
        description="Профессиональное выгорание",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["выгорание", "выгорел", "эмоциональное выгорание"],
    ),

    "work_004": CrisisSituation(
        id="work_004",
        category=CrisisCategory.WORK_CAREER,
        title="Моббинг на работе",
        description="Травля на работе",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["травля на работе", "моббинг", "травят на работе"],
    ),

    "work_005": CrisisSituation(
        id="work_005",
        category=CrisisCategory.WORK_CAREER,
        title="Увольнение после многих лет работы",
        description="Увольнение после многих лет работы в одной компании",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["уволили после", "проработал много лет", "отдал компании"],
    ),

    "work_006": CrisisSituation(
        id="work_006",
        category=CrisisCategory.WORK_CAREER,
        title="Сокращение",
        description="Сокращение штата",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["сокращение", "сократили", "сокращают"],
    ),

    "work_007": CrisisSituation(
        id="work_007",
        category=CrisisCategory.WORK_CAREER,
        title="Провал стартапа",
        description="Провал собственного стартапа",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["стартап провалился", "стартап закрылся", "провал стартапа"],
    ),

    "work_008": CrisisSituation(
        id="work_008",
        category=CrisisCategory.WORK_CAREER,
        title="Конфликт с начальником",
        description="Конфликт с начальником",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с начальником", "начальник", "босс"],
    ),

    "work_009": CrisisSituation(
        id="work_009",
        category=CrisisCategory.WORK_CAREER,
        title="Конфликт с коллегами",
        description="Конфликт с коллегами",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с коллегами", "коллеги", "не ладим"],
    ),

    "work_010": CrisisSituation(
        id="work_010",
        category=CrisisCategory.WORK_CAREER,
        title="Невозможность найти работу",
        description="Долгий поиск работы без результата",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не могу найти работу", "ищу работу", "безработица"],
    ),

    "work_011": CrisisSituation(
        id="work_011",
        category=CrisisCategory.WORK_CAREER,
        title="Работа не по специальности",
        description="Работа не по специальности, разочарование",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["работа не по специальности", "не то чем хотел", "разочарование в профессии"],
    ),

    "work_012": CrisisSituation(
        id="work_012",
        category=CrisisCategory.WORK_CAREER,
        title="Потеря смысла в работе",
        description="Потеря смысла в работе",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["нет смысла в работе", "зачем я работаю", "бессмысленная работа"],
    ),

    "work_013": CrisisSituation(
        id="work_013",
        category=CrisisCategory.WORK_CAREER,
        title="Переработки",
        description="Хронические переработки, усталость",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["переработки", "работаю по 12 часов", "нет времени"],
    ),

    "work_014": CrisisSituation(
        id="work_014",
        category=CrisisCategory.WORK_CAREER,
        title="Токсичная корпоративная культура",
        description="Токсичная корпоративная культура",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["токсичная культура", "токсичная компания", "ужасная атмосфера"],
    ),

    "work_015": CrisisSituation(
        id="work_015",
        category=CrisisCategory.WORK_CAREER,
        title="Дискриминация на работе",
        description="Дискриминация по возрасту, полу, национальности",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["дискриминация", "дискриминируют", "из-за возраста", "из-за пола"],
    ),

    "work_016": CrisisSituation(
        id="work_016",
        category=CrisisCategory.WORK_CAREER,
        title="Невыплата зарплаты",
        description="Невыплата зарплаты",
        severity="critical",
        recommended_approach=["SFBT", "crisis_contacts"],
        keywords=["не платят зарплату", "задержка зарплаты", "невыплата"],
    ),

    "work_017": CrisisSituation(
        id="work_017",
        category=CrisisCategory.WORK_CAREER,
        title="Понижение в должности",
        description="Понижение в должности",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["понизили", "понижение", "разжаловали"],
    ),

    "work_018": CrisisSituation(
        id="work_018",
        category=CrisisCategory.WORK_CAREER,
        title="Провал важного проекта",
        description="Провал важного проекта на работе",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["провалил проект", "проект провалился", "всё пошло не так"],
    ),

    "work_019": CrisisSituation(
        id="work_019",
        category=CrisisCategory.WORK_CAREER,
        title="Ошибка на работе с серьёзными последствиями",
        description="Ошибка на работе с серьёзными последствиями",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["ошибка на работе", "серьёзная ошибка", "косяк"],
    ),

    "work_020": CrisisSituation(
        id="work_020",
        category=CrisisCategory.WORK_CAREER,
        title="Трудоголизм",
        description="Зависимость от работы, трудоголизм",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["трудоголизм", "зависимость от работы", "не могу не работать"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 6: ИДЕНТИЧНОСТЬ И СМЫСЛ (20 ситуаций)
    # ========================================================================
    # Добавлю ключевые ситуации из каждой категории

    "identity_001": CrisisSituation(
        id="identity_001",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Потеря смысла жизни",
        description="Экзистенциальный кризис, потеря смысла",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["нет смысла", "бессмысленно", "зачем жить", "потерял смысл"],
    ),

    "identity_002": CrisisSituation(
        id="identity_002",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис среднего возраста",
        description="Кризис среднего возраста",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["кризис среднего возраста", "мне 40", "жизнь прошла"],
    ),

    "identity_003": CrisisSituation(
        id="identity_003",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Экзистенциальный кризис",
        description="Экзистенциальный кризис",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["экзистенциальный кризис", "кто я", "зачем я"],
    ),

    "identity_004": CrisisSituation(
        id="identity_004",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис идентичности",
        description="Кризис идентичности (кто я?)",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["кризис идентичности", "не знаю кто я", "потерял себя"],
    ),

    "identity_005": CrisisSituation(
        id="identity_005",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Конфликт ценностей",
        description="Внутренний конфликт ценностей",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт ценностей", "не знаю что важно", "противоречие"],
    ),

    "identity_006": CrisisSituation(
        id="identity_006",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Религиозный кризис",
        description="Потеря веры, религиозный кризис",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["потерял веру", "религиозный кризис", "не верю в бога"],
    ),

    "identity_007": CrisisSituation(
        id="identity_007",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис после выхода на пенсию",
        description="Кризис после выхода на пенсию",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["вышел на пенсию", "пенсия", "не знаю что делать"],
    ),

    "identity_008": CrisisSituation(
        id="identity_008",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Синдром опустевшего гнезда",
        description="Дети выросли и ушли, синдром опустевшего гнезда",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["дети выросли", "дети ушли", "опустевшее гнездо"],
    ),

    "identity_009": CrisisSituation(
        id="identity_009",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис после достижения цели",
        description="Кризис после достижения цели (а дальше что?)",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["достиг цели", "а дальше что", "пустота после успеха"],
    ),

    "identity_010": CrisisSituation(
        id="identity_010",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Невозможность реализовать мечту",
        description="Невозможность реализовать мечту",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["не могу реализовать мечту", "мечта недостижима"],
    ),

    "identity_011": CrisisSituation(
        id="identity_011",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Разочарование в профессии",
        description="Разочарование в профессии",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["разочарование в профессии", "не то чем хотел заниматься"],
    ),

    "identity_012": CrisisSituation(
        id="identity_012",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Разочарование в отношениях",
        description="Разочарование в отношениях",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["разочарование в отношениях", "не верю в любовь"],
    ),

    "identity_013": CrisisSituation(
        id="identity_013",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Чувство бессмысленности",
        description="Чувство бессмысленности существования",
        severity="critical",
        recommended_approach=["ACT", "PFA"],
        keywords=["бессмысленность", "всё бессмысленно", "нет смысла"],
    ),

    "identity_014": CrisisSituation(
        id="identity_014",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Страх старости",
        description="Страх старости",
        severity="medium",
        recommended_approach=["ACT", "CBT"],
        keywords=["боюсь стареть", "страх старости", "не хочу стареть"],
    ),

    "identity_015": CrisisSituation(
        id="identity_015",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис гендерной идентичности",
        description="Кризис гендерной идентичности",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["гендерная идентичность", "трансгендер", "не чувствую себя"],
    ),

    "identity_016": CrisisSituation(
        id="identity_016",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис сексуальной ориентации",
        description="Кризис сексуальной ориентации",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["сексуальная ориентация", "гомосексуальность", "бисексуальность"],
    ),

    "identity_017": CrisisSituation(
        id="identity_017",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Конфликт между личными желаниями и ожиданиями общества",
        description="Конфликт между личными желаниями и ожиданиями общества",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["ожидания общества", "давление общества", "не хочу как все"],
    ),

    "identity_018": CrisisSituation(
        id="identity_018",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Чувство упущенного времени",
        description="Чувство упущенного времени",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["упущенное время", "потерял время", "жизнь прошла мимо"],
    ),

    "identity_019": CrisisSituation(
        id="identity_019",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Сожаление о прошлых решениях",
        description="Сожаление о прошлых решениях",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["сожаление", "жалею", "не так сделал"],
    ),

    "identity_020": CrisisSituation(
        id="identity_020",
        category=CrisisCategory.IDENTITY_MEANING,
        title="Кризис после рождения ребёнка",
        description="Кризис после рождения ребёнка (ответственность за жизнь)",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["после рождения ребёнка", "ответственность за ребёнка", "не готов"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 7: СОЦИАЛЬНАЯ ИЗОЛЯЦИЯ (15 ситуаций)
    # ========================================================================
    "isolation_001": CrisisSituation(
        id="isolation_001",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Хроническое одиночество",
        description="Длительное одиночество, нет друзей",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["одиночество", "один", "нет друзей", "никого нет"],
    ),

    "isolation_002": CrisisSituation(
        id="isolation_002",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Отсутствие друзей",
        description="Отсутствие друзей",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["нет друзей", "ни с кем не общаюсь", "одинок"],
    ),

    "isolation_003": CrisisSituation(
        id="isolation_003",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Социальная тревожность",
        description="Социальная тревожность, невозможность общаться",
        severity="high",
        recommended_approach=["CBT", "DBT"],
        keywords=["социальная тревожность", "боюсь людей", "не могу общаться"],
    ),

    "isolation_004": CrisisSituation(
        id="isolation_004",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Переезд в новый город",
        description="Переезд в новый город, потеря связей",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["переехал", "новый город", "никого не знаю"],
    ),

    "isolation_005": CrisisSituation(
        id="isolation_005",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Эмиграция",
        description="Эмиграция, культурная изоляция",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["эмиграция", "уехал из страны", "культурная изоляция"],
    ),

    "isolation_006": CrisisSituation(
        id="isolation_006",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Изоляция после пандемии",
        description="Изоляция после пандемии",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["после пандемии", "разучился общаться", "изоляция"],
    ),

    "isolation_007": CrisisSituation(
        id="isolation_007",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Изоляция из-за болезни",
        description="Изоляция из-за хронической болезни",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["изоляция из-за болезни", "не могу выходить", "прикован к дому"],
    ),

    "isolation_008": CrisisSituation(
        id="isolation_008",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Изоляция из-за инвалидности",
        description="Изоляция из-за инвалидности",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["изоляция из-за инвалидности", "инвалид", "не могу выходить"],
    ),

    "isolation_009": CrisisSituation(
        id="isolation_009",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Изоляция в старости",
        description="Изоляция в старости",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["изоляция в старости", "старость", "все умерли"],
    ),

    "isolation_010": CrisisSituation(
        id="isolation_010",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Отсутствие семьи",
        description="Отсутствие семьи",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["нет семьи", "нет родных", "сирота"],
    ),

    "isolation_011": CrisisSituation(
        id="isolation_011",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Отсутствие романтических отношений",
        description="Длительное отсутствие романтических отношений",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["нет отношений", "никто не нужен", "одинок"],
    ),

    "isolation_012": CrisisSituation(
        id="isolation_012",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Чувство непонимания окружающими",
        description="Чувство непонимания окружающими",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["меня не понимают", "никто не понимает", "чужой"],
    ),

    "isolation_013": CrisisSituation(
        id="isolation_013",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Отчуждение от общества",
        description="Отчуждение от общества",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["отчуждение", "не вписываюсь", "чужой"],
    ),

    "isolation_014": CrisisSituation(
        id="isolation_014",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Изоляция из-за стигмы",
        description="Изоляция из-за стигмы (ВИЧ, психическое расстройство)",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["стигма", "избегают", "боятся"],
    ),

    "isolation_015": CrisisSituation(
        id="isolation_015",
        category=CrisisCategory.SOCIAL_ISOLATION,
        title="Изоляция из-за работы",
        description="Изоляция из-за работы (удалёнка, вахта)",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["удалёнка", "вахта", "изоляция из-за работы"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 8: ФИНАНСОВЫЕ КРИЗИСЫ (15 ситуаций)
    # ========================================================================
    "financial_001": CrisisSituation(
        id="financial_001",
        category=CrisisCategory.FINANCIAL,
        title="Банкротство",
        description="Личное банкротство, долги",
        severity="critical",
        recommended_approach=["SFBT", "ACT"],
        keywords=["банкротство", "долги", "кредиты", "не могу платить"],
    ),

    "financial_002": CrisisSituation(
        id="financial_002",
        category=CrisisCategory.FINANCIAL,
        title="Потеря жилья",
        description="Потеря жилья (ипотека, выселение)",
        severity="critical",
        recommended_approach=["PFA", "SFBT"],
        keywords=["потеря жилья", "выселение", "ипотека", "не могу платить"],
    ),

    "financial_003": CrisisSituation(
        id="financial_003",
        category=CrisisCategory.FINANCIAL,
        title="Долги",
        description="Долги (кредиты, микрозаймы)",
        severity="critical",
        recommended_approach=["SFBT", "ACT"],
        keywords=["долги", "кредиты", "микрозаймы", "коллекторы"],
    ),

    "financial_004": CrisisSituation(
        id="financial_004",
        category=CrisisCategory.FINANCIAL,
        title="Потеря работы без сбережений",
        description="Потеря работы без сбережений",
        severity="critical",
        recommended_approach=["PFA", "SFBT"],
        keywords=["потерял работу", "нет денег", "нет сбережений"],
    ),

    "financial_005": CrisisSituation(
        id="financial_005",
        category=CrisisCategory.FINANCIAL,
        title="Невозможность прокормить семью",
        description="Невозможность прокормить семью",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["не могу прокормить", "нечем кормить", "голодаем"],
    ),

    "financial_006": CrisisSituation(
        id="financial_006",
        category=CrisisCategory.FINANCIAL,
        title="Мошенничество",
        description="Мошенничество, потеря сбережений",
        severity="critical",
        recommended_approach=["PFA", "SFBT"],
        keywords=["мошенничество", "обманули", "потерял деньги"],
    ),

    "financial_007": CrisisSituation(
        id="financial_007",
        category=CrisisCategory.FINANCIAL,
        title="Финансовая зависимость",
        description="Финансовая зависимость от партнёра/родителей",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["финансовая зависимость", "не могу уйти", "нет денег"],
    ),

    "financial_008": CrisisSituation(
        id="financial_008",
        category=CrisisCategory.FINANCIAL,
        title="Невозможность оплатить лечение",
        description="Невозможность оплатить лечение",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["не могу оплатить лечение", "нет денег на лечение"],
    ),

    "financial_009": CrisisSituation(
        id="financial_009",
        category=CrisisCategory.FINANCIAL,
        title="Невозможность оплатить образование детей",
        description="Невозможность оплатить образование детей",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не могу оплатить образование", "нет денег на учёбу"],
    ),

    "financial_010": CrisisSituation(
        id="financial_010",
        category=CrisisCategory.FINANCIAL,
        title="Потеря пенсии",
        description="Потеря пенсии или сбережений",
        severity="critical",
        recommended_approach=["PFA", "SFBT"],
        keywords=["потерял пенсию", "потерял сбережения"],
    ),

    "financial_011": CrisisSituation(
        id="financial_011",
        category=CrisisCategory.FINANCIAL,
        title="Финансовая эксплуатация",
        description="Финансовая эксплуатация родственниками или партнёром",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["финансовая эксплуатация", "забирают деньги", "вымогают"],
    ),

    "financial_012": CrisisSituation(
        id="financial_012",
        category=CrisisCategory.FINANCIAL,
        title="Невозможность выплатить алименты",
        description="Невозможность выплатить алименты",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не могу платить алименты", "алименты", "долг по алиментам"],
    ),

    "financial_013": CrisisSituation(
        id="financial_013",
        category=CrisisCategory.FINANCIAL,
        title="Долг перед криминалом",
        description="Невозможность погасить долг перед криминалом",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["долг перед криминалом", "угрожают", "долг"],
    ),

    "financial_014": CrisisSituation(
        id="financial_014",
        category=CrisisCategory.FINANCIAL,
        title="Финансовый кризис из-за зависимости",
        description="Финансовый кризис из-за игромании или алкоголизма",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["проиграл всё", "пропил", "игромания"],
    ),

    "financial_015": CrisisSituation(
        id="financial_015",
        category=CrisisCategory.FINANCIAL,
        title="Банкротство бизнеса с долгами",
        description="Банкротство бизнеса с личными долгами",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["бизнес обанкротился", "личные долги", "поручительство"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 9: ЭКЗИСТЕНЦИАЛЬНЫЕ КРИЗИСЫ (15 ситуаций)
    # ========================================================================
    "existential_001": CrisisSituation(
        id="existential_001",
        category=CrisisCategory.EXISTENTIAL,
        title="Страх смерти",
        description="Танатофобия, страх смерти",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["боюсь умереть", "страх смерти", "танатофобия"],
    ),

    "existential_002": CrisisSituation(
        id="existential_002",
        category=CrisisCategory.EXISTENTIAL,
        title="Паническая атака с мыслями о смерти",
        description="Паническая атака с мыслями о смерти",
        severity="critical",
        recommended_approach=["PFA", "DBT"],
        keywords=["паническая атака", "умру", "сейчас умру"],
    ),

    "existential_003": CrisisSituation(
        id="existential_003",
        category=CrisisCategory.EXISTENTIAL,
        title="Осознание конечности жизни",
        description="Осознание конечности жизни",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["осознание смертности", "конечность жизни", "все умрут"],
    ),

    "existential_004": CrisisSituation(
        id="existential_004",
        category=CrisisCategory.EXISTENTIAL,
        title="Страх небытия",
        description="Страх небытия после смерти",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["страх небытия", "что после смерти", "ничего не будет"],
    ),

    "existential_005": CrisisSituation(
        id="existential_005",
        category=CrisisCategory.EXISTENTIAL,
        title="Кризис после смерти близкого",
        description="Осознание собственной смертности после смерти близкого",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["осознание смертности", "я тоже умру", "после смерти близкого"],
    ),

    "existential_006": CrisisSituation(
        id="existential_006",
        category=CrisisCategory.EXISTENTIAL,
        title="Чувство бессмысленности существования",
        description="Чувство бессмысленности существования",
        severity="critical",
        recommended_approach=["ACT", "PFA"],
        keywords=["бессмысленность", "зачем всё это", "нет смысла"],
    ),

    "existential_007": CrisisSituation(
        id="existential_007",
        category=CrisisCategory.EXISTENTIAL,
        title="Депрессия с экзистенциальным компонентом",
        description="Депрессия с экзистенциальным компонентом",
        severity="critical",
        recommended_approach=["ACT", "CBT"],
        keywords=["депрессия", "нет смысла", "зачем жить"],
    ),

    "existential_008": CrisisSituation(
        id="existential_008",
        category=CrisisCategory.EXISTENTIAL,
        title="Страх старения",
        description="Страх старения",
        severity="medium",
        recommended_approach=["ACT", "CBT"],
        keywords=["боюсь стареть", "страх старости", "не хочу стареть"],
    ),

    "existential_009": CrisisSituation(
        id="existential_009",
        category=CrisisCategory.EXISTENTIAL,
        title="Страх потери контроля",
        description="Страх потери контроля над жизнью",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["страх потери контроля", "не контролирую", "всё рушится"],
    ),

    "existential_010": CrisisSituation(
        id="existential_010",
        category=CrisisCategory.EXISTENTIAL,
        title="Страх неизвестности",
        description="Страх неизвестности",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["страх неизвестности", "не знаю что будет", "неопределённость"],
    ),

    "existential_011": CrisisSituation(
        id="existential_011",
        category=CrisisCategory.EXISTENTIAL,
        title="Кризис после диагноза смертельной болезни",
        description="Кризис после диагноза смертельной болезни",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["смертельная болезнь", "скоро умру", "диагноз"],
    ),

    "existential_012": CrisisSituation(
        id="existential_012",
        category=CrisisCategory.EXISTENTIAL,
        title="Кризис после клинической смерти",
        description="Кризис после пережитой клинической смерти",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["клиническая смерть", "был мёртв", "пережил смерть"],
    ),

    "existential_013": CrisisSituation(
        id="existential_013",
        category=CrisisCategory.EXISTENTIAL,
        title="Кризис после теракта",
        description="Осознание хрупкости жизни после теракта или катастрофы",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["после теракта", "хрупкость жизни", "мог умереть"],
    ),

    "existential_014": CrisisSituation(
        id="existential_014",
        category=CrisisCategory.EXISTENTIAL,
        title="Философский кризис",
        description="Философский кризис (зачем всё это?)",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["философский кризис", "зачем всё это", "в чём смысл"],
    ),

    "existential_015": CrisisSituation(
        id="existential_015",
        category=CrisisCategory.EXISTENTIAL,
        title="Кризис после рождения ребёнка",
        description="Осознание ответственности за жизнь после рождения ребёнка",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["после рождения ребёнка", "ответственность за жизнь", "страшно"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 10: ЗАВИСИМОСТИ (20 ситуаций)
    # ========================================================================
    "addiction_001": CrisisSituation(
        id="addiction_001",
        category=CrisisCategory.ADDICTION,
        title="Алкогольная зависимость",
        description="Алкогольная зависимость (себе или близкому)",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["алкоголизм", "пью", "алкоголь", "зависимость от алкоголя"],
    ),

    "addiction_002": CrisisSituation(
        id="addiction_002",
        category=CrisisCategory.ADDICTION,
        title="Алкогольная зависимость близкого",
        description="Алкогольная зависимость у близкого человека",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["муж пьёт", "жена пьёт", "родитель алкоголик"],
    ),

    "addiction_003": CrisisSituation(
        id="addiction_003",
        category=CrisisCategory.ADDICTION,
        title="Наркотическая зависимость",
        description="Наркотическая зависимость",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["наркотики", "наркозависимость", "употребляю"],
    ),

    "addiction_004": CrisisSituation(
        id="addiction_004",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от лекарств",
        description="Зависимость от бензодиазепинов, опиоидов",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["зависимость от лекарств", "бензодиазепины", "опиоиды"],
    ),

    "addiction_005": CrisisSituation(
        id="addiction_005",
        category=CrisisCategory.ADDICTION,
        title="Игромания",
        description="Игромания (казино, ставки)",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["игромания", "казино", "ставки", "проиграл всё"],
    ),

    "addiction_006": CrisisSituation(
        id="addiction_006",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от компьютерных игр",
        description="Зависимость от компьютерных игр",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от игр", "играю сутками", "не могу оторваться"],
    ),

    "addiction_007": CrisisSituation(
        id="addiction_007",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от социальных сетей",
        description="Зависимость от социальных сетей",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от соцсетей", "постоянно в телефоне", "не могу оторваться"],
    ),

    "addiction_008": CrisisSituation(
        id="addiction_008",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от порнографии",
        description="Зависимость от порнографии",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от порно", "порнозависимость", "не могу остановиться"],
    ),

    "addiction_009": CrisisSituation(
        id="addiction_009",
        category=CrisisCategory.ADDICTION,
        title="Сексуальная зависимость",
        description="Сексуальная зависимость",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["сексуальная зависимость", "секс-зависимость", "не могу контролировать"],
    ),

    "addiction_010": CrisisSituation(
        id="addiction_010",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от работы",
        description="Трудоголизм, зависимость от работы",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["трудоголизм", "зависимость от работы", "не могу не работать"],
    ),

    "addiction_011": CrisisSituation(
        id="addiction_011",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от еды",
        description="Компульсивное переедание",
        severity="high",
        recommended_approach=["DBT", "ACT"],
        keywords=["компульсивное переедание", "не могу остановиться", "заедаю стресс"],
    ),

    "addiction_012": CrisisSituation(
        id="addiction_012",
        category=CrisisCategory.ADDICTION,
        title="Созависимость (партнёр-алкоголик)",
        description="Созависимость с партнёром-алкоголиком",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["созависимость", "партнёр алкоголик", "не могу уйти"],
    ),

    "addiction_013": CrisisSituation(
        id="addiction_013",
        category=CrisisCategory.ADDICTION,
        title="Созависимость (родитель-алкоголик)",
        description="Созависимость с родителем-алкоголиком",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["созависимость", "родитель алкоголик", "мама пьёт", "папа пьёт"],
    ),

    "addiction_014": CrisisSituation(
        id="addiction_014",
        category=CrisisCategory.ADDICTION,
        title="Созависимость (ребёнок-наркоман)",
        description="Созависимость с ребёнком-наркоманом",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["созависимость", "ребёнок наркоман", "сын наркоман", "дочь наркоман"],
    ),

    "addiction_015": CrisisSituation(
        id="addiction_015",
        category=CrisisCategory.ADDICTION,
        title="Рецидив после лечения",
        description="Рецидив зависимости после лечения",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["рецидив", "сорвался", "снова начал"],
    ),

    "addiction_016": CrisisSituation(
        id="addiction_016",
        category=CrisisCategory.ADDICTION,
        title="Невозможность бросить курить",
        description="Невозможность бросить курить",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["не могу бросить курить", "курение", "никотиновая зависимость"],
    ),

    "addiction_017": CrisisSituation(
        id="addiction_017",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от азартных игр онлайн",
        description="Зависимость от азартных игр онлайн",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["онлайн казино", "ставки онлайн", "проиграл всё"],
    ),

    "addiction_018": CrisisSituation(
        id="addiction_018",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от шопинга",
        description="Зависимость от шопинга",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от шопинга", "не могу не покупать", "трачу всё"],
    ),

    "addiction_019": CrisisSituation(
        id="addiction_019",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от отношений",
        description="Зависимость от отношений (невозможность быть одному)",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от отношений", "не могу быть один", "любовная зависимость"],
    ),

    "addiction_020": CrisisSituation(
        id="addiction_020",
        category=CrisisCategory.ADDICTION,
        title="Зависимость от одобрения",
        description="Зависимость от одобрения окружающих",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от одобрения", "нужно одобрение", "не могу без похвалы"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 11: СЕМЬЯ И ДЕТИ (20 ситуаций)
    # ========================================================================
    "family_001": CrisisSituation(
        id="family_001",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Конфликт с подростком",
        description="Конфликт с ребёнком-подростком",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["конфликт с ребёнком", "подросток", "не слушается"],
    ),

    "family_002": CrisisSituation(
        id="family_002",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Ребёнок-наркоман",
        description="Ребёнок употребляет наркотики",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["ребёнок наркоман", "сын наркоман", "дочь наркоман"],
    ),

    "family_003": CrisisSituation(
        id="family_003",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Ребёнок в тюрьме",
        description="Ребёнок в тюрьме",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["ребёнок в тюрьме", "сын в тюрьме", "дочь в тюрьме"],
    ),

    "family_004": CrisisSituation(
        id="family_004",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Ребёнок с инвалидностью",
        description="Ребёнок с инвалидностью",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["ребёнок инвалид", "инвалидность у ребёнка"],
    ),

    "family_005": CrisisSituation(
        id="family_005",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Ребёнок с психическим расстройством",
        description="Ребёнок с психическим расстройством",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["ребёнок с психическим расстройством", "психоз у ребёнка"],
    ),

    "family_006": CrisisSituation(
        id="family_006",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Ребёнок отказывается общаться",
        description="Ребёнок отказывается общаться, отчуждение",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["ребёнок не общается", "отчуждение от ребёнка"],
    ),

    "family_007": CrisisSituation(
        id="family_007",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Конфликт из-за воспитания детей",
        description="Конфликт с партнёром из-за воспитания детей",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["конфликт из-за воспитания", "не сходимся в воспитании"],
    ),

    "family_008": CrisisSituation(
        id="family_008",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Конфликт с родителями",
        description="Конфликт с токсичными родителями",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["токсичные родители", "конфликт с родителями"],
    ),

    "family_009": CrisisSituation(
        id="family_009",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Уход за больным родителем",
        description="Уход за больным родителем, выгорание",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["уход за родителем", "больной родитель", "выгорание"],
    ),

    "family_010": CrisisSituation(
        id="family_010",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Уход за больным ребёнком",
        description="Уход за больным ребёнком, выгорание",
        severity="critical",
        recommended_approach=["ACT", "DBT"],
        keywords=["уход за ребёнком", "больной ребёнок", "выгорание"],
    ),

    "family_011": CrisisSituation(
        id="family_011",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Невозможность иметь детей",
        description="Бесплодие, невозможность иметь детей",
        severity="high",
        recommended_approach=["ACT", "grief_module"],
        keywords=["бесплодие", "не могу иметь детей"],
    ),

    "family_012": CrisisSituation(
        id="family_012",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Нежелание иметь детей",
        description="Нежелание иметь детей, давление общества",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["не хочу детей", "давление иметь детей"],
    ),

    "family_013": CrisisSituation(
        id="family_013",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Аборт",
        description="Аборт, чувство вины",
        severity="high",
        recommended_approach=["ACT", "grief_module"],
        keywords=["аборт", "чувство вины", "прервала беременность"],
    ),

    "family_014": CrisisSituation(
        id="family_014",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Отказ от ребёнка",
        description="Отказ от ребёнка, чувство вины",
        severity="critical",
        recommended_approach=["ACT", "grief_module"],
        keywords=["отказ от ребёнка", "отказалась от ребёнка", "чувство вины"],
    ),

    "family_015": CrisisSituation(
        id="family_015",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Усыновление",
        description="Усыновление, сложности адаптации",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["усыновление", "приёмный ребёнок", "адаптация"],
    ),

    "family_016": CrisisSituation(
        id="family_016",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Конфликт между детьми",
        description="Конфликт между детьми, ревность, агрессия",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["конфликт между детьми", "ревность", "дерутся"],
    ),

    "family_017": CrisisSituation(
        id="family_017",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Развод родителей",
        description="Развод родителей (глазами ребёнка)",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["родители разводятся", "развод родителей"],
    ),

    "family_018": CrisisSituation(
        id="family_018",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Алкоголизм родителя",
        description="Алкоголизм родителя",
        severity="critical",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["родитель алкоголик", "мама пьёт", "папа пьёт"],
    ),

    "family_019": CrisisSituation(
        id="family_019",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Насилие в семье",
        description="Насилие в семье (свидетель)",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["насилие в семье", "видел насилие", "бьют маму"],
    ),

    "family_020": CrisisSituation(
        id="family_020",
        category=CrisisCategory.FAMILY_CHILDREN,
        title="Смерть ребёнка",
        description="Смерть ребёнка (СВДС, несчастный случай, болезнь)",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["умер ребёнок", "смерть ребёнка", "потерял ребёнка"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 12: ПРАВОВЫЕ ПРОБЛЕМЫ (15 ситуаций)
    # ========================================================================
    "legal_001": CrisisSituation(
        id="legal_001",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Тюремное заключение",
        description="Тюремное заключение (себе или близкому)",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["тюрьма", "посадили", "сидит в тюрьме"],
    ),

    "legal_002": CrisisSituation(
        id="legal_002",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Судебный процесс (обвиняемый)",
        description="Судебный процесс (обвиняемый)",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["суд", "обвиняют", "судебный процесс"],
    ),

    "legal_003": CrisisSituation(
        id="legal_003",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Судебный процесс (жертва)",
        description="Судебный процесс (жертва)",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["суд", "жертва", "судебный процесс"],
    ),

    "legal_004": CrisisSituation(
        id="legal_004",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Лишение родительских прав",
        description="Лишение родительских прав",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["лишение родительских прав", "забрали ребёнка"],
    ),

    "legal_005": CrisisSituation(
        id="legal_005",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Лишение водительских прав",
        description="Лишение водительских прав",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["лишение прав", "забрали права", "без прав"],
    ),

    "legal_006": CrisisSituation(
        id="legal_006",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Уголовное дело",
        description="Конфликт с законом (уголовное дело)",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["уголовное дело", "возбудили дело", "следствие"],
    ),

    "legal_007": CrisisSituation(
        id="legal_007",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Административное дело",
        description="Конфликт с законом (административное дело)",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["административное дело", "штраф", "административка"],
    ),

    "legal_008": CrisisSituation(
        id="legal_008",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Долги перед государством",
        description="Долги перед государством (налоги, штрафы)",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["долги перед государством", "налоги", "штрафы"],
    ),

    "legal_009": CrisisSituation(
        id="legal_009",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Депортация",
        description="Депортация (угроза или факт)",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["депортация", "депортируют", "выдворение"],
    ),

    "legal_010": CrisisSituation(
        id="legal_010",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Потеря гражданства",
        description="Потеря гражданства",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["потеря гражданства", "лишили гражданства"],
    ),

    "legal_011": CrisisSituation(
        id="legal_011",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Конфликт с соседями (судебный)",
        description="Конфликт с соседями (судебный)",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["конфликт с соседями", "суд с соседями"],
    ),

    "legal_012": CrisisSituation(
        id="legal_012",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Конфликт с работодателем (судебный)",
        description="Конфликт с работодателем (судебный)",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["конфликт с работодателем", "суд с работодателем"],
    ),

    "legal_013": CrisisSituation(
        id="legal_013",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Ложное обвинение",
        description="Ложное обвинение",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["ложное обвинение", "обвиняют ложно", "не виноват"],
    ),

    "legal_014": CrisisSituation(
        id="legal_014",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Невозможность доказать невиновность",
        description="Невозможность доказать невиновность",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не могу доказать", "нет доказательств", "невиновен"],
    ),

    "legal_015": CrisisSituation(
        id="legal_015",
        category=CrisisCategory.LEGAL_JUSTICE,
        title="Условный срок",
        description="Условный срок",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["условный срок", "условка", "условное наказание"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 13: СТИХИЙНЫЕ БЕДСТВИЯ (10 ситуаций)
    # ========================================================================
    "disaster_001": CrisisSituation(
        id="disaster_001",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Потеря жилья в пожаре",
        description="Потеря жилья в пожаре или наводнении",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["пожар", "сгорел дом", "наводнение", "потерял жильё"],
    ),

    "disaster_002": CrisisSituation(
        id="disaster_002",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Потеря близких в стихийном бедствии",
        description="Потеря близких в стихийном бедствии",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["погибли в пожаре", "погибли в наводнении", "стихийное бедствие"],
    ),

    "disaster_003": CrisisSituation(
        id="disaster_003",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Землетрясение",
        description="Землетрясение (травма)",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["землетрясение", "был в землетрясении"],
    ),

    "disaster_004": CrisisSituation(
        id="disaster_004",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Ураган",
        description="Ураган, торнадо",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["ураган", "торнадо", "смерч"],
    ),

    "disaster_005": CrisisSituation(
        id="disaster_005",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Оползень",
        description="Оползень, сход лавины",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["оползень", "лавина", "сход лавины"],
    ),

    "disaster_006": CrisisSituation(
        id="disaster_006",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Потеря имущества в катастрофе",
        description="Потеря имущества в катастрофе",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["потеря имущества", "всё потерял", "катастрофа"],
    ),

    "disaster_007": CrisisSituation(
        id="disaster_007",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="ПТСР после стихийного бедствия",
        description="ПТСР после стихийного бедствия",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["птср", "после катастрофы", "после бедствия"],
    ),

    "disaster_008": CrisisSituation(
        id="disaster_008",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Эвакуация из зоны бедствия",
        description="Эвакуация из зоны бедствия",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["эвакуация", "эвакуировали", "зона бедствия"],
    ),

    "disaster_009": CrisisSituation(
        id="disaster_009",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Невозможность вернуться домой после катастрофы",
        description="Невозможность вернуться домой после катастрофы",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не могу вернуться домой", "дом разрушен", "зона отчуждения"],
    ),

    "disaster_010": CrisisSituation(
        id="disaster_010",
        category=CrisisCategory.NATURAL_DISASTERS,
        title="Потеря жилья в наводнении",
        description="Потеря жилья в наводнении",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["наводнение", "затопило дом", "потоп"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 14: ЦИФРОВЫЕ КРИЗИСЫ (15 ситуаций)
    # ========================================================================
    "digital_001": CrisisSituation(
        id="digital_001",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Кибербуллинг",
        description="Травля в интернете",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["кибербуллинг", "травля в интернете", "троллинг", "хейт"],
    ),

    "digital_002": CrisisSituation(
        id="digital_002",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Утечка личных данных",
        description="Утечка личных данных",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["утечка данных", "слили данные", "взломали"],
    ),

    "digital_003": CrisisSituation(
        id="digital_003",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Утечка интимных фото",
        description="Утечка интимных фото/видео",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["утечка фото", "слили фото", "интимные фото"],
    ),

    "digital_004": CrisisSituation(
        id="digital_004",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Шантаж в интернете",
        description="Шантаж в интернете",
        severity="critical",
        recommended_approach=["PFA", "crisis_contacts"],
        keywords=["шантаж", "шантажируют", "вымогают"],
    ),

    "digital_005": CrisisSituation(
        id="digital_005",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Взлом аккаунтов",
        description="Взлом аккаунтов",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["взлом", "взломали аккаунт", "украли аккаунт"],
    ),

    "digital_006": CrisisSituation(
        id="digital_006",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Мошенничество онлайн",
        description="Мошенничество онлайн (потеря денег)",
        severity="critical",
        recommended_approach=["PFA", "SFBT"],
        keywords=["мошенничество онлайн", "обманули в интернете", "потерял деньги"],
    ),

    "digital_007": CrisisSituation(
        id="digital_007",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Зависимость от социальных сетей",
        description="Зависимость от социальных сетей",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от соцсетей", "постоянно в телефоне"],
    ),

    "digital_008": CrisisSituation(
        id="digital_008",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Зависимость от онлайн-игр",
        description="Зависимость от онлайн-игр",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от игр", "играю сутками"],
    ),

    "digital_009": CrisisSituation(
        id="digital_009",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Сравнение себя с другими в соцсетях",
        description="Сравнение себя с другими в соцсетях (депрессия)",
        severity="high",
        recommended_approach=["ACT", "CBT"],
        keywords=["сравниваю себя", "все лучше меня", "депрессия от соцсетей"],
    ),

    "digital_010": CrisisSituation(
        id="digital_010",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="FOMO",
        description="FOMO (страх упустить что-то важное)",
        severity="medium",
        recommended_approach=["ACT", "CBT"],
        keywords=["fomo", "страх упустить", "все без меня"],
    ),

    "digital_011": CrisisSituation(
        id="digital_011",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Цифровая слежка",
        description="Цифровая слежка (партнёр, родители)",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["цифровая слежка", "следит через телефон", "контролирует"],
    ),

    "digital_012": CrisisSituation(
        id="digital_012",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Потеря работы из-за поста в соцсетях",
        description="Потеря работы из-за поста в соцсетях",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["уволили из-за поста", "пост в соцсетях"],
    ),

    "digital_013": CrisisSituation(
        id="digital_013",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Репутационный кризис в интернете",
        description="Репутационный кризис в интернете",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["репутационный кризис", "испортили репутацию", "травля"],
    ),

    "digital_014": CrisisSituation(
        id="digital_014",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Троллинг",
        description="Троллинг, хейт в интернете",
        severity="high",
        recommended_approach=["ACT", "crisis_contacts"],
        keywords=["троллинг", "хейт", "травят в интернете"],
    ),

    "digital_015": CrisisSituation(
        id="digital_015",
        category=CrisisCategory.TECHNOLOGY_DIGITAL,
        title="Зависимость от порнографии онлайн",
        description="Зависимость от порнографии онлайн",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["зависимость от порно", "порнозависимость"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 15: МЕДРАБОТНИКИ (20 ситуаций)
    # ========================================================================
    "med_001": CrisisSituation(
        id="med_001",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Выгорание медработника после COVID",
        description="Работал в красной зоне, ПТСР, не может вернуться к работе",
        severity="high",
        recommended_approach=["PFA", "ACT", "DBT"],
        keywords=["красная зона", "ковид", "выгорание врач", "выгорание медсестра", "не могу работать врачом", "птср медик"],
    ),

    "med_002": CrisisSituation(
        id="med_002",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Смерть пациента по своей вине",
        description="Врачебная ошибка, чувство вины, суицидальные мысли",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["врачебная ошибка", "пациент умер по моей вине", "я убил пациента", "ошибка врача", "виноват в смерти"],
    ),

    "med_003": CrisisSituation(
        id="med_003",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Смерть пациента не по своей вине",
        description="Сделал всё возможное, но пациент умер, чувство бессилия",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["не смог спасти", "пациент умер", "сделал всё что мог", "бессилие врач"],
    ),

    "med_004": CrisisSituation(
        id="med_004",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Множественные смерти за смену",
        description="Работа в реанимации/скорой, эмоциональное истощение",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["реанимация", "скорая помощь", "много смертей", "каждый день умирают", "истощение врач"],
    ),

    "med_005": CrisisSituation(
        id="med_005",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Агрессия от родственников пациента",
        description="Обвиняют, угрожают, физическое насилие",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["родственники угрожают", "напали на врача", "обвиняют врача", "агрессия родственников"],
    ),

    "med_006": CrisisSituation(
        id="med_006",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Судебный процесс за врачебную ошибку",
        description="Уголовное дело, страх тюрьмы, потеря репутации",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["суд врач", "уголовное дело врач", "тюрьма за ошибку", "судят врача"],
    ),

    "med_007": CrisisSituation(
        id="med_007",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Невозможность спасти ребёнка",
        description="Смерть ребёнка на операционном столе, травма",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["ребёнок умер", "не спас ребёнка", "смерть ребёнка операция", "детская смерть врач"],
    ),

    "med_008": CrisisSituation(
        id="med_008",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Работа в условиях нехватки ресурсов",
        description="Нет лекарств/оборудования, приходится выбирать кого спасать",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["нет лекарств", "нет оборудования", "выбирать кого спасать", "нехватка ресурсов больница"],
    ),

    "med_009": CrisisSituation(
        id="med_009",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Заражение на работе",
        description="Заразился от пациента (COVID, гепатит, ВИЧ), страх за семью",
        severity="high",
        recommended_approach=["PFA", "CBT"],
        keywords=["заразился на работе", "вич от пациента", "гепатит от пациента", "ковид от пациента", "страх заразить семью"],
    ),

    "med_010": CrisisSituation(
        id="med_010",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Моральная травма от эвтаназии",
        description="Пришлось отключить аппарат ИВЛ, чувство вины",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["отключил ивл", "эвтаназия", "отключил аппарат", "прекратил жизнеобеспечение"],
    ),

    "med_011": CrisisSituation(
        id="med_011",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Конфликт с коллегами из-за ошибки",
        description="Коллега допустил ошибку, пациент пострадал, моральная дилемма",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["коллега ошибся", "ошибка коллеги", "донести на врача", "скрыть ошибку"],
    ),

    "med_012": CrisisSituation(
        id="med_012",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Невозможность помочь близкому",
        description="Родственник болен, но ты не можешь его спасти",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["не могу спасти родственника", "близкий болен", "врач не может помочь своим"],
    ),

    "med_013": CrisisSituation(
        id="med_013",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Работа в военном госпитале",
        description="Раненые с СВО, ампутации, ПТСР",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["военный госпиталь", "раненые сво", "ампутации", "военная медицина"],
    ),

    "med_014": CrisisSituation(
        id="med_014",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Суицид коллеги",
        description="Коллега покончил с собой из-за выгорания",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["коллега покончил", "суицид врача", "врач покончил с собой"],
    ),

    "med_015": CrisisSituation(
        id="med_015",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Насилие от пациента",
        description="Пациент с психозом напал, травма",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["пациент напал", "избил пациент", "психоз пациент", "насилие от пациента"],
    ),

    "med_016": CrisisSituation(
        id="med_016",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Невыплата зарплаты медработникам",
        description="Работаешь на износ, но не платят",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не платят зарплату врач", "задержка зарплаты больница", "долг по зарплате медик"],
    ),

    "med_017": CrisisSituation(
        id="med_017",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Принуждение к фальсификации документов",
        description="Начальство требует скрыть врачебную ошибку",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["скрыть ошибку", "фальсификация медицинских документов", "заставляют врать"],
    ),

    "med_018": CrisisSituation(
        id="med_018",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Работа без отдыха",
        description="36-часовые смены, хроническая усталость, ошибки из-за усталости",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["36 часов смена", "работаю без сна", "усталость врач", "нет отдыха медик"],
    ),

    "med_019": CrisisSituation(
        id="med_019",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Потеря лицензии",
        description="Лишили права работать врачом, потеря идентичности",
        severity="critical",
        recommended_approach=["ACT", "SFBT"],
        keywords=["лишили лицензии", "не могу работать врачом", "отобрали право лечить"],
    ),

    "med_020": CrisisSituation(
        id="med_020",
        category=CrisisCategory.MEDICAL_WORKERS,
        title="Моральная травма от аборта",
        description="Делал аборт на позднем сроке, чувство вины",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["аборт поздний срок", "чувство вины аборт", "делал аборт"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 16: УЧИТЕЛЯ (15 ситуаций)
    # ========================================================================
    "teach_001": CrisisSituation(
        id="teach_001",
        category=CrisisCategory.TEACHERS,
        title="Травля от учеников",
        description="Буллинг, унижения, видео в интернете",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["травят ученики", "буллинг учитель", "унижают дети", "видео учитель интернет"],
    ),

    "teach_002": CrisisSituation(
        id="teach_002",
        category=CrisisCategory.TEACHERS,
        title="Травля от родителей",
        description="Жалобы, угрозы, давление",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["родители угрожают", "жалобы родителей", "травля от родителей", "давление родители"],
    ),

    "teach_003": CrisisSituation(
        id="teach_003",
        category=CrisisCategory.TEACHERS,
        title="Физическое насилие от ученика",
        description="Ученик ударил, травма",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["ученик ударил", "избил ученик", "насилие от ученика", "напал школьник"],
    ),

    "teach_004": CrisisSituation(
        id="teach_004",
        category=CrisisCategory.TEACHERS,
        title="Суицид ученика",
        description="Ученик покончил с собой, чувство вины",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["ученик покончил", "суицид школьник", "ученик покончил с собой", "не заметил признаки"],
    ),

    "teach_005": CrisisSituation(
        id="teach_005",
        category=CrisisCategory.TEACHERS,
        title="Обвинение в домогательствах",
        description="Ложное обвинение, потеря работы, репутации",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["обвинили в домогательствах", "ложное обвинение учитель", "обвинение педофилия"],
    ),

    "teach_006": CrisisSituation(
        id="teach_006",
        category=CrisisCategory.TEACHERS,
        title="Выгорание учителя",
        description="Не могу больше учить, потеря смысла",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["выгорание учитель", "не могу учить", "устал от школы", "потерял смысл учитель"],
    ),

    "teach_007": CrisisSituation(
        id="teach_007",
        category=CrisisCategory.TEACHERS,
        title="Невозможность помочь ученику",
        description="Вижу что ребёнка бьют дома, но не могу помочь",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["ребёнка бьют дома", "не могу помочь ученику", "насилие в семье ученика"],
    ),

    "teach_008": CrisisSituation(
        id="teach_008",
        category=CrisisCategory.TEACHERS,
        title="Конфликт с администрацией",
        description="Давление, требования фальсификации оценок",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["давление администрация", "завуч требует", "фальсификация оценок", "директор давит"],
    ),

    "teach_009": CrisisSituation(
        id="teach_009",
        category=CrisisCategory.TEACHERS,
        title="Низкая зарплата учителя",
        description="Не могу прокормить семью на зарплату учителя",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["маленькая зарплата учитель", "не хватает денег учитель", "нищета учитель"],
    ),

    "teach_010": CrisisSituation(
        id="teach_010",
        category=CrisisCategory.TEACHERS,
        title="Насилие в школе",
        description="Драка между учениками, кто-то ранен",
        severity="high",
        recommended_approach=["PFA"],
        keywords=["драка в школе", "ученик ранен", "насилие между учениками", "избили в школе"],
    ),

    "teach_011": CrisisSituation(
        id="teach_011",
        category=CrisisCategory.TEACHERS,
        title="Угрозы от родителей",
        description="Родитель угрожает расправой за плохую оценку",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["родитель угрожает расправой", "угрозы за оценку", "родитель угрожает убить"],
    ),

    "teach_012": CrisisSituation(
        id="teach_012",
        category=CrisisCategory.TEACHERS,
        title="Потеря авторитета",
        description="Ученики не слушаются, не могу контролировать класс",
        severity="medium",
        recommended_approach=["ACT", "SFBT"],
        keywords=["не слушаются ученики", "потерял контроль класс", "не уважают учителя"],
    ),

    "teach_013": CrisisSituation(
        id="teach_013",
        category=CrisisCategory.TEACHERS,
        title="Работа в опасной школе",
        description="Школа в криминальном районе, страх за жизнь",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["опасная школа", "криминальный район школа", "страх за жизнь учитель"],
    ),

    "teach_014": CrisisSituation(
        id="teach_014",
        category=CrisisCategory.TEACHERS,
        title="Моральная травма от наказания ученика",
        description="Наказал ученика, он пострадал",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["наказал ученика", "ученик пострадал", "чувство вины наказание"],
    ),

    "teach_015": CrisisSituation(
        id="teach_015",
        category=CrisisCategory.TEACHERS,
        title="Конфликт с коллегами",
        description="Травля от других учителей",
        severity="medium",
        recommended_approach=["DBT", "ACT"],
        keywords=["травля коллеги учителя", "конфликт в учительской", "буллинг от учителей"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 17: ВОЕННЫЕ И КОНТРАКТНИКИ (25 ситуаций)
    # ========================================================================
    "mil_001": CrisisSituation(
        id="mil_001",
        category=CrisisCategory.MILITARY,
        title="ПТСР после боевых действий",
        description="Кошмары, флешбэки, не могу спать",
        severity="critical",
        recommended_approach=["PFA", "DBT", "ACT"],
        keywords=["птср война", "кошмары война", "флешбэки", "не могу спать после войны", "боевые действия"],
    ),

    "mil_002": CrisisSituation(
        id="mil_002",
        category=CrisisCategory.MILITARY,
        title="Потеря сослуживца",
        description="Друг погиб на войне, чувство вины выжившего",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["друг погиб война", "сослуживец погиб", "чувство вины выжил", "все погибли я выжил"],
    ),

    "mil_003": CrisisSituation(
        id="mil_003",
        category=CrisisCategory.MILITARY,
        title="Ранение на войне",
        description="Потерял конечность, инвалидность",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["потерял ногу", "потерял руку", "ранение война", "инвалидность война", "ампутация"],
    ),

    "mil_004": CrisisSituation(
        id="mil_004",
        category=CrisisCategory.MILITARY,
        title="Контузия",
        description="Контузия, проблемы со слухом/зрением/памятью",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["контузия", "не слышу после войны", "проблемы с памятью война", "взрыв контузия"],
    ),

    "mil_005": CrisisSituation(
        id="mil_005",
        category=CrisisCategory.MILITARY,
        title="Убийство на войне",
        description="Убил человека, моральная травма",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["убил человека", "убил на войне", "моральная травма убийство", "не могу жить с этим"],
    ),

    "mil_006": CrisisSituation(
        id="mil_006",
        category=CrisisCategory.MILITARY,
        title="Плен",
        description="Был в плену, пытки, ПТСР",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["был в плену", "пытки", "плен война", "пленный"],
    ),

    "mil_007": CrisisSituation(
        id="mil_007",
        category=CrisisCategory.MILITARY,
        title="Дезертирство",
        description="Сбежал с войны, страх наказания, чувство вины",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["дезертир", "сбежал с войны", "дезертирство", "страх наказания"],
    ),

    "mil_008": CrisisSituation(
        id="mil_008",
        category=CrisisCategory.MILITARY,
        title="Невозможность вернуться к мирной жизни",
        description="После войны не могу адаптироваться",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["не могу адаптироваться", "после войны не могу", "вернулся с войны", "мирная жизнь"],
    ),

    "mil_009": CrisisSituation(
        id="mil_009",
        category=CrisisCategory.MILITARY,
        title="Конфликт с командованием",
        description="Приказ противоречит совести",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["приказ противоречит", "конфликт с командиром", "не могу выполнить приказ"],
    ),

    "mil_010": CrisisSituation(
        id="mil_010",
        category=CrisisCategory.MILITARY,
        title="Свидетель военных преступлений",
        description="Видел как убивают мирных, моральная травма",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["военные преступления", "убивают мирных", "видел зверства", "свидетель преступлений"],
    ),

    "mil_011": CrisisSituation(
        id="mil_011",
        category=CrisisCategory.MILITARY,
        title="Потеря отделения",
        description="Все погибли, я один выжил",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["все погибли", "один выжил", "потеря отделения", "весь взвод погиб"],
    ),

    "mil_012": CrisisSituation(
        id="mil_012",
        category=CrisisCategory.MILITARY,
        title="Ранение товарища",
        description="Не смог спасти, чувство вины",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не смог спасти товарища", "друг умер на руках", "не успел помочь"],
    ),

    "mil_013": CrisisSituation(
        id="mil_013",
        category=CrisisCategory.MILITARY,
        title="Страх перед боем",
        description="Паника перед отправкой на передовую",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["страх перед боем", "боюсь идти в бой", "паника передовая", "не хочу на фронт"],
    ),

    "mil_014": CrisisSituation(
        id="mil_014",
        category=CrisisCategory.MILITARY,
        title="Невозможность связаться с семьёй",
        description="Нет связи, не знаю живы ли близкие",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["нет связи с семьёй", "не знаю живы ли", "не могу позвонить домой"],
    ),

    "mil_015": CrisisSituation(
        id="mil_015",
        category=CrisisCategory.MILITARY,
        title="Конфликт с сослуживцами",
        description="Дедовщина, травля",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["дедовщина", "травля в армии", "избивают сослуживцы", "конфликт в части"],
    ),

    "mil_016": CrisisSituation(
        id="mil_016",
        category=CrisisCategory.MILITARY,
        title="Моральная травма от приказа",
        description="Выполнил приказ, который противоречит совести",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["выполнил приказ", "моральная травма приказ", "против совести"],
    ),

    "mil_017": CrisisSituation(
        id="mil_017",
        category=CrisisCategory.MILITARY,
        title="Адаптация после службы",
        description="Вернулся, но не могу найти работу/смысл",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["вернулся с войны", "не могу найти работу", "потерял смысл после войны"],
    ),

    "mil_018": CrisisSituation(
        id="mil_018",
        category=CrisisCategory.MILITARY,
        title="Алкоголизм после войны",
        description="Пью чтобы забыть",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["пью после войны", "алкоголизм война", "пью чтобы забыть"],
    ),

    "mil_019": CrisisSituation(
        id="mil_019",
        category=CrisisCategory.MILITARY,
        title="Суицидальные мысли после войны",
        description="Не вижу смысла жить",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["суицид после войны", "не вижу смысла жить", "хочу умереть после войны"],
    ),

    "mil_020": CrisisSituation(
        id="mil_020",
        category=CrisisCategory.MILITARY,
        title="Развод после войны",
        description="Жена не узнаёт меня, развод",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["развод после войны", "жена не узнаёт", "семья распалась война"],
    ),

    "mil_021": CrisisSituation(
        id="mil_021",
        category=CrisisCategory.MILITARY,
        title="Инвалидность после ранения",
        description="Потерял ногу/руку, не могу работать",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["инвалидность война", "не могу работать инвалид", "потерял конечность"],
    ),

    "mil_022": CrisisSituation(
        id="mil_022",
        category=CrisisCategory.MILITARY,
        title="Фантомные боли",
        description="После ампутации, хроническая боль",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["фантомные боли", "боль после ампутации", "хроническая боль"],
    ),

    "mil_023": CrisisSituation(
        id="mil_023",
        category=CrisisCategory.MILITARY,
        title="Невозможность говорить о войне",
        description="Никто не понимает, изоляция",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["не могу говорить о войне", "никто не понимает", "изоляция после войны"],
    ),

    "mil_024": CrisisSituation(
        id="mil_024",
        category=CrisisCategory.MILITARY,
        title="Чувство вины за выживание",
        description="Почему я выжил, а они нет",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["чувство вины выжил", "почему я выжил", "вина выжившего"],
    ),

    "mil_025": CrisisSituation(
        id="mil_025",
        category=CrisisCategory.MILITARY,
        title="Агрессия после войны",
        description="Не могу контролировать гнев, бью близких",
        severity="critical",
        recommended_approach=["PFA", "DBT"],
        keywords=["агрессия после войны", "не могу контролировать гнев", "бью близких", "насилие после войны"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 18: ПОЛИЦИЯ И СПАСАТЕЛИ (15 ситуаций)
    # ========================================================================
    "police_001": CrisisSituation(
        id="police_001",
        category=CrisisCategory.POLICE_RESCUE,
        title="ПТСР после операции",
        description="Видел смерть, насилие, не могу забыть",
        severity="high",
        recommended_approach=["PFA", "ACT", "DBT"],
        keywords=["птср полиция", "птср спасатель", "видел смерть", "не могу забыть операцию"],
    ),

    "police_002": CrisisSituation(
        id="police_002",
        category=CrisisCategory.POLICE_RESCUE,
        title="Убийство в ходе службы",
        description="Застрелил человека, моральная травма",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["застрелил человека", "убил при задержании", "применил оружие", "моральная травма полиция"],
    ),

    "police_003": CrisisSituation(
        id="police_003",
        category=CrisisCategory.POLICE_RESCUE,
        title="Потеря напарника",
        description="Напарник погиб, чувство вины",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["напарник погиб", "партнёр погиб", "не смог защитить напарника"],
    ),

    "police_004": CrisisSituation(
        id="police_004",
        category=CrisisCategory.POLICE_RESCUE,
        title="Коррупция",
        description="Давление от начальства, принуждение к взяткам",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["коррупция полиция", "заставляют брать взятки", "давление начальство полиция"],
    ),

    "police_005": CrisisSituation(
        id="police_005",
        category=CrisisCategory.POLICE_RESCUE,
        title="Моральная дилемма",
        description="Приказ противоречит закону/совести",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["приказ противоречит закону", "моральная дилемма полиция", "не могу выполнить приказ"],
    ),

    "police_006": CrisisSituation(
        id="police_006",
        category=CrisisCategory.POLICE_RESCUE,
        title="Травля от общества",
        description="Ненависть к полиции, угрозы",
        severity="high",
        recommended_approach=["DBT", "ACT"],
        keywords=["ненависть к полиции", "угрозы полиции", "травля полицейских", "все ненавидят полицию"],
    ),

    "police_007": CrisisSituation(
        id="police_007",
        category=CrisisCategory.POLICE_RESCUE,
        title="Невозможность спасти человека",
        description="Спасатель не смог спасти, чувство вины",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не смог спасти", "человек погиб спасатель", "не успел спасти", "чувство вины спасатель"],
    ),

    "police_008": CrisisSituation(
        id="police_008",
        category=CrisisCategory.POLICE_RESCUE,
        title="Работа на месте катастрофы",
        description="Видел множество трупов, ПТСР",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["катастрофа", "много трупов", "место катастрофы", "массовая гибель"],
    ),

    "police_009": CrisisSituation(
        id="police_009",
        category=CrisisCategory.POLICE_RESCUE,
        title="Суицид коллеги",
        description="Коллега покончил с собой",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["коллега покончил полиция", "суицид коллеги спасатель", "коллега покончил с собой"],
    ),

    "police_010": CrisisSituation(
        id="police_010",
        category=CrisisCategory.POLICE_RESCUE,
        title="Конфликт с начальством",
        description="Давление, требования нарушить закон",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["конфликт с начальством полиция", "требуют нарушить закон", "давление начальство"],
    ),

    "police_011": CrisisSituation(
        id="police_011",
        category=CrisisCategory.POLICE_RESCUE,
        title="Физическое насилие при задержании",
        description="Пострадал при задержании преступника",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["пострадал при задержании", "избили при задержании", "травма полиция"],
    ),

    "police_012": CrisisSituation(
        id="police_012",
        category=CrisisCategory.POLICE_RESCUE,
        title="Моральная травма от насилия",
        description="Применил силу, человек пострадал",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["применил силу", "избил задержанного", "моральная травма насилие"],
    ),

    "police_013": CrisisSituation(
        id="police_013",
        category=CrisisCategory.POLICE_RESCUE,
        title="Невозможность помочь жертве",
        description="Видел насилие, но не смог помочь",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["не смог помочь жертве", "видел насилие", "бессилие полиция"],
    ),

    "police_014": CrisisSituation(
        id="police_014",
        category=CrisisCategory.POLICE_RESCUE,
        title="Работа с детьми-жертвами",
        description="Работа с детьми, пострадавшими от насилия, травма",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["дети жертвы насилия", "работа с пострадавшими детьми", "травма от работы с детьми"],
    ),

    "police_015": CrisisSituation(
        id="police_015",
        category=CrisisCategory.POLICE_RESCUE,
        title="Выгорание спасателя",
        description="Не могу больше спасать, эмоциональное истощение",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["выгорание спасатель", "не могу больше спасать", "истощение спасатель"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 19: МИГРАНТЫ И БЕЖЕНЦЫ (20 ситуаций)
    # ========================================================================
    "migr_001": CrisisSituation(
        id="migr_001",
        category=CrisisCategory.MIGRANTS,
        title="Депортация",
        description="Депортируют, страх за будущее",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["депортация", "депортируют", "высылают из страны", "страх депортации"],
    ),

    "migr_002": CrisisSituation(
        id="migr_002",
        category=CrisisCategory.MIGRANTS,
        title="Разлука с семьёй",
        description="Семья осталась в другой стране",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["семья осталась", "разлука с семьёй мигрант", "не могу забрать семью"],
    ),

    "migr_003": CrisisSituation(
        id="migr_003",
        category=CrisisCategory.MIGRANTS,
        title="Языковой барьер",
        description="Не могу найти работу из-за языка",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["языковой барьер", "не знаю язык", "не могу найти работу язык"],
    ),

    "migr_004": CrisisSituation(
        id="migr_004",
        category=CrisisCategory.MIGRANTS,
        title="Дискриминация",
        description="Дискриминация по национальности",
        severity="high",
        recommended_approach=["DBT", "ACT"],
        keywords=["дискриминация мигрант", "ксенофобия", "расизм", "дискриминация по национальности"],
    ),

    "migr_005": CrisisSituation(
        id="migr_005",
        category=CrisisCategory.MIGRANTS,
        title="Потеря статуса",
        description="Потерял легальный статус, страх депортации",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["потерял статус", "нелегальный статус", "истёк вид на жительство"],
    ),

    "migr_006": CrisisSituation(
        id="migr_006",
        category=CrisisCategory.MIGRANTS,
        title="Невозможность вернуться домой",
        description="Война/преследования, не могу вернуться",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не могу вернуться домой", "война на родине", "преследования", "беженец"],
    ),

    "migr_007": CrisisSituation(
        id="migr_007",
        category=CrisisCategory.MIGRANTS,
        title="Культурная изоляция",
        description="Не понимаю культуру, чувствую себя чужим",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["культурная изоляция", "чувствую себя чужим", "не понимаю культуру"],
    ),

    "migr_008": CrisisSituation(
        id="migr_008",
        category=CrisisCategory.MIGRANTS,
        title="Потеря профессии",
        description="Был врачом/учителем, здесь работаю грузчиком",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["потеря профессии мигрант", "был врачом работаю грузчиком", "не признают диплом"],
    ),

    "migr_009": CrisisSituation(
        id="migr_009",
        category=CrisisCategory.MIGRANTS,
        title="Травля от местных",
        description="Ксенофобия, насилие",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["ксенофобия", "травля мигрантов", "насилие против мигрантов", "избили за национальность"],
    ),

    "migr_010": CrisisSituation(
        id="migr_010",
        category=CrisisCategory.MIGRANTS,
        title="Невозможность получить документы",
        description="Бюрократия, не могу легализоваться",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не могу получить документы", "бюрократия миграция", "не дают документы"],
    ),

    "migr_011": CrisisSituation(
        id="migr_011",
        category=CrisisCategory.MIGRANTS,
        title="Разлука с детьми",
        description="Дети остались в другой стране",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["дети остались", "разлука с детьми мигрант", "не могу забрать детей"],
    ),

    "migr_012": CrisisSituation(
        id="migr_012",
        category=CrisisCategory.MIGRANTS,
        title="Потеря дома",
        description="Дом разрушен войной, не могу вернуться",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["дом разрушен", "потерял дом война", "не могу вернуться домой"],
    ),

    "migr_013": CrisisSituation(
        id="migr_013",
        category=CrisisCategory.MIGRANTS,
        title="Эксплуатация на работе",
        description="Работодатель эксплуатирует, не платит",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["эксплуатация мигрантов", "не платят зарплату мигрант", "рабство"],
    ),

    "migr_014": CrisisSituation(
        id="migr_014",
        category=CrisisCategory.MIGRANTS,
        title="Страх перед полицией",
        description="Боюсь полиции, могут депортировать",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["боюсь полиции", "страх депортации", "боюсь проверки документов"],
    ),

    "migr_015": CrisisSituation(
        id="migr_015",
        category=CrisisCategory.MIGRANTS,
        title="Невозможность получить медицинскую помощь",
        description="Нет страховки, не могу лечиться",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["нет страховки", "не могу лечиться мигрант", "нет медицинской помощи"],
    ),

    "migr_016": CrisisSituation(
        id="migr_016",
        category=CrisisCategory.MIGRANTS,
        title="Конфликт поколений",
        description="Дети ассимилировались, я нет, конфликт",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт поколений мигранты", "дети ассимилировались", "культурный разрыв"],
    ),

    "migr_017": CrisisSituation(
        id="migr_017",
        category=CrisisCategory.MIGRANTS,
        title="Потеря идентичности",
        description="Не знаю кто я, не там и не здесь",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["потеря идентичности мигрант", "не там не здесь", "кто я"],
    ),

    "migr_018": CrisisSituation(
        id="migr_018",
        category=CrisisCategory.MIGRANTS,
        title="Травма от войны",
        description="Бежал от войны, ПТСР",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["бежал от войны", "птср беженец", "травма войны беженец"],
    ),

    "migr_019": CrisisSituation(
        id="migr_019",
        category=CrisisCategory.MIGRANTS,
        title="Невозможность найти жильё",
        description="Дискриминация, не сдают жильё",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не сдают жильё мигрант", "дискриминация жильё", "не могу снять квартиру"],
    ),

    "migr_020": CrisisSituation(
        id="migr_020",
        category=CrisisCategory.MIGRANTS,
        title="Разлука с родителями",
        description="Родители остались, не могу их забрать",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["родители остались", "не могу забрать родителей", "разлука с родителями мигрант"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 20: МОБИЛИЗАЦИЯ (20 ситуаций)
    # ========================================================================
    "mob_001": CrisisSituation(
        id="mob_001",
        category=CrisisCategory.MOBILIZATION,
        title="Повестка на мобилизацию",
        description="Получил повестку, страх, паника",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["повестка", "мобилизация", "получил повестку", "призыв", "военкомат"],
    ),

    "mob_002": CrisisSituation(
        id="mob_002",
        category=CrisisCategory.MOBILIZATION,
        title="Мобилизация мужа",
        description="Муж мобилизован, страх за его жизнь",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["муж мобилизован", "мужа забрали", "муж на войне", "страх за мужа"],
    ),

    "mob_003": CrisisSituation(
        id="mob_003",
        category=CrisisCategory.MOBILIZATION,
        title="Мобилизация отца",
        description="Отца мобилизовали, семья без кормильца",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["отца мобилизовали", "папу забрали", "отец на войне", "семья без кормильца"],
    ),

    "mob_004": CrisisSituation(
        id="mob_004",
        category=CrisisCategory.MOBILIZATION,
        title="Мобилизация сына",
        description="Сына мобилизовали, страх потерять",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["сына мобилизовали", "сын на войне", "забрали сына", "страх за сына"],
    ),

    "mob_005": CrisisSituation(
        id="mob_005",
        category=CrisisCategory.MOBILIZATION,
        title="Попытка избежать мобилизации",
        description="Прячусь, страх быть пойманным",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["прячусь от мобилизации", "избежать призыва", "скрываюсь от военкомата", "боюсь повестки"],
    ),

    "mob_006": CrisisSituation(
        id="mob_006",
        category=CrisisCategory.MOBILIZATION,
        title="Конфликт из-за мобилизации",
        description="Жена требует уехать, я не хочу",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт из-за мобилизации", "жена требует уехать", "семья против мобилизации"],
    ),

    "mob_007": CrisisSituation(
        id="mob_007",
        category=CrisisCategory.MOBILIZATION,
        title="Потеря работы из-за мобилизации",
        description="Мобилизовали, потерял работу",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["потерял работу мобилизация", "уволили из-за мобилизации", "работа мобилизация"],
    ),

    "mob_008": CrisisSituation(
        id="mob_008",
        category=CrisisCategory.MOBILIZATION,
        title="Невозможность содержать семью",
        description="Мобилизован, семья без денег",
        severity="critical",
        recommended_approach=["PFA", "SFBT"],
        keywords=["семья без денег мобилизация", "не могу содержать семью", "нет денег мобилизация"],
    ),

    "mob_009": CrisisSituation(
        id="mob_009",
        category=CrisisCategory.MOBILIZATION,
        title="Страх перед отправкой на фронт",
        description="Мобилизован, жду отправки, паника",
        severity="critical",
        recommended_approach=["PFA", "DBT"],
        keywords=["страх перед фронтом", "жду отправки", "паника мобилизация", "боюсь на фронт"],
    ),

    "mob_010": CrisisSituation(
        id="mob_010",
        category=CrisisCategory.MOBILIZATION,
        title="Конфликт с военкоматом",
        description="Давление, угрозы",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["конфликт с военкоматом", "давление военкомат", "угрозы военкомат"],
    ),

    "mob_011": CrisisSituation(
        id="mob_011",
        category=CrisisCategory.MOBILIZATION,
        title="Мобилизация по ошибке",
        description="Мобилизовали хотя не должны были (возраст, здоровье)",
        severity="high",
        recommended_approach=["PFA", "SFBT"],
        keywords=["мобилизация по ошибке", "не должны были мобилизовать", "ошибка военкомат"],
    ),

    "mob_012": CrisisSituation(
        id="mob_012",
        category=CrisisCategory.MOBILIZATION,
        title="Невозможность вернуться с мобилизации",
        description="Не отпускают, бессрочная служба",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не отпускают", "бессрочная служба", "не могу вернуться с мобилизации"],
    ),

    "mob_013": CrisisSituation(
        id="mob_013",
        category=CrisisCategory.MOBILIZATION,
        title="Ранение на мобилизации",
        description="Ранен, инвалидность",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["ранение мобилизация", "инвалидность мобилизация", "ранен на войне"],
    ),

    "mob_014": CrisisSituation(
        id="mob_014",
        category=CrisisCategory.MOBILIZATION,
        title="Смерть мобилизованного",
        description="Муж/отец/сын погиб на войне",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["муж погиб мобилизация", "отец погиб война", "сын погиб", "погиб на войне"],
    ),

    "mob_015": CrisisSituation(
        id="mob_015",
        category=CrisisCategory.MOBILIZATION,
        title="Неизвестность",
        description="Мобилизован, нет связи, не знаю жив ли",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["нет связи мобилизация", "не знаю жив ли", "пропал без вести"],
    ),

    "mob_016": CrisisSituation(
        id="mob_016",
        category=CrisisCategory.MOBILIZATION,
        title="Конфликт с семьёй из-за мобилизации",
        description="Семья против войны, я за",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт с семьёй мобилизация", "семья против войны", "разные взгляды война"],
    ),

    "mob_017": CrisisSituation(
        id="mob_017",
        category=CrisisCategory.MOBILIZATION,
        title="Потеря бизнеса из-за мобилизации",
        description="Мобилизован, бизнес рухнул",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["потерял бизнес мобилизация", "бизнес рухнул", "разорился мобилизация"],
    ),

    "mob_018": CrisisSituation(
        id="mob_018",
        category=CrisisCategory.MOBILIZATION,
        title="Невозможность вернуться к мирной жизни",
        description="Вернулся с мобилизации, не могу адаптироваться",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["вернулся с мобилизации", "не могу адаптироваться", "после мобилизации"],
    ),

    "mob_019": CrisisSituation(
        id="mob_019",
        category=CrisisCategory.MOBILIZATION,
        title="Алкоголизм после мобилизации",
        description="Пью чтобы забыть",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["пью после мобилизации", "алкоголизм мобилизация", "пью чтобы забыть"],
    ),

    "mob_020": CrisisSituation(
        id="mob_020",
        category=CrisisCategory.MOBILIZATION,
        title="Развод после мобилизации",
        description="Вернулся, жена не узнаёт меня",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["развод после мобилизации", "жена не узнаёт", "семья распалась мобилизация"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 21: КОНТРАКТНАЯ СЛУЖБА (15 ситуаций)
    # ========================================================================
    "contr_001": CrisisSituation(
        id="contr_001",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Подписал контракт из-за денег",
        description="Нужны деньги, подписал, теперь жалею",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["подписал контракт", "контракт из-за денег", "жалею контракт", "нужны деньги контракт"],
    ),

    "contr_002": CrisisSituation(
        id="contr_002",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Обман при подписании контракта",
        description="Обещали одно, реальность другая",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["обман контракт", "обещали одно", "обманули контракт", "реальность другая"],
    ),

    "contr_003": CrisisSituation(
        id="contr_003",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Невозможность расторгнуть контракт",
        description="Хочу уйти, не отпускают",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не могу расторгнуть контракт", "не отпускают", "хочу уйти контракт"],
    ),

    "contr_004": CrisisSituation(
        id="contr_004",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Ранение на контракте",
        description="Ранен, инвалидность, не получаю обещанные выплаты",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["ранение контракт", "инвалидность контракт", "не платят выплаты", "обещали деньги"],
    ),

    "contr_005": CrisisSituation(
        id="contr_005",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Смерть контрактника",
        description="Муж/брат погиб, не выплачивают компенсацию",
        severity="critical",
        recommended_approach=["PFA", "ACT", "grief_module"],
        keywords=["контрактник погиб", "не выплачивают компенсацию", "муж погиб контракт", "брат погиб"],
    ),

    "contr_006": CrisisSituation(
        id="contr_006",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="ПТСР после контракта",
        description="Вернулся, кошмары, не могу работать",
        severity="critical",
        recommended_approach=["PFA", "ACT", "DBT"],
        keywords=["птср контракт", "кошмары после контракта", "не могу работать контракт"],
    ),

    "contr_007": CrisisSituation(
        id="contr_007",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Конфликт с командованием",
        description="Давление, угрозы",
        severity="high",
        recommended_approach=["PFA", "ACT"],
        keywords=["конфликт с командованием контракт", "давление командование", "угрозы командир"],
    ),

    "contr_008": CrisisSituation(
        id="contr_008",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Дедовщина на контракте",
        description="Травля, насилие",
        severity="high",
        recommended_approach=["PFA", "DBT"],
        keywords=["дедовщина контракт", "травля контракт", "насилие контракт"],
    ),

    "contr_009": CrisisSituation(
        id="contr_009",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Невозможность получить выплаты",
        description="Обещали деньги, не платят",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не платят контракт", "обещали деньги", "не получаю выплаты контракт"],
    ),

    "contr_010": CrisisSituation(
        id="contr_010",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Конфликт с семьёй из-за контракта",
        description="Семья против, я подписал",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт с семьёй контракт", "семья против контракта", "подписал контракт"],
    ),

    "contr_011": CrisisSituation(
        id="contr_011",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Потеря здоровья на контракте",
        description="Контузия, инвалидность",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["потеря здоровья контракт", "контузия контракт", "инвалидность контракт"],
    ),

    "contr_012": CrisisSituation(
        id="contr_012",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Моральная травма от войны",
        description="Убивал, не могу жить с этим",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["моральная травма контракт", "убивал", "не могу жить с этим контракт"],
    ),

    "contr_013": CrisisSituation(
        id="contr_013",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Невозможность найти работу после контракта",
        description="Вернулся, никто не берёт на работу",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не могу найти работу контракт", "вернулся с контракта", "никто не берёт"],
    ),

    "contr_014": CrisisSituation(
        id="contr_014",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Алкоголизм после контракта",
        description="Пью чтобы забыть",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["алкоголизм контракт", "пью после контракта", "пью чтобы забыть"],
    ),

    "contr_015": CrisisSituation(
        id="contr_015",
        category=CrisisCategory.CONTRACT_SERVICE,
        title="Суицидальные мысли после контракта",
        description="Не вижу смысла жить",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["суицид контракт", "не вижу смысла жить контракт", "хочу умереть контракт"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 22: ЭМИГРАЦИЯ ИЗ-ЗА ВОЙНЫ (15 ситуаций)
    # ========================================================================
    "emig_001": CrisisSituation(
        id="emig_001",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Эмиграция из-за несогласия с войной",
        description="Уехал, чувство вины, потеря родины",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["эмиграция из-за войны", "уехал из-за войны", "чувство вины эмиграция", "потеря родины"],
    ),

    "emig_002": CrisisSituation(
        id="emig_002",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Разлука с семьёй из-за эмиграции",
        description="Семья осталась, не могу забрать",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["семья осталась эмиграция", "не могу забрать семью", "разлука эмиграция"],
    ),

    "emig_003": CrisisSituation(
        id="emig_003",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Потеря работы из-за эмиграции",
        description="Уехал, не могу найти работу",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["потеря работы эмиграция", "не могу найти работу эмигрант", "уехал не могу работать"],
    ),

    "emig_004": CrisisSituation(
        id="emig_004",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Дискриминация за границей",
        description="Дискриминация за то что русский",
        severity="high",
        recommended_approach=["DBT", "ACT"],
        keywords=["дискриминация русских", "русофобия", "дискриминация за границей", "ненависть к русским"],
    ),

    "emig_005": CrisisSituation(
        id="emig_005",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Невозможность вернуться",
        description="Уехал, боюсь вернуться (преследования)",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не могу вернуться", "боюсь вернуться", "преследования", "страх возвращения"],
    ),

    "emig_006": CrisisSituation(
        id="emig_006",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Конфликт с семьёй из-за эмиграции",
        description="Семья против, я уехал",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт с семьёй эмиграция", "семья против эмиграции", "родители не понимают"],
    ),

    "emig_007": CrisisSituation(
        id="emig_007",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Потеря идентичности",
        description="Не знаю кто я, не там и не здесь",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["потеря идентичности эмигрант", "не там не здесь", "кто я эмиграция"],
    ),

    "emig_008": CrisisSituation(
        id="emig_008",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Чувство вины за эмиграцию",
        description="Уехал, а другие остались",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["чувство вины эмиграция", "уехал а другие остались", "предал родину"],
    ),

    "emig_009": CrisisSituation(
        id="emig_009",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Невозможность получить статус беженца",
        description="Не дают статус, страх депортации",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["не дают статус беженца", "отказ в убежище", "страх депортации беженец"],
    ),

    "emig_010": CrisisSituation(
        id="emig_010",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Разлука с детьми",
        description="Дети остались с бывшим партнёром",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["дети остались эмиграция", "разлука с детьми", "не могу видеть детей"],
    ),

    "emig_011": CrisisSituation(
        id="emig_011",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Потеря бизнеса из-за эмиграции",
        description="Бизнес остался, рухнул",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["потеря бизнеса эмиграция", "бизнес рухнул эмиграция", "разорился эмиграция"],
    ),

    "emig_012": CrisisSituation(
        id="emig_012",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Невозможность найти жильё",
        description="Дискриминация, не сдают",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не сдают жильё эмигрант", "дискриминация жильё эмиграция", "не могу снять квартиру"],
    ),

    "emig_013": CrisisSituation(
        id="emig_013",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Языковой барьер",
        description="Не могу найти работу из-за языка",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["языковой барьер эмиграция", "не знаю язык", "не могу найти работу язык"],
    ),

    "emig_014": CrisisSituation(
        id="emig_014",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Конфликт поколений",
        description="Родители не понимают почему уехал",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт поколений эмиграция", "родители не понимают", "разные взгляды эмиграция"],
    ),

    "emig_015": CrisisSituation(
        id="emig_015",
        category=CrisisCategory.WAR_EMIGRATION,
        title="Депрессия из-за эмиграции",
        description="Потерял всё, депрессия",
        severity="critical",
        recommended_approach=["PFA", "ACT", "DBT"],
        keywords=["депрессия эмиграция", "потерял всё", "не вижу смысла эмиграция"],
    ),

    # ========================================================================
    # КАТЕГОРИЯ 23: ПОЛИТИЧЕСКИЕ РЕПРЕССИИ (10 ситуаций)
    # ========================================================================
    "polit_001": CrisisSituation(
        id="polit_001",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Уголовное дело за антивоенную позицию",
        description="Возбудили дело, страх тюрьмы",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["уголовное дело антивоенное", "дело за позицию", "страх тюрьмы", "преследование за взгляды"],
    ),

    "polit_002": CrisisSituation(
        id="polit_002",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Увольнение за политические взгляды",
        description="Уволили за антивоенный пост",
        severity="high",
        recommended_approach=["ACT", "SFBT"],
        keywords=["уволили за взгляды", "увольнение за пост", "уволили за политику"],
    ),

    "polit_003": CrisisSituation(
        id="polit_003",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Травля за политические взгляды",
        description="Травят на работе/в семье",
        severity="high",
        recommended_approach=["DBT", "ACT"],
        keywords=["травля за взгляды", "травят за политику", "изоляция за позицию"],
    ),

    "polit_004": CrisisSituation(
        id="polit_004",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Штраф за антивоенный пост",
        description="Оштрафовали, не могу платить",
        severity="medium",
        recommended_approach=["SFBT", "ACT"],
        keywords=["штраф за пост", "оштрафовали", "штраф антивоенное"],
    ),

    "polit_005": CrisisSituation(
        id="polit_005",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Конфликт с семьёй из-за политики",
        description="Семья за войну, я против",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["конфликт с семьёй политика", "семья за войну", "разные взгляды война"],
    ),

    "polit_006": CrisisSituation(
        id="polit_006",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Потеря друзей из-за политики",
        description="Друзья отвернулись",
        severity="medium",
        recommended_approach=["ACT", "DBT"],
        keywords=["потеря друзей политика", "друзья отвернулись", "изоляция политика"],
    ),

    "polit_007": CrisisSituation(
        id="polit_007",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Страх высказываться",
        description="Боюсь говорить, самоцензура",
        severity="high",
        recommended_approach=["ACT", "DBT"],
        keywords=["страх высказываться", "самоцензура", "боюсь говорить", "страх репрессий"],
    ),

    "polit_008": CrisisSituation(
        id="polit_008",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Конфликт с властями",
        description="Давление, угрозы",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["конфликт с властями", "давление власти", "угрозы власти"],
    ),

    "polit_009": CrisisSituation(
        id="polit_009",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Невозможность найти работу",
        description="Не берут из-за политических взглядов",
        severity="high",
        recommended_approach=["SFBT", "ACT"],
        keywords=["не берут на работу политика", "дискриминация политика", "чёрный список"],
    ),

    "polit_010": CrisisSituation(
        id="polit_010",
        category=CrisisCategory.POLITICAL_REPRESSION,
        title="Депортация за политическую активность",
        description="Депортировали из страны",
        severity="critical",
        recommended_approach=["PFA", "ACT"],
        keywords=["депортация политика", "выслали из страны", "депортировали за активность"],
    ),
}


# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ
# ============================================================================

def get_situation_by_id(situation_id: str) -> CrisisSituation:
    """Получить ситуацию по ID."""
    return CRISIS_SITUATIONS.get(situation_id)


def find_situations_by_keywords(text: str) -> List[CrisisSituation]:
    """Найти ситуации по ключевым словам в тексте пользователя."""
    text_lower = text.lower()
    matches = []

    for situation in CRISIS_SITUATIONS.values():
        # Проверить, есть ли ключевые слова в тексте
        if any(keyword in text_lower for keyword in situation.keywords):
            matches.append(situation)

    # Сортировать по тяжести (critical → high → medium → low)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    matches.sort(key=lambda s: severity_order.get(s.severity, 4))

    return matches


def get_situations_by_category(category: CrisisCategory) -> List[CrisisSituation]:
    """Получить все ситуации в категории."""
    return [
        situation for situation in CRISIS_SITUATIONS.values()
        if situation.category == category
    ]


def get_statistics() -> Dict[str, int]:
    """Получить статистику по базе кризисных ситуаций."""
    stats = {
        "total": len(CRISIS_SITUATIONS),
        "by_category": {},
        "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    }

    for situation in CRISIS_SITUATIONS.values():
        # По категориям
        cat = situation.category.value
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

        # По тяжести
        stats["by_severity"][situation.severity] += 1

    return stats


if __name__ == "__main__":
    # Вывести статистику
    stats = get_statistics()
    print(f"Всего ситуаций: {stats['total']}")
    print(f"\nПо категориям:")
    for cat, count in stats['by_category'].items():
        print(f"  {cat}: {count}")
    print(f"\nПо тяжести:")
    for sev, count in stats['by_severity'].items():
        print(f"  {sev}: {count}")

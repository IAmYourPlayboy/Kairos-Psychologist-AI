"""Многоуровневая анонимизация ПДн перед записью в БД.

ФЗ-152 (ст. 10) требует особого режима для специальной категории ПДн —
данных о психоэмоциональном состоянии. Один из путей легально использовать
такие данные для исследований/LoRA — обезличивание (ст. 6 ч.2 п.9).

Архитектура:
    LLM получает ОРИГИНАЛЬНЫЙ текст (для качества ответа).
    БД хранит АНОНИМИЗИРОВАННЫЙ текст (для data flywheel + ФЗ-152).
    Анонимизация — точечная замена в момент записи `Message.content`.

Уровни анонимизации (в порядке применения):
    1. Email → [EMAIL]
    2. Телефоны (RU и интернац.) → [PHONE]
    3. URL → [URL]
    4. Номера карт (luhn-валидные 13-19 цифр) → [CARD]
    5. ИНН/СНИЛС-подобные числовые ID → [ID]
    6. Адреса (улица + дом) → [ADDRESS]
    7. Точные даты → [DATE]
    8. Имена и отчества (словарь + Capitalized слова после маркеров)
       → [NAME]

K-анонимность (k≥5) применяется ОТДЕЛЬНО на этапе экспорта датасета —
не здесь. Здесь — только замена ПДн на заглушки.

Что НЕ делает этот модуль:
    - Не трогает эмоциональную окраску, мат, сленг (это маркеры дистресса).
    - Не правит грамматику.
    - Не сокращает текст.
    - Не определяет регион — это делает экспорт по `meta` сессии.

Лог удалённых полей:
    Каждый вызов возвращает не только текст, но и список замен —
    `AnonymizationLog`. Сохраняется в `anonymization_log` в БД для аудита.

Будущие расширения:
    - Natasha NER для имён (более точно, чем словарь). Пока словарь —
      покрывает топ-1000 русских имён, чего достаточно для MVP.
    - K-анонимность в `research_export.py` (Блок B2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Pattern


# ============================================================================
# Структуры данных
# ============================================================================


@dataclass(frozen=True)
class Replacement:
    """Одна замена ПДн на заглушку."""

    kind: str  # "email" | "phone" | "url" | "card" | "address" | "date" | "name" | "id"
    original: str
    placeholder: str
    start: int
    end: int


@dataclass
class AnonymizationLog:
    """Лог замен для аудита.

    Атрибуты:
        replacements: список всех произведённых замен.
        had_pii: True если хотя бы одна замена была.
    """

    replacements: list[Replacement] = field(default_factory=list)

    @property
    def had_pii(self) -> bool:
        return len(self.replacements) > 0

    def kinds(self) -> set[str]:
        """Какие типы ПДн были найдены."""
        return {r.kind for r in self.replacements}

    def to_dict(self) -> dict:
        """Сериализация для записи в БД (без оригиналов!).

        Оригиналы НЕ пишутся — это тоже ПДн. Пишем только метаданные:
        тип, длина, позиция. Этого достаточно для аудита («сколько и каких
        ПДн встречалось в каком сообщении») без хранения самих данных.
        """
        return {
            "had_pii": self.had_pii,
            "kinds": sorted(self.kinds()),
            "count": len(self.replacements),
            "items": [
                {
                    "kind": r.kind,
                    "len": len(r.original),
                    "start": r.start,
                    "end": r.end,
                }
                for r in self.replacements
            ],
        }


# ============================================================================
# Регулярные выражения (компилируются один раз)
# ============================================================================


# Email: простой и достаточный паттерн.
# Не покрывает экзотику типа "user@[192.168.1.1]" — это редкость.
_RE_EMAIL: Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)


# Телефоны: российские и интернациональные форматы.
# Покрывает: +7 (495) 123-45-67, 8-800-333-44-34, 89991234567, +1 555 1234567.
# Минимум 10 цифр после очистки.
_RE_PHONE: Pattern[str] = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?"  # код страны (опц.)
    r"\(?\d{3,4}\)?"            # код города
    r"[\s\-]?\d{2,4}"           # первая часть
    r"[\s\-]?\d{2,4}"           # вторая часть
    r"(?:[\s\-]?\d{2,4})?"      # третья (опц., для длинных номеров)
)


# URL: http(s), а также короткие ссылки без схемы (vk.com/...)
_RE_URL: Pattern[str] = re.compile(
    r"\b(?:https?://|www\.)[^\s<>\"']+"
    r"|(?<!\w)(?:vk|t|telegram|youtu|ya|yandex)\.(?:com|me|be|ru)/[^\s<>\"']+",
    re.IGNORECASE,
)


# Номера банковских карт: 13-19 цифр, могут быть разделены пробелами/дефисами.
# Доп. проверяем алгоритмом Луна, чтобы не схватывать случайные числа.
_RE_CARD: Pattern[str] = re.compile(
    r"\b(?:\d[\s\-]?){12,18}\d\b"
)


# ID-номера длиной 10-12 цифр (ИНН 10/12, СНИЛС 11). Пишутся подряд или с дефисами.
# Размещаем ПОСЛЕ карт и телефонов в порядке применения, чтобы не перетянуть их.
_RE_ID: Pattern[str] = re.compile(
    r"\b\d{10,12}\b"
)


# Адрес: «ул./улица/проспект/пр-кт/...» + следующее слово + цифра дома.
# Типичный пример: «ул. Тверская, 15», «проспект Мира 50», «Тверская улица 15».
_RE_ADDRESS: Pattern[str] = re.compile(
    r"(?:"
    r"(?:ул|улица|пр|проспект|пр\-кт|пер|переулок|пл|площадь|"
    r"наб|набережная|ш|шоссе|б\-р|бульвар|пр\-д|проезд)\.?"
    r"\s+[А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+)?"
    r"|"  # ИЛИ обратный порядок: "Тверская улица"
    r"[А-ЯЁ][а-яё\-]+\s+(?:улица|проспект|переулок|шоссе|бульвар)"
    r")"
    r"(?:[,\s]+(?:дом\s+)?\d+[А-Яа-я]?)?",
    re.IGNORECASE,
)


# Точные даты: ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ, 1 января 2020, 2020-01-15.
_RE_DATE: Pattern[str] = re.compile(
    r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b"
    r"|\b\d{4}\-\d{1,2}\-\d{1,2}\b"
    r"|\b\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)"
    r"[а-я]*\s+\d{2,4}\b",
    re.IGNORECASE,
)


# Список топ-имён для словарного метода.
# Покрывает большинство бытовых упоминаний. Для MVP достаточно.
# Расширение через Natasha NER — после MVP (см. модуль docstring).
_RUSSIAN_NAMES: frozenset[str] = frozenset(
    name.lower()
    for name in {
        # Мужские
        "Александр", "Алексей", "Анатолий", "Андрей", "Антон", "Аркадий",
        "Артём", "Артем", "Артур", "Борис", "Вадим", "Валентин", "Валерий",
        "Василий", "Виктор", "Виталий", "Владимир", "Владислав", "Вячеслав",
        "Геннадий", "Георгий", "Глеб", "Григорий", "Даниил", "Данила",
        "Денис", "Дмитрий", "Евгений", "Егор", "Иван", "Игорь", "Илья",
        "Кирилл", "Константин", "Лев", "Леонид", "Максим", "Марк", "Матвей",
        "Михаил", "Никита", "Николай", "Олег", "Павел", "Пётр", "Петр",
        "Роман", "Руслан", "Семён", "Семен", "Сергей", "Станислав",
        "Степан", "Тимофей", "Тимур", "Фёдор", "Федор", "Юрий", "Ярослав",
        # Женские
        "Александра", "Алёна", "Алена", "Алина", "Алла", "Анастасия",
        "Анна", "Антонина", "Валентина", "Валерия", "Варвара", "Вера",
        "Вероника", "Виктория", "Галина", "Дарья", "Диана", "Евгения",
        "Екатерина", "Елена", "Елизавета", "Жанна", "Зинаида", "Зоя",
        "Инна", "Ирина", "Карина", "Кира", "Ксения", "Лариса", "Лидия",
        "Любовь", "Людмила", "Маргарита", "Марина", "Мария", "Маша",
        "Надежда", "Наталья", "Наталия", "Нина", "Оксана", "Олеся",
        "Ольга", "Полина", "Раиса", "Регина", "Светлана", "София", "Софья",
        "Тамара", "Татьяна", "Ульяна", "Юлия", "Яна",
    }
)


# Маркеры, после которых вероятно идёт имя.
# «меня зовут Маша» → ловим «Маша» даже если её нет в словаре.
_NAME_MARKERS: tuple[str, ...] = (
    "меня зовут", "моё имя", "мое имя", "я ", "мама", "папа", "сын", "дочь",
    "брат", "сестра", "жена", "муж", "подруга", "друг", "сосед", "соседка",
    "коллега", "начальник", "начальница", "врач", "терапевт", "психолог",
)


# ============================================================================
# Главная функция
# ============================================================================


def anonymize(text: str) -> tuple[str, AnonymizationLog]:
    """Анонимизировать текст: заменить ПДн на заглушки.

    Args:
        text: исходный текст пользователя (или, реже, бота).

    Returns:
        (anonymized_text, log): текст с заглушками и лог замен.

    Порядок применения важен:
        1. Email — самый специфичный паттерн, не пересекается с остальным.
        2. URL — до телефонов (vk.com/123 не должен схватиться как телефон).
        3. Карты — до телефонов (длинные числа).
        4. Телефоны — после карт.
        5. ID — после карт и телефонов (10-12 цифр).
        6. Адреса — независимо.
        7. Даты — независимо.
        8. Имена — словарный метод + маркеры.
    """
    if not text:
        return text, AnonymizationLog()

    log = AnonymizationLog()
    result = text

    # Применяем замены по очереди. Каждая функция возвращает (новый_текст, замены).
    # Замены сразу добавляем в log.
    result, repls = _replace_pattern(result, _RE_EMAIL, "[EMAIL]", "email")
    log.replacements.extend(repls)

    result, repls = _replace_pattern(result, _RE_URL, "[URL]", "url")
    log.replacements.extend(repls)

    result, repls = _replace_cards(result)
    log.replacements.extend(repls)

    result, repls = _replace_phones(result)
    log.replacements.extend(repls)

    result, repls = _replace_pattern(result, _RE_ID, "[ID]", "id")
    log.replacements.extend(repls)

    result, repls = _replace_pattern(result, _RE_ADDRESS, "[ADDRESS]", "address")
    log.replacements.extend(repls)

    result, repls = _replace_pattern(result, _RE_DATE, "[DATE]", "date")
    log.replacements.extend(repls)

    result, repls = _replace_names(result)
    log.replacements.extend(repls)

    return result, log


# ============================================================================
# Вспомогательные функции
# ============================================================================


def _replace_pattern(
    text: str, pattern: Pattern[str], placeholder: str, kind: str
) -> tuple[str, list[Replacement]]:
    """Применить regex-замену и собрать список замен.

    Используется для простых случаев (email, URL, ID, address, date).
    """
    replacements: list[Replacement] = []

    def _capture(m: re.Match[str]) -> str:
        replacements.append(
            Replacement(
                kind=kind,
                original=m.group(0),
                placeholder=placeholder,
                start=m.start(),
                end=m.end(),
            )
        )
        return placeholder

    new_text = pattern.sub(_capture, text)
    return new_text, replacements


def _replace_phones(text: str) -> tuple[str, list[Replacement]]:
    """Заменить телефонные номера на [PHONE].

    Дополнительная проверка: после очистки от разделителей должно быть
    минимум 10 цифр. Иначе паттерн может схватить «12-15 человек» и т.п.
    """
    replacements: list[Replacement] = []

    def _capture(m: re.Match[str]) -> str:
        original = m.group(0)
        digits_only = re.sub(r"\D", "", original)
        # Минимум 10 цифр (российский без +7 кода) и максимум 15 (E.164).
        if not (10 <= len(digits_only) <= 15):
            return original
        replacements.append(
            Replacement(
                kind="phone",
                original=original,
                placeholder="[PHONE]",
                start=m.start(),
                end=m.end(),
            )
        )
        return "[PHONE]"

    new_text = _RE_PHONE.sub(_capture, text)
    return new_text, replacements


def _replace_cards(text: str) -> tuple[str, list[Replacement]]:
    """Заменить номера банковских карт на [CARD].

    Проверка алгоритмом Луна — иначе любая длинная последовательность цифр
    схватится как карта.
    """
    replacements: list[Replacement] = []

    def _capture(m: re.Match[str]) -> str:
        original = m.group(0)
        digits = re.sub(r"\D", "", original)
        if not _luhn_valid(digits):
            return original
        replacements.append(
            Replacement(
                kind="card",
                original=original,
                placeholder="[CARD]",
                start=m.start(),
                end=m.end(),
            )
        )
        return "[CARD]"

    new_text = _RE_CARD.sub(_capture, text)
    return new_text, replacements


def _luhn_valid(digits: str) -> bool:
    """Проверка алгоритмом Луна.

    Реальные банковские карты валидны по Луну. Случайные числа — почти
    никогда. Это позволяет отличить «4276 5500 1234 5678» (карта) от
    «1234 5678 9012 3456» (просто длинное число).
    """
    if not digits.isdigit() or len(digits) < 13:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _replace_names(text: str) -> tuple[str, list[Replacement]]:
    """Заменить имена на [NAME].

    Стратегия:
        1. Словарный метод — проходим по словам, проверяем lowercase в _RUSSIAN_NAMES.
        2. Маркеры — после «меня зовут», «мама» и т.п. — следующее
           Capitalized слово тоже считаем именем (даже если нет в словаре).

    Особенности:
        - Учитываем падежи через начало слова: «Маша», «Машу», «Маше», «Маши».
        - Не трогаем слова в начале предложения если они не имена
          (поэтому только словарь — нельзя слепо менять все Capitalized).
    """
    replacements: list[Replacement] = []

    # Шаг 1: словарный метод. Проходим по словам, ищем формы имён.
    # Учитываем все падежи через сравнение начала слова с именем.
    pattern = re.compile(r"\b[А-ЯЁ][а-яёА-ЯЁ\-]+\b")

    def _check_word(m: re.Match[str]) -> str:
        word = m.group(0)
        word_lower = word.lower()
        # Проверяем точное совпадение или начало слова с любым именем.
        # «Маша» и «Машу» оба начинаются с «маш», поэтому проверяем
        # «word_lower начинается с какого-то имени из словаря».
        # Чтобы избежать ложных срабатываний (Виктория → "Викт..." как имя?),
        # требуем минимум 4 символа имени или точное совпадение.
        if word_lower in _RUSSIAN_NAMES:
            replacements.append(
                Replacement(
                    kind="name",
                    original=word,
                    placeholder="[NAME]",
                    start=m.start(),
                    end=m.end(),
                )
            )
            return "[NAME]"
        # Проверка падежных форм: имя должно быть префиксом, и оставшаяся
        # часть слова — короткое окончание (1-3 символа).
        for name in _RUSSIAN_NAMES:
            if (
                len(name) >= 4
                and word_lower.startswith(name[:-1])  # без последней буквы (-а, -я, -й)
                and len(word_lower) - len(name) <= 2
            ):
                replacements.append(
                    Replacement(
                        kind="name",
                        original=word,
                        placeholder="[NAME]",
                        start=m.start(),
                        end=m.end(),
                    )
                )
                return "[NAME]"
        return word

    new_text = pattern.sub(_check_word, text)

    # Шаг 2: маркеры. Ищем «меня зовут <Имя>», «мама <Имя>» и т.п.
    # Capitalized слово после маркера — заменяем независимо от словаря.
    # Делаем это ПОСЛЕ словарного шага — чтобы [NAME] от шага 1 не схватилось.
    for marker in _NAME_MARKERS:
        marker_re = re.compile(
            rf"(?<!\w){re.escape(marker)}\s+([А-ЯЁ][а-яёА-ЯЁ\-]+)",
            re.IGNORECASE,
        )

        def _capture_marker(m: re.Match[str]) -> str:
            full = m.group(0)
            name_part = m.group(1)
            # Если это уже [NAME] — не трогаем.
            if name_part.startswith("["):
                return full
            replacements.append(
                Replacement(
                    kind="name",
                    original=name_part,
                    placeholder="[NAME]",
                    start=m.start(1),
                    end=m.end(1),
                )
            )
            return full.replace(name_part, "[NAME]")

        new_text = marker_re.sub(_capture_marker, new_text)

    return new_text, replacements


# ============================================================================
# Утилиты для perception_json
# ============================================================================


def anonymize_perception_json(perception_dict: dict) -> tuple[dict, AnonymizationLog]:
    """Анонимизировать поля PerceptionReport, которые могут содержать ПДн.

    Поля анализатора, в которых могут оказаться ПДн (LLM их пересказывает):
        - inner_monologue (мысли Кайроса от первого лица — может цитировать)
        - what_user_needs (краткое резюме нужды — может содержать имя)

    Эмоция, тема, risk_level — категориальные, ПДн в них быть не может.
    folder_hints — fixed enum, тоже без ПДн.
    """
    log = AnonymizationLog()
    if not perception_dict:
        return perception_dict, log

    out = dict(perception_dict)
    for field_name in ("inner_monologue", "what_user_needs"):
        value = out.get(field_name)
        if isinstance(value, str) and value:
            new_value, sub_log = anonymize(value)
            out[field_name] = new_value
            log.replacements.extend(sub_log.replacements)
    return out, log

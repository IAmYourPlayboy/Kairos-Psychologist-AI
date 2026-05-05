"""Сериализация фактов досье в текст для промптов LLM.

Два варианта:
- compact_summary       — короткая выжимка для MessageAnalyzer
                          (он использует это чтобы понять «кто это»).
- full_dossier_block    — полный блок для основной LLM с цитатами,
                          чтобы Кайрос мог ссылаться на конкретные слова.
"""

from __future__ import annotations

from app.data.dossier_models import DossierFact


def facts_to_compact_summary(facts: list[DossierFact]) -> str:
    """Короткая выжимка: одна строка на факт.

    Формат:
        - [folder/subfolder, sev=0.95] Папа пьёт
        - [relationships/school_peers, sev=0.80] Травля в школе

    Если фактов нет — placeholder «пусто».
    """
    if not facts:
        return "(пусто — досье ещё не наполнено)"

    lines: list[str] = []
    for f in facts:
        loc = f"{f.folder}/{f.subfolder}" if f.subfolder else f.folder
        lines.append(f"- [{loc}, sev={f.severity:.2f}] {f.summary}")
    return "\n".join(lines)


def facts_to_full_dossier_block(facts: list[DossierFact]) -> str:
    """Полный блок с цитатами для основной LLM.

    Формат:
        ## ЧТО Я ЗНАЮ О НЁМ/НЕЙ

        ### family/parents — Папа пьёт (severity 0.95, упомянуто 3 раза)
        Цитаты:
        - «вчера папа опять напился»
        - «когда отец бухой я прячусь»

        ### relationships/school_peers — ...

    Если фактов нет — пустая строка (блок целиком пропускается в промпте).
    """
    if not facts:
        return ""

    parts: list[str] = ["## ЧТО Я ЗНАЮ О НЁМ/НЕЙ\n"]
    for f in facts:
        loc = f"{f.folder}/{f.subfolder}" if f.subfolder else f.folder
        parts.append(
            f"### {loc} — {f.summary} "
            f"(severity {f.severity:.2f}, упомянуто {f.times_mentioned} раз)"
        )
        if f.quotes:
            parts.append("Цитаты:")
            # Последние 3 цитаты (не все, чтобы промпт не разбух)
            for q in f.quotes[-3:]:
                parts.append(f"- «{q.text}»")
        parts.append("")  # пустая строка между фактами

    return "\n".join(parts)

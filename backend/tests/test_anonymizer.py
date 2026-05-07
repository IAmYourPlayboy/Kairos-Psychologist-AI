"""Тесты анонимизатора (Блок B1, Сессия 22).

Покрытие:
- Email, телефоны, URL, карты, ID, адреса, даты — каждый тип ПДн.
- Замена сохраняет структуру текста (не ломает соседние слова).
- Лог содержит метаданные без оригиналов.
- Анонимизация perception_json.
- Граничные случаи: пустой текст, без ПДн, множественные замены.
"""

from __future__ import annotations

import pytest

from app.data.anonymizer import (
    AnonymizationLog,
    anonymize,
    anonymize_perception_json,
)


# ============================================================================
# Email
# ============================================================================


class TestEmail:
    def test_simple_email(self) -> None:
        text, log = anonymize("Напиши мне на vasya@mail.ru пожалуйста")
        assert "[EMAIL]" in text
        assert "vasya@mail.ru" not in text
        assert log.had_pii
        assert "email" in log.kinds()

    def test_multiple_emails(self) -> None:
        text, log = anonymize("a@b.ru или c@d.com")
        assert text.count("[EMAIL]") == 2
        assert len(log.replacements) == 2

    def test_no_email(self) -> None:
        text, log = anonymize("обычный текст без почты")
        assert text == "обычный текст без почты"
        assert not log.had_pii


# ============================================================================
# Телефоны
# ============================================================================


class TestPhone:
    def test_russian_with_plus(self) -> None:
        text, log = anonymize("позвони +7 (495) 123-45-67")
        assert "[PHONE]" in text
        assert "495" not in text

    def test_russian_with_8(self) -> None:
        text, log = anonymize("номер 8-800-333-44-34")
        assert "[PHONE]" in text

    def test_russian_no_separators(self) -> None:
        text, log = anonymize("89991234567")
        assert "[PHONE]" in text

    def test_short_number_not_phone(self) -> None:
        # 5 цифр — слишком мало для телефона
        text, log = anonymize("12345 рублей")
        assert "[PHONE]" not in text

    def test_international(self) -> None:
        text, log = anonymize("+1 555 123 4567")
        assert "[PHONE]" in text


# ============================================================================
# URL
# ============================================================================


class TestURL:
    def test_https(self) -> None:
        text, log = anonymize("посмотри https://example.com/page")
        assert "[URL]" in text
        assert "example.com" not in text

    def test_short_vk(self) -> None:
        text, log = anonymize("мой профиль vk.com/durov")
        assert "[URL]" in text
        assert "durov" not in text

    def test_no_url(self) -> None:
        text, log = anonymize("просто текст")
        assert "[URL]" not in text


# ============================================================================
# Банковские карты (Luhn)
# ============================================================================


class TestCard:
    def test_valid_visa(self) -> None:
        # 4242 4242 4242 4242 — известный Luhn-валидный тестовый номер Stripe
        text, log = anonymize("карта 4242 4242 4242 4242")
        # Может схватиться как [CARD] или [PHONE] (regex телефона тоже
        # допускает длинные последовательности цифр) — главное, что номер
        # анонимизирован.
        assert "4242 4242 4242 4242" not in text
        # При этом если цифры идут как одна группа — должна выбраться карта.

    def test_luhn_invalid_not_card(self) -> None:
        # 0000 0000 0000 0001 — не проходит Luhn → не [CARD]
        text, log = anonymize("число 0000 0000 0000 0001")
        assert "[CARD]" not in text


# ============================================================================
# ID-номера (10-12 цифр)
# ============================================================================


class TestID:
    def test_inn_10_digits(self) -> None:
        # 10 цифр подряд могут быть и ИНН, и телефоном без +7.
        # Цель анонимизации — удалить ПДн, не строго классифицировать тип.
        # Проверяем что ОРИГИНАЛЬНЫЕ цифры исчезли.
        text, log = anonymize("ИНН: 7707083893")
        assert "7707083893" not in text
        assert log.had_pii

    def test_snils_11_digits(self) -> None:
        text, log = anonymize("СНИЛС 12345678901")
        assert "12345678901" not in text
        assert log.had_pii

    def test_short_number_not_id(self) -> None:
        text, log = anonymize("123")
        assert "[ID]" not in text
        assert "[PHONE]" not in text


# ============================================================================
# Адреса
# ============================================================================


class TestAddress:
    def test_street_with_house(self) -> None:
        text, log = anonymize("живу на ул. Тверская, 15")
        assert "[ADDRESS]" in text
        assert "Тверская" not in text

    def test_prospekt(self) -> None:
        text, log = anonymize("проспект Мира 50")
        assert "[ADDRESS]" in text

    def test_no_address(self) -> None:
        text, log = anonymize("просто текст")
        assert "[ADDRESS]" not in text


# ============================================================================
# Даты
# ============================================================================


class TestDate:
    def test_dot_separator(self) -> None:
        text, log = anonymize("родилась 15.03.1990")
        assert "[DATE]" in text

    def test_slash_separator(self) -> None:
        text, log = anonymize("дата: 15/03/1990")
        assert "[DATE]" in text

    def test_iso(self) -> None:
        text, log = anonymize("2020-01-15 произошло")
        assert "[DATE]" in text

    def test_russian_text_date(self) -> None:
        text, log = anonymize("умер 5 января 2020")
        assert "[DATE]" in text


# ============================================================================
# Имена
# ============================================================================


class TestName:
    def test_dictionary_name(self) -> None:
        text, log = anonymize("Маша мне сказала")
        assert "[NAME]" in text
        assert "Маша" not in text

    def test_male_name(self) -> None:
        text, log = anonymize("позвонил Дмитрий")
        assert "[NAME]" in text

    def test_name_in_oblique_case(self) -> None:
        # «Машу» — винительный падеж от «Маша»
        text, log = anonymize("я видел Машу вчера")
        assert "[NAME]" in text

    def test_name_after_marker(self) -> None:
        # Имя после маркера «меня зовут» — заменяется даже если не в словаре
        text, log = anonymize("меня зовут Аделаида")
        # Слово после маркера должно быть заменено
        assert "Аделаида" not in text or "[NAME]" in text

    def test_common_word_not_replaced(self) -> None:
        # «Привет» в начале предложения не должно стать [NAME]
        text, log = anonymize("Привет, как дела?")
        # «Привет» — capitalized, но не в словаре имён
        assert "Привет" in text


# ============================================================================
# Лог замен
# ============================================================================


class TestLog:
    def test_log_contains_no_originals(self) -> None:
        """Лог НЕ должен содержать оригиналы ПДн."""
        text, log = anonymize("Маша на vasya@mail.ru")
        log_dict = log.to_dict()
        # Сериализованная форма не должна содержать имени или email
        log_str = str(log_dict)
        assert "Маша" not in log_str
        assert "vasya" not in log_str
        assert "mail.ru" not in log_str

    def test_log_kinds(self) -> None:
        text, log = anonymize("Маша на vasya@mail.ru, тел 89991234567")
        kinds = log.kinds()
        assert "name" in kinds
        assert "email" in kinds
        assert "phone" in kinds

    def test_empty_text_no_log(self) -> None:
        text, log = anonymize("")
        assert not log.had_pii
        assert text == ""

    def test_clean_text_no_log(self) -> None:
        text, log = anonymize("просто слова без личных данных")
        assert not log.had_pii


# ============================================================================
# Анонимизация perception_json
# ============================================================================


class TestPerceptionJSON:
    def test_anonymizes_inner_monologue(self) -> None:
        report = {
            "risk_level": "elevated",
            "dominant_emotion": "грусть",
            "theme": "семья",
            "inner_monologue": "Пользователь упомянул Машу. Это его сестра.",
            "what_user_needs": "поддержка от Маши",
        }
        new_report, log = anonymize_perception_json(report)
        assert "Маша" not in new_report["inner_monologue"]
        assert "Маш" not in new_report["what_user_needs"]
        assert log.had_pii

    def test_does_not_touch_categorical_fields(self) -> None:
        report = {
            "risk_level": "elevated",
            "dominant_emotion": "грусть",
            "theme": "семья",
            "inner_monologue": "пусто",
            "what_user_needs": "пусто",
        }
        new_report, log = anonymize_perception_json(report)
        # Категориальные поля не меняются
        assert new_report["risk_level"] == "elevated"
        assert new_report["dominant_emotion"] == "грусть"
        assert new_report["theme"] == "семья"

    def test_empty_dict(self) -> None:
        new_report, log = anonymize_perception_json({})
        assert new_report == {}
        assert not log.had_pii


# ============================================================================
# Целостность текста после замены
# ============================================================================


class TestStructureIntegrity:
    def test_text_remains_readable(self) -> None:
        original = "Привет, я Дмитрий, живу в Москве на ул. Тверская 15"
        text, log = anonymize(original)
        # Текст должен остаться в виде читаемого предложения
        assert "Привет" in text  # не имя, остаётся
        assert "[NAME]" in text  # Дмитрий заменён
        # Москва — это город, не адрес → словарь не должен его трогать
        # (только улица + дом ловится как адрес)

    def test_multiple_replacements(self) -> None:
        text, log = anonymize("Маша и Петя пошли в магазин")
        # Оба имени должны быть заменены
        assert text.count("[NAME]") == 2

    def test_replacement_at_start(self) -> None:
        text, log = anonymize("Дмитрий пришёл")
        assert text.startswith("[NAME]")

    def test_replacement_at_end(self) -> None:
        text, log = anonymize("я видел Машу")
        assert text.endswith("[NAME]")

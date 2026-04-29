"""
Извлечение фактов из диалога (Fact Extractor)
Использует LLM для извлечения структурированных фактов из сообщений пользователя
"""

from typing import List, Dict, Any
from openai import AsyncOpenAI
import json


class FactExtractor:
    """Извлекает факты из сообщений пользователя"""

    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client

    async def extract_facts(self, user_message: str) -> List[Dict[str, Any]]:
        """
        Извлечь факты из сообщения пользователя

        Args:
            user_message: Сообщение пользователя

        Returns:
            Список фактов в формате:
            [
                {
                    "category": "basic_info",
                    "field": "name",
                    "value": "Иван"
                },
                {
                    "category": "current_challenges",
                    "value": {
                        "challenge": "развод",
                        "severity": "high"
                    }
                }
            ]
        """

        system_prompt = """Ты — ассистент, который извлекает факты о пользователе из диалога.

Твоя задача: проанализировать сообщение пользователя и извлечь все факты о нём в структурированном формате.

КАТЕГОРИИ ФАКТОВ:
- basic_info: имя, возраст, пол, город, профессия
- life_stages: детство, юность, взрослая жизнь
- relationships: статус отношений, семья, друзья
- work: работа, карьера, удовлетворённость
- health: физическое и ментальное здоровье
- current_challenges: текущие проблемы
- goals: цели пользователя
- values: ценности
- coping_strategies: что помогает/не помогает
- preferences: предпочтения в общении

ФОРМАТ ОТВЕТА (JSON):
{
    "facts": [
        {
            "category": "basic_info",
            "field": "name",
            "value": "Иван",
            "confidence": 0.95
        }
    ]
}

ПРАВИЛА:
1. Извлекай только явные факты, не додумывай
2. Если факт неоднозначен — укажи низкую confidence
3. Для current_challenges указывай severity: low/medium/high/critical
4. Не извлекай факты, которые уже устарели (например, "раньше работал X" — не сохраняй как текущую работу)
"""

        user_prompt = f"""Сообщение пользователя:
"{user_message}"

Извлеки все факты о пользователе."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Быстрая модель для извлечения фактов
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("facts", [])

        except Exception as e:
            print(f"Error extracting facts: {e}")
            return []

    async def should_update_dossier(self, user_message: str) -> bool:
        """
        Определить, содержит ли сообщение факты, которые нужно сохранить в досье

        Быстрая проверка перед полным извлечением фактов
        """

        # Простая эвристика: если сообщение содержит личную информацию
        personal_keywords = [
            "меня зовут", "мне ", "лет", "работаю", "живу",
            "женат", "замужем", "разведён", "развелась",
            "мама", "папа", "родители", "друг", "подруга",
            "болею", "диагноз", "проблема", "цель", "хочу"
        ]

        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in personal_keywords)

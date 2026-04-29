"""Агент 6: ModuleBuilder Agent — создание скиллов и модулей.

Создаёт готовые к использованию скиллы и Python-модули
из эталонных агрегированных статей.
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.shared.base_agent import BaseAgent
from agents.shared.knowledge_base import KnowledgeBase
from agents.brain.aggregator_agent import ConsolidatedArticle, Source

logger = logging.getLogger(__name__)


class ModuleBuilderAgent(BaseAgent):
    """Агент построения модулей.

    Преобразует эталонные статьи в:
    1. Python модули для backend/app/core/knowledge/
    2. Скиллы для skills/
    3. Обновляет therapy_router.py
    4. Обновляет prompts/builder.py
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        skills_path: str = "skills",
        knowledge_module_path: str = "backend/app/core/knowledge",
    ) -> None:
        """
        Args:
            knowledge_base: База знаний
            skills_path: Путь к папке скиллов
            knowledge_module_path: Путь к Python-модулям
        """
        super().__init__(name="ModuleBuilderAgent", priority=6)
        self._kb = knowledge_base
        self._skills_path = Path(skills_path)
        self._module_path = Path(knowledge_module_path)

    async def run(self, context: dict) -> dict:
        """Создать модуль из эталонной статьи.

        Args:
            context: {
                "article": ConsolidatedArticle,
                "create_skill": bool = True,
                "create_module": bool = True,
                "update_router": bool = True,
            }

        Returns:
            {
                "skill_created": bool,
                "module_created": bool,
                "router_updated": bool,
                "files": list[str]
            }
        """
        article: ConsolidatedArticle = context["article"]
        create_skill = context.get("create_skill", True)
        create_module = context.get("create_module", True)
        update_router = context.get("update_router", True)

        logger.info(f"Построение модуля из статьи: {article.id}")

        result = {
            "skill_created": False,
            "module_created": False,
            "router_updated": False,
            "files": [],
        }

        # 1. Создать Python модуль
        if create_module:
            module_path = await self._create_python_module(article)
            if module_path:
                result["module_created"] = True
                result["files"].append(module_path)

        # 2. Создать скилл
        if create_skill:
            skill_path = await self._create_skill(article)
            if skill_path:
                result["skill_created"] = True
                result["files"].append(skill_path)

        # 3. Обновить therapy_router.py
        if update_router:
            router_updated = await self._update_therapy_router(article)
            result["router_updated"] = router_updated

        logger.info(f"Модуль построен. Файлов создано: {len(result['files'])}")

        return result

    async def _create_python_module(
        self, article: ConsolidatedArticle
    ) -> Optional[str]:
        """Создать Python модуль в backend/app/core/knowledge/.

        Args:
            article: Эталонная статья

        Returns:
            Путь к созданному файлу
        """
        topic = article.topic
        module_name = self._sanitize_name(topic)

        # Путь к файлу
        module_file = self._module_path / f"{module_name}.py"
        module_file.parent.mkdir(parents=True, exist_ok=True)

        # Генерация кода
        code = self._generate_python_module(article, module_name)

        with open(module_file, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"Создан модуль: {module_file}")
        return str(module_file)

    def _generate_python_module(
        self, article: ConsolidatedArticle, module_name: str
    ) -> str:
        """Генерировать код Python модуля."""
        # Сформировать строку источников
        sources_list = []
        for s in article.sources[:5]:
            sources_list.append(
                f'    "{s.name}": "{s.full_name}",  # {s.contribution[:50]}..."'
            )
        sources_str = "\n".join(sources_list) if sources_list else '    "[default]": "Научные источники"'

        # Сформировать техники (из metadata)
        techniques = article.metadata.get("techniques", [])
        techniques_list = []
        for t in techniques:
            techniques_list.append(f'    "{t["name"]}": "{t["description"]}"')
        techniques_str = "\n".join(techniques_list) if techniques_list else '    "base": "Базовые техники поддержки"'

        # Сторителлинг (обрезать до разумного размера)
        story_lines = article.story.split("\n")[:10]
        story_str = '"""\n' + "\n".join(f"# {line}" for line in story_lines) + '\n"""'

        code = f'''"""Модуль знаний: {article.title}.

Автогенерирован из эталонной статьи {article.id}.
Дата создания: {datetime.now().strftime("%Y-%m-%d")}
"""

{story_str}

# ============================================================================
# МЕТАДАННЫЕ
# ============================================================================

TOPIC = "{article.topic}"
CONFIDENCE = "{article.confidence}"
CONTROVERSY_LEVEL = "{article.controversy_level}"

# Уровень доверия: HIGH = можно использовать в промптах
# MEDIUM = требует осторожности
# LOW = только для справки

# ============================================================================
# ИСТОЧНИКИ
# ============================================================================

SOURCES = {{
{sources_str}
}}

# Для ответа "почему ты так считаешь?" —
# бот находит тег источника и использует сторителлинг из sources_info

# ============================================================================
# ТЕХНИКИ
# ============================================================================

TECHNIQUES = {{
{techniques_str}
}}

# Ключевые техники из научных источников
# Каждая техника: название и краткое описание

# ============================================================================
# STORYTELLING (для объяснения пользователю)
# ============================================================================

STORYTELLING = """
{article.story[:2000]}
"""
# Полный сторителллинг хранится в эталонной статье
# Этот срез для быстрого доступа

# ============================================================================
# КОНСЕНСУС И НЮАНСЫ
# ============================================================================

CONSENSUS = """
{article.consensus[:1000]}
"""

NUANCES = """
{article.nuances[:1000]}
"""

# ============================================================================
# ФУНКЦИИ ДЛЯ ИСПОЛЬЗОВАНИЯ В ПРОМПТАХ
# ============================================================================

def get_prompt_context() -> dict:
    """Получить контекст для промпта.

    Returns:
        dict с ключами: consensus, nuances, techniques, storytelling
    """
    return {{
        "topic": TOPIC,
        "consensus": CONSENSUS.strip(),
        "nuances": NUANCES.strip(),
        "techniques": TECHNIQUES,
        "storytelling": STORYTELLING.strip(),
        "confidence": CONFIDENCE,
        "controversy_level": CONTROVERSY_LEVEL,
    }}


def get_source_info(source_tag: str) -> dict | None:
    """Получить информацию об источнике по тегу.

    Args:
        source_tag: Тег источника, например "[Worden]"

    Returns:
        dict с информацией об источнике или None
    """
    return None  # Заглушка — реальная реализация ниже


# Информация об источниках для сторителлинга
SOURCES_INFO = {{
'''

        # Добавить информацию об источниках
        for s in article.sources[:5]:
            code += f'''    "{s.name}": {{
        "full_name": "{s.full_name}",
        "reference": "{s.reference[:100]}",
        "contribution": "{s.contribution}",
        "story": 'Жил был {s.full_name}. '  # Реальный сторителлинг из эталонной статьи
    }},
'''

        code += "}\n"

        # Функция для поиска источника
        code += '''
def get_source_info(source_tag: str) -> dict | None:
    """Получить информацию об источнике по тегу.

    Args:
        source_tag: Тег источника, например "[Worden]"

    Returns:
        dict с информацией или None
    """
    return SOURCES_INFO.get(source_tag)
'''

        return code

    async def _create_skill(self, article: ConsolidatedArticle) -> Optional[str]:
        """Создать скилл в skills/.

        Args:
            article: Эталонная статья

        Returns:
            Путь к созданному файлу
        """
        topic = article.topic
        skill_name = self._sanitize_name(topic)

        # Путь к файлу
        skill_file = self._skills_path / f"{skill_name}.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)

        # Генерация контента
        content = self._generate_skill_content(article, skill_name)

        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Создан скилл: {skill_file}")
        return str(skill_file)

    def _generate_skill_content(
        self, article: ConsolidatedArticle, skill_name: str
    ) -> str:
        """Генерировать контент скилла."""
        # Техники в виде списка
        techniques_list = []
        for t_name, t_desc in list(article.metadata.get("techniques", {}).items())[:5]:
            techniques_list.append(f"- **{t_name}**: {t_desc}")
        techniques_str = "\n".join(techniques_list) if techniques_list else "- Базовые техники поддержки"

        # Источники
        sources_list = []
        for s in article.sources[:5]:
            sources_list.append(f"- **{s.name}**: {s.full_name} — {s.contribution[:50]}")
        sources_str = "\n".join(sources_list)

        content = f'''# Скилл: {article.title}

> Автогенерирован из эталонной статьи {article.id}
> Уровень доверия: {article.confidence}
> Последняя проверка: {article.last_reviewed.strftime("%Y-%m-%d")}

---

## Описание

{article.consensus[:500]}

---

## Контекст для AI-ассистента

### Когда использовать этот скилл
- Пользователь спрашивает о теме: {", ".join(article.tags[:5])}
- NLP определил тему как "{article.topic}"
- Требуется объяснить концепцию простым языком

### Как использовать
```python
from backend.app.core.knowledge.{skill_name} import get_prompt_context

context = get_prompt_context()
# context содержит: consensus, nuances, techniques, storytelling
```

---

## Ключевые техники

{techniques_str}

---

## Сторителлинг для пользователя

{article.story[:1500]}

---

## Источники

{sources_str}

---

## Нюансы и разногласия

{article.nuances[:500]}

---

## Для ответа "Почему ты так считаешь?"

Когда пользователь спрашивает "почему?", найди соответствующий тег
используй сторителлинг из секции "Источники".

---

*Этот скилл автогенерирован. При обнаружении ошибок — исправь вручную
и обнови эталонную статью.*
'''

        return content

    async def _update_therapy_router(
        self, article: ConsolidatedArticle
    ) -> bool:
        """Обновить therapy_router.py.

        Args:
            article: Эталонная статья

        Returns:
            True если обновлён
        """
        router_path = self._module_path.parent / "therapy_router.py"

        if not router_path.exists():
            logger.warning(f"therapy_router.py не найден: {router_path}")
            return False

        # Читаем существующий файл
        with open(router_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверяем, есть ли уже эта тема
        topic = article.topic
        if topic in content:
            logger.info(f"Тема '{topic}' уже есть в therapy_router.py")
            return False

        # Добавляем импорт модуля
        module_name = self._sanitize_name(topic)
        import_line = f"from app.core.knowledge.{module_name} import get_prompt_context"

        # Ищем место для добавления (после существующих импортов)
        # Простой подход: добавляем в конец блока импортов

        # Найти последний импорт из knowledge
        import_pattern = r"(from app\.core\.knowledge\.\w+ import .*\n)"
        matches = list(re.finditer(import_pattern, content))

        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            new_content = (
                content[:insert_pos]
                + import_line
                + "\n"
                + content[insert_pos:]
            )
        else:
            # Нет импортов — добавляем в конец imports
            new_content = content + f"\n{import_line}\n"

        # Добавляем тему в router mapping
        # Ищем секцию TOPIC_MAPPING или создаём
        mapping_pattern = r"(TOPIC_MAPPING\s*=\s*\{[^}]*\}"
        if re.search(mapping_pattern, new_content):
            # Добавляем в существующий mapping
            new_content = re.sub(
                mapping_pattern,
                lambda m: m.group(0) + f',\n    "{topic}": "{module_name}"',
                new_content
            )
        else:
            # Создаём новый mapping
            new_content += f'''
# Автогенерировано ModuleBuilderAgent
TOPIC_MAPPING = {{
    "{topic}": "{module_name}",
}}
'''

        # Сохраняем
        with open(router_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"Обновлён therapy_router.py: добавлен {topic}")
        return True

    def _sanitize_name(self, topic: str) -> str:
        """Преобразовать название темы в валидное имя модуля.

        Args:
            topic: Название темы, например "grief" или "emotional-regulation"

        Returns:
            "grief", "emotional_regulation"
        """
        # Заменить дефисы и пробелы на подчёркивания
        name = topic.lower().replace("-", "_").replace(" ", "_")
        # Убрать всё кроме букв, цифр и подчёркиваний
        name = re.sub(r"[^a-z0-9_]", "", name)
        return name

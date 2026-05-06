# CSS-Variables Foundation для Кайроса: дизайн

> **Версия**: 1.0
> **Дата**: 2026-05-06 (Сессия 21 / Phase 9)
> **Статус**: дизайн утверждён пользователем, ждёт review перед передачей в writing-plans
> **Дополняет**: `2026-05-06-frontend-figma-redesign-design.md` (Сессия 19) — закладывает архитектурный фундамент для будущей миграции с Tailwind

---

## 1. Зачем

В Сессии 19 фронтенд был полностью переделан под дизайн из Figma Make: glassmorphism, dark/light тема, плавающие элементы. Реализация работает, но имеет два **архитектурных долга**, которые проявились во время manual regression:

**Долг A — z-stack хаос.**

Текущее состояние z-index'ов в `frontend/`:

```
z-0       Background (decorative)
z-10      AppShell wrapper
z-20      RightDock
z-30      Sidebar               ← конфликт
z-30      SOSButton              ← конфликт (тот же z, разные слои)
z-40      FloatingButtons
z-50      Sidebar context-menu
z-50      DialogOverlay
z-50      DialogContent
```

Проблемы:
- **Конфликт на z-30**: Sidebar (структурный) и SOSButton (плавающий control) на одном уровне. На widescreen это ничего не ломает, но на узком viewport SOS может попасть за край сайдбара.
- **Перегрузка z-50**: context-menu, Dialog overlay и Dialog content — всё одинаково. Если context-menu откроется одновременно с Dialog (теоретически, через клавиатуру) — поведение непредсказуемо.
- **Magic numbers**: 10 разных мест в коде с числами 0/10/20/30/40/50, без единого источника правды. Любое изменение требует grep по всему коду.
- **Tab-порядок прыгает**: a11y test Сессии 19 показал что Tab проходит «sidebar → settings/toggle → SOS → пропадает на 2 нажатия → телефоны в дисклеймере → тема/профиль». Это потому что DOM-порядок не совпадает с z-stack-порядком, и focus-ring почти невидим на тёмных стеклянных фонах.

**Долг B — Tailwind lock-in.**

Все цвета, glass-эффекты, размеры объявлены в `tailwind.config.ts` и используются как `className="bg-warm-50 dark:bg-neutral-950 backdrop-blur-md ..."`. Это **atomic-CSS-pattern**, который имеет известную проблему: **стили физически живут в JSX-компонентах**, а не в дизайн-системе.

Если в будущем понадобится:
- Перейти на **CSS Modules** (для лучшего code-splitting и SSR-производительности)
- Использовать **vanilla-extract** или **Panda CSS** (type-safe styling)
- Подключить **styled-components** или **Emotion**
- Полностью отказаться от Tailwind в пользу **vanilla CSS**
- Сделать **дизайн-токены доступными в Figma** через единый источник правды

— потребуется переписать десятки JSX-файлов с `className="..."`. Перенесение Сессии 19 (glassmorphism + темы) на новый стек будет неделей работы.

Пользователь зафиксировал в брейншторме Сессии 21:

> «Tailwind я не переношу, и… структурно классно, но я не хочу в будущем видеть только tailwind»

**Цель Сессии 21** — не уходить от Tailwind сейчас, но **закладывать фундамент** для будущей миграции. Делаем минимальный, но правильный шаг: **CSS Variables First**.

## 2. Что мы строим

Фундаментальный рефакторинг визуальных токенов: палитра, glass-эффекты, z-layers, типографика — всё переезжает в **CSS custom properties** (`:root` + `.dark`). Tailwind `theme.extend` становится **тонкой обёрткой**, которая мапит эти CSS-vars в Tailwind-классы для удобства использования.

### Архитектурная схема

```
                        ИСТОЧНИК ПРАВДЫ
                        ┌──────────────┐
                        │  globals.css │
                        │              │
                        │  :root {     │  ← 60+ CSS variables:
                        │    --z-...   │     palette, glass, z-layers
                        │    --color-..│
                        │    --glass-..│
                        │  }           │
                        │              │
                        │  .dark {     │  ← override для тёмной темы
                        │    --color-..│
                        │  }           │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
       │ tailwind.    │ │ Прямой      │ │ Будущие      │
       │ config.ts    │ │ доступ из   │ │ инструменты  │
       │              │ │ inline-style│ │ (CSS Modules,│
       │ Мапит CSS-vars│ │            │ │  Panda CSS,  │
       │ в Tailwind   │ │ <div style={{│ │  styled-comp)│
       │ classes      │ │  zIndex: 'var(--z-modal)'│ │              │
       │              │ │ }}>        │ │ — все умеют  │
       │ z-decorative │ │            │ │ читать CSS-  │
       │ z-structure  │ │            │ │ vars         │
       │ bg-warm-50   │ │            │ │              │
       │ ...          │ │            │ │              │
       └──────┬───────┘ └─────────────┘ └──────────────┘
              │
              ▼
       ┌──────────────┐
       │ React        │  ← 99% использования сейчас
       │ компоненты   │
       │              │
       │ className="  │
       │  z-structure │
       │  bg-warm-50  │
       │  ..."        │
       └──────────────┘
```

**Что это даёт прямо сейчас:**
1. **Z-layers становятся семантичными.** `z-30` → `z-structure`. Конфликт Sidebar/SOS на z-30 разрешается естественно.
2. **Цвета централизуются.** Один файл (`globals.css`) видит всю палитру. Меняешь оттенок warm-500 — меняется во всех местах сразу.
3. **Тёмная тема упрощается.** Не нужно дублировать `dark:` варианты в `tailwind.config.ts` — один блок `.dark { --color-bg: ...; }` переопределяет всё.

**Что это даёт в будущем (когда захочешь):**
4. Можешь мигрировать **по одному компоненту за раз** на любой другой стек. Component A остаётся на Tailwind, component B переходит на CSS Modules — оба читают одни и те же CSS-vars. Никаких ломающих изменений.
5. Дизайн-токены становятся **переносимыми**: можно экспортировать в Figma Tokens (через JSON), синхронизировать с дизайнером.
6. Если завтра придёт новый AI-tool который генерит CSS Modules вместо Tailwind — он сможет работать на тех же токенах что и текущий Tailwind-код.

### Принципы

1. **CSS variables — единственный источник правды.** Не дублируем значения в `tailwind.config.ts`. Tailwind читает CSS-vars через `var(--name)` синтаксис.
2. **Семантические имена слоёв.** Никаких magic numbers. `z-structure`, `z-modal`, `z-toast` — если читаешь код впервые, сразу понимаешь логику.
3. **Обратная совместимость API хуков.** `useThemeTokens()` продолжает возвращать Tailwind-классы. Меняем только их внутренние значения. **0 изменений в 100+ местах вызова.**
4. **Минимум новых концепций.** Никаких CSS Modules, никаких новых build-tools. Только CSS-vars (которые понимает любой браузер с 2017 года) + Tailwind 3.4 (текущий, не апгрейдим до v4).
5. **Тёмная тема — переопределение токенов, а не новый набор классов.** `.dark` блок меняет CSS-vars — Tailwind-классы автоматически перерисовываются.
6. **Tab-порядок и a11y фиксы — параллельно.** Раз уж трогаем layout-слои — делаем focus-ring видимым и проверяем DOM-порядок.

## 3. Объём изменений (overview)

```
ТРОГАЕМ:
  ├── frontend/app/globals.css         (REWRITE: + CSS-vars блок)
  ├── frontend/tailwind.config.ts      (REWRITE: цвета + z через var())
  ├── frontend/components/Layout/      (CHANGE z-classes на семантические)
  │   ├── Background.tsx                z-0 → z-decorative
  │   ├── AppShell.tsx                  z-10 → z-content
  │   ├── Sidebar.tsx                   z-30 → z-structure (+ context-menu z-50 → z-overlay)
  │   ├── RightDock.tsx                 z-20 → z-floating-low
  │   ├── FloatingButtons.tsx           z-40 → z-floating-high
  │   ├── TipCard.tsx                   локальный z-10 уточняем
  │   └── ThemeScript.tsx               (no change)
  ├── frontend/components/Chat/
  │   └── ChatContainer.tsx             SOS z-30 → z-floating-high
  ├── frontend/components/ui/
  │   └── Dialog.tsx                    z-50 → z-modal-backdrop / z-modal
  └── docs/superpowers/specs/...        (этот файл)
  └── docs/superpowers/plans/...        (план реализации)
  └── CLAUDE.md, PROGRESS.md            (docs Сессия 21)

НЕ ТРОГАЕМ:
  ├── frontend/hooks/                   (useThemeTokens возвращает те же классы)
  ├── frontend/lib/                     (cn, theme-config — без изменений)
  ├── backend/                          (никаких бекенд-изменений)
  └── любая бизнес-логика (useChat, crisis-routing, perception)
```

## 4. CSS Variables: структура и значения

Все переменные живут в `frontend/app/globals.css`. Сгруппированы в 5 блоков для читаемости:

### 4.1 Z-layers (9 уровней, 3 семантические группы)

```css
:root {
  /* ===== Z-LAYERS =====
   * Семантические уровни наложения. Никаких magic numbers в JSX.
   *
   * Группа 1 — DECORATIVE: фон и декоративные слои. pointer-events: none.
   * Группа 2 — STRUCTURAL: контент и навигационные панели.
   * Группа 3 — INTERACTIVE: плавающие controls, overlays, modals, toasts.
   *
   * Между группами — щель в 10 единиц для будущих вставок без сдвига.
   */
  --z-decorative:     0;   /* Background картинка + темовый overlay */
  --z-content:       10;   /* AppShell content wrapper, main, лента сообщений */
  --z-structure:     20;   /* Sidebar — стеклянная панель НАД фоном НО ПОД плавающими controls */
  --z-floating-low:  30;   /* RightDock — тоггл темы, аватар, TipCard */
  --z-floating-high: 40;   /* SOSButton, FloatingButtons (settings/toggle) — должны быть ВЫШЕ RightDock */
  --z-overlay:       50;   /* Context menus, dropdown'ы, popovers — открываются ОТ floating элементов */
  --z-modal-backdrop: 60;  /* Полупрозрачная подложка модалки — должна быть ВЫШЕ всего интерактивного UI */
  --z-modal:         70;   /* CrisisPanel, RenameDialog — сама модалка */
  --z-toast:         80;   /* Sonner Toaster — выше всего, чтобы оповещения всегда видны */
}
```

**Обоснование уровней:**

| От | До | Зачем |
|---|---|---|
| `decorative` < `content` | Фон должен быть позади всего | Очевидно |
| `content` < `structure` | Sidebar должен накладываться на main (стеклянный эффект над фото) | Glassmorphism требование |
| `structure` < `floating-low` | RightDock должен быть видим даже когда сайдбар развёрнут | Иначе при `width: 240px` сайдбар закроет правую часть |
| `floating-low` < `floating-high` | SOS должен быть выше RightDock-аватара (они находятся на одной visual-зоне в правом верхнем углу) | Безопасность: SOS всегда доступен |
| `floating-high` < `overlay` | Меню откроется ОТ кнопки и должно перекрывать другие плавающие элементы | UX-стандарт |
| `overlay` < `modal-backdrop` | Подложка модалки гасит ВСЁ под ней | Modal best practice |
| `modal-backdrop` < `modal` | Сам контент модалки выше своей подложки | Очевидно |
| `modal` < `toast` | Тосты "ваш чат удалён" должны быть видны ДАЖЕ когда открыта модалка | Toast/Snackbar pattern |

### 4.2 Color palette — RGB-тройки (для Tailwind alpha-channel синтаксиса)

Tailwind v3 поддерживает `rgb(var(--name) / <alpha-value>)` — это позволяет писать `bg-warm-50/80` (warm-50 с alpha 0.8). Для этого CSS-vars должны быть RGB **тройками**, разделёнными пробелами (без `rgb()` обёртки).

```css
:root {
  /* ===== PALETTE =====
   * RGB-тройки (без rgb()/без запятых) для Tailwind alpha-channel синтаксиса.
   * Использование: rgb(var(--color-warm-50) / 0.8) — это warm-50 с alpha 0.8.
   *
   * Палитра не меняется между темами — меняются только семантические aliases (см. 4.3).
   */

  /* warm — тёплая нейтральная база (фон, текст) */
  --color-warm-50:  250 247 242;   /* #FAF7F2 */
  --color-warm-100: 244 239 231;   /* #F4EFE7 */
  --color-warm-200: 232 223 208;   /* #E8DFD0 */
  --color-warm-300: 212 197 174;   /* #D4C5AE */
  --color-warm-400: 184 164 136;   /* #B8A488 */
  --color-warm-500: 157 136 107;   /* #9D886B */
  --color-warm-600: 126 109  84;   /* #7E6D54 */
  --color-warm-700:  95  82  64;   /* #5F5240 */
  --color-warm-800:  63  54  43;   /* #3F362B */
  --color-warm-900:  31  27  22;   /* #1F1B16 */

  /* accent — спокойный синий (доверие, безопасность) */
  --color-accent-50:  238 244 248;   /* #EEF4F8 */
  --color-accent-100: 214 227 237;   /* #D6E3ED */
  --color-accent-200: 174 206 219;   /* #AECEDB */
  --color-accent-300: 122 177 194;   /* #7AB1C2 */
  --color-accent-400:  77 147 168;   /* #4D93A8 */
  --color-accent-500:  53 117 136;   /* #357588 */
  --color-accent-600:  40  89 106;   /* #28596A */
  --color-accent-700:  29  65  76;   /* #1D414C */
  --color-accent-800:  20  43  51;   /* #142B33 */
  --color-accent-900:  11  23  25;   /* #0B1719 */

  /* crisis — приглушённый красный (тревога, не паника) */
  --color-crisis-50:  250 240 238;   /* #FAF0EE */
  --color-crisis-100: 244 217 212;   /* #F4D9D4 */
  --color-crisis-200: 232 176 166;   /* #E8B0A6 */
  --color-crisis-300: 217 132 122;   /* #D9847A */
  --color-crisis-400: 199  87  79;   /* #C7574F */
  --color-crisis-500: 165  58  54;   /* #A53A36 */
  --color-crisis-600: 127  42  41;   /* #7F2A29 */
  --color-crisis-700:  92  30  29;   /* #5C1E1D */
  --color-crisis-800:  62  20  20;   /* #3E1414 */
  --color-crisis-900:  31  10  10;   /* #1F0A0A */

  /* neutral — нейтральная шкала (для тёмной темы фон, dark mode UI) */
  --color-neutral-50:  250 250 250;
  --color-neutral-100: 245 245 245;
  --color-neutral-200: 229 229 229;
  --color-neutral-300: 212 212 212;
  --color-neutral-400: 163 163 163;
  --color-neutral-500: 115 115 115;
  --color-neutral-600:  82  82  82;
  --color-neutral-700:  64  64  64;
  --color-neutral-800:  38  38  38;
  --color-neutral-900:  23  23  23;
  --color-neutral-950:  10  10  10;
}
```

**Что это даёт:**
- `bg-warm-50` → `background-color: rgb(var(--color-warm-50));` → `rgb(250 247 242)`
- `bg-warm-50/80` → `background-color: rgb(var(--color-warm-50) / 0.8);` → `rgb(250 247 242 / 0.8)`
- `text-accent-500` → `color: rgb(var(--color-accent-500));`

Tailwind генерирует CSS automatically — мы только меняем источник значений с хардкода на CSS-var.

**Зачем `neutral` — это новая шкала?** В текущем коде используется `bg-neutral-950` (для тёмной темы body). Tailwind поставляет `neutral-50..950` из коробки, но эти значения **захардкожены в `tailwind/colors`**. Чтобы и нейтральная шкала была переопределяема через CSS-vars (например, для будущей кастомизации dark-режима) — выносим её. Это 11 значений (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, **950**), потому что `neutral-950` существует только начиная с Tailwind 3.4.

### 4.3 Semantic aliases (тема-зависимые)

Это блок, который **переопределяется в `.dark`**. Здесь живут абстрактные имена («фон», «текст», «бордер»), которые автоматически меняются между темами.

**Зачем нужно:** в существующем `useThemeTokens` логика «`text-warm-900` для светлой темы, `text-white` для тёмной» зашита в JS. Это работает, но:
- Любое использование цвета вне `useThemeTokens` (например, инлайн в компоненте) дублирует эту логику.
- Будущим инструментам (CSS Modules) такая абстракция недоступна — им нужны CSS-vars.

Решение: ключевые семантические алиасы живут как CSS-vars и переопределяются в `.dark` блоке. Tailwind может использовать их через `bg-[rgb(var(--text-primary))]` или мы добавим их в `theme.extend.colors` как именованные классы (`bg-text-primary`).

```css
:root {
  /* ===== SEMANTIC ALIASES (light theme defaults) =====
   * Эти переменные имеют РАЗНЫЕ значения в .dark.
   * Все компоненты должны предпочитать их вместо прямых обращений к
   * --color-warm-N / --color-neutral-N когда нужна тема-зависимость.
   */

  /* Фон страницы (body), панелей, карточек по умолчанию */
  --bg-base:        var(--color-warm-50);
  --bg-elevated:    var(--color-warm-100);     /* приподнятые элементы (карточки) */
  --bg-sunken:      var(--color-warm-200);     /* «утопленные» зоны (input, code) */

  /* Текст */
  --text-primary:   var(--color-warm-900);     /* основной */
  --text-secondary: var(--color-warm-700);     /* подзаголовки, описания */
  --text-muted:     var(--color-warm-600);     /* третичный, disclaimer */
  --text-inverted:  var(--color-warm-50);      /* на тёмном фоне в светлой теме (например, на accent-700 кнопке) */

  /* Бордеры и разделители */
  --border-subtle:  var(--color-warm-200);
  --border-default: var(--color-warm-300);

  /* Surface — стеклянные панели */
  --surface-rgb:    255 255 255;               /* RGB для стекла (светлая тема — белое стекло) */
  --surface-alpha-low:  0.6;                   /* для glassSidebar */
  --surface-alpha-high: 0.7;                   /* для glassPanel */
  --surface-border-rgb: 255 255 255;
  --surface-border-alpha-low:  0.4;
  --surface-border-alpha-high: 0.6;
}

.dark {
  /* ===== SEMANTIC ALIASES (dark theme overrides) ===== */

  --bg-base:        var(--color-neutral-950);
  --bg-elevated:    var(--color-neutral-900);
  --bg-sunken:      var(--color-neutral-800);

  --text-primary:   var(--color-neutral-50);
  --text-secondary: 255 255 255;               /* white с alpha управляется на месте через text-text-secondary/60 */
  --text-muted:     255 255 255;               /* same */
  --text-inverted:  var(--color-neutral-900);

  --border-subtle:  var(--color-neutral-800);
  --border-default: var(--color-neutral-700);

  /* Surface — чёрное стекло в тёмной теме */
  --surface-rgb:    0 0 0;
  --surface-alpha-low:  0.3;
  --surface-alpha-high: 0.4;
  --surface-border-rgb: 255 255 255;
  --surface-border-alpha-low:  0.1;
  --surface-border-alpha-high: 0.1;
}
```

⚠ **Важная тонкость:** RGB-тройки используются с alpha-каналом через формат `rgb(R G B / A)`. Поэтому `--text-secondary: 255 255 255` — это **не белый текст**, а **«источник RGB для белого»**. Использование: `color: rgb(var(--text-secondary) / 0.6);` → белый с alpha 0.6. Tailwind делает это автоматически через `theme.extend.colors`.

### 4.4 Glass tokens

Композитные значения (несколько свойств сразу), на которых построен весь glassmorphism эффект:

```css
:root {
  /* ===== GLASS TOKENS =====
   * Значения blur соответствуют дефолтам Tailwind backdrop-blur-*,
   * поэтому существующие классы backdrop-blur-md / -xl / -2xl продолжают
   * работать идентично текущему визуалу. См. §12.1 для полного маппинга.
   */
  --glass-blur-sm:   4px;
  --glass-blur:      8px;   /* Tailwind backdrop-blur (default) */
  --glass-blur-md:  12px;
  --glass-blur-lg:  16px;
  --glass-blur-xl:  24px;
  --glass-blur-2xl: 40px;

  /* Стеклянные панели (используются в glassSidebar / glassPanel) */
  --glass-sidebar-bg:    rgb(var(--surface-rgb) / var(--surface-alpha-low));
  --glass-sidebar-border: rgb(var(--surface-border-rgb) / var(--surface-border-alpha-low));

  --glass-panel-bg:      rgb(var(--surface-rgb) / var(--surface-alpha-high));
  --glass-panel-border:  rgb(var(--surface-border-rgb) / var(--surface-border-alpha-high));

  /* Темовый overlay поверх Background (картинки) */
  --overlay-bg-light:    rgba(255, 255, 255, 0.20);
  --overlay-bg-dark:     rgba(0, 0, 0, 0.50);
}
```

Эти значения используются в Tailwind классах `bg-glass-panel`, `border-glass-panel-border` (см. Раздел 5 — Tailwind config).

### 4.5 Typography tokens (минимально)

```css
:root {
  /* ===== TYPOGRAPHY ===== */
  --font-sans: var(--font-golos), ui-sans-serif, system-ui, sans-serif;

  /* Высоты UI-элементов (для будущей синхронизации с Figma) */
  --header-height: 56px;
  --footer-height: 40px;

  /* Sidebar */
  --sidebar-width: 240px;
  --right-dock-width: 280px;
  --right-dock-width-md: 260px;
}
```

`--sidebar-width` и `--right-dock-width` особенно важны: сейчас они **дублируются** в `Sidebar.tsx` (`const SIDEBAR_WIDTH = 240`) и `FloatingButtons.tsx` (импортирует ту же константу) и `RightDock.tsx` (`w-[260px] lg:w-[280px]`). После рефактора эти значения станут единым источником в CSS-vars, а TypeScript-константа `SIDEBAR_WIDTH` либо читает из CSS-var через `getComputedStyle`, либо остаётся жёсткой ссылкой с комментарием «keep in sync with --sidebar-width». Делаем ВТОРОЕ для простоты — TS-константа с комментарием. Это компромисс, но минимальный.

## 5. Tailwind Config: тонкая обёртка над CSS-vars

Файл `frontend/tailwind.config.ts` переписывается так, чтобы цвета, z-индексы и семантические алиасы читались из CSS-vars:

```ts
import type { Config } from "tailwindcss";

/**
 * Tailwind конфигурация Кайроса (Сессия 21+).
 *
 * Сам файл — ТОНКАЯ ОБЁРТКА: значения читаются из CSS variables
 * в frontend/app/globals.css. Если хочешь поменять цвет — иди в globals.css.
 *
 * Зачем: дизайн-токены не привязаны к Tailwind. В будущем компонент
 * можно будет мигрировать на CSS Modules / Panda CSS / любой другой стек —
 * он будет читать ТЕ ЖЕ переменные, никаких ломающих изменений.
 *
 * Спека: docs/superpowers/specs/2026-05-06-css-variables-foundation-design.md
 */
const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ====================================================================
      // Z-LAYERS
      // Семантические имена слоёв вместо magic numbers.
      // ====================================================================
      zIndex: {
        decorative: "var(--z-decorative)",
        content: "var(--z-content)",
        structure: "var(--z-structure)",
        "floating-low": "var(--z-floating-low)",
        "floating-high": "var(--z-floating-high)",
        overlay: "var(--z-overlay)",
        "modal-backdrop": "var(--z-modal-backdrop)",
        modal: "var(--z-modal)",
        toast: "var(--z-toast)",
      },

      // ====================================================================
      // COLORS
      // Все палитры — RGB-тройки из CSS-vars + alpha-channel поддержка.
      // ====================================================================
      colors: {
        warm: {
          50:  "rgb(var(--color-warm-50)  / <alpha-value>)",
          100: "rgb(var(--color-warm-100) / <alpha-value>)",
          200: "rgb(var(--color-warm-200) / <alpha-value>)",
          300: "rgb(var(--color-warm-300) / <alpha-value>)",
          400: "rgb(var(--color-warm-400) / <alpha-value>)",
          500: "rgb(var(--color-warm-500) / <alpha-value>)",
          600: "rgb(var(--color-warm-600) / <alpha-value>)",
          700: "rgb(var(--color-warm-700) / <alpha-value>)",
          800: "rgb(var(--color-warm-800) / <alpha-value>)",
          900: "rgb(var(--color-warm-900) / <alpha-value>)",
        },
        accent: {
          50:  "rgb(var(--color-accent-50)  / <alpha-value>)",
          100: "rgb(var(--color-accent-100) / <alpha-value>)",
          200: "rgb(var(--color-accent-200) / <alpha-value>)",
          300: "rgb(var(--color-accent-300) / <alpha-value>)",
          400: "rgb(var(--color-accent-400) / <alpha-value>)",
          500: "rgb(var(--color-accent-500) / <alpha-value>)",
          600: "rgb(var(--color-accent-600) / <alpha-value>)",
          700: "rgb(var(--color-accent-700) / <alpha-value>)",
          800: "rgb(var(--color-accent-800) / <alpha-value>)",
          900: "rgb(var(--color-accent-900) / <alpha-value>)",
        },
        crisis: {
          50:  "rgb(var(--color-crisis-50)  / <alpha-value>)",
          100: "rgb(var(--color-crisis-100) / <alpha-value>)",
          200: "rgb(var(--color-crisis-200) / <alpha-value>)",
          300: "rgb(var(--color-crisis-300) / <alpha-value>)",
          400: "rgb(var(--color-crisis-400) / <alpha-value>)",
          500: "rgb(var(--color-crisis-500) / <alpha-value>)",
          600: "rgb(var(--color-crisis-600) / <alpha-value>)",
          700: "rgb(var(--color-crisis-700) / <alpha-value>)",
          800: "rgb(var(--color-crisis-800) / <alpha-value>)",
          900: "rgb(var(--color-crisis-900) / <alpha-value>)",
        },
        // Переопределяем neutral (Tailwind поставляет свою — игнорируем).
        // Это даёт нам контроль над bg-neutral-950 в темной теме через CSS-vars.
        neutral: {
          50:  "rgb(var(--color-neutral-50)  / <alpha-value>)",
          100: "rgb(var(--color-neutral-100) / <alpha-value>)",
          200: "rgb(var(--color-neutral-200) / <alpha-value>)",
          300: "rgb(var(--color-neutral-300) / <alpha-value>)",
          400: "rgb(var(--color-neutral-400) / <alpha-value>)",
          500: "rgb(var(--color-neutral-500) / <alpha-value>)",
          600: "rgb(var(--color-neutral-600) / <alpha-value>)",
          700: "rgb(var(--color-neutral-700) / <alpha-value>)",
          800: "rgb(var(--color-neutral-800) / <alpha-value>)",
          900: "rgb(var(--color-neutral-900) / <alpha-value>)",
          950: "rgb(var(--color-neutral-950) / <alpha-value>)",
        },

        // ====================================================================
        // SEMANTIC ALIASES — auto-switch между темами через .dark на <html>
        // ====================================================================
        "bg-base":      "rgb(var(--bg-base) / <alpha-value>)",
        "bg-elevated":  "rgb(var(--bg-elevated) / <alpha-value>)",
        "bg-sunken":    "rgb(var(--bg-sunken) / <alpha-value>)",
        "text-primary":   "rgb(var(--text-primary) / <alpha-value>)",
        "text-secondary": "rgb(var(--text-secondary) / <alpha-value>)",
        "text-muted":     "rgb(var(--text-muted) / <alpha-value>)",
        "text-inverted":  "rgb(var(--text-inverted) / <alpha-value>)",
        "border-subtle":  "rgb(var(--border-subtle) / <alpha-value>)",
        "border-default": "rgb(var(--border-default) / <alpha-value>)",

        // Glass surfaces — composite values, для будущего использования
        // (на этапе Phase 9 пока не везде применяем — оставляем точечный
        // переход).
        "glass-sidebar":        "var(--glass-sidebar-bg)",
        "glass-sidebar-border": "var(--glass-sidebar-border)",
        "glass-panel":          "var(--glass-panel-bg)",
        "glass-panel-border":   "var(--glass-panel-border)",
      },

      // ====================================================================
      // FONT FAMILY (как сейчас)
      // ====================================================================
      fontFamily: {
        sans: ["var(--font-golos)", "ui-sans-serif", "system-ui", "sans-serif"],
      },

      // ====================================================================
      // ANIMATION (как сейчас)
      // ====================================================================
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },

      // ====================================================================
      // BACKDROP-BLUR через переменные (для glass эффектов)
      // Значения соответствуют дефолтам Tailwind — сохраняем визуал.
      // ====================================================================
      backdropBlur: {
        sm:      "var(--glass-blur-sm)",
        DEFAULT: "var(--glass-blur)",
        md:      "var(--glass-blur-md)",
        lg:      "var(--glass-blur-lg)",
        xl:      "var(--glass-blur-xl)",
        "2xl":   "var(--glass-blur-2xl)",
      },
    },
  },
  plugins: [],
};

export default config;
```

**Что изменилось vs текущая версия:**
- Хексы → CSS-vars: `#FAF7F2` → `rgb(var(--color-warm-50) / <alpha-value>)`. Значение идентично, источник перенесён.
- Добавлены `zIndex` секция и semantic aliases — этого раньше не было.
- `backdropBlur` явно переопределён через CSS-vars (раньше использовались дефолтные Tailwind классы `backdrop-blur-md` etc — они продолжат работать, но через `--glass-blur-*`).
- Добавлены `glass-sidebar`/`glass-panel` цветовые алиасы для будущего использования. На этапе Phase 9 мы их **не применяем массово** в коде — текущие `useThemeTokens` классы продолжат работать. Алиасы — задел для следующих сессий, когда захочется переписать `useThemeTokens` с минимальным изменением call-sites.

## 6. Конкретные изменения в компонентах

В Phase 9 трогаем 9 файлов в `frontend/`. Все изменения — точечные замены `z-N` на семантические имена + одно дополнение в `globals.css` для focus-ring (см. часть 5 спеки).

### 6.1 `frontend/components/Layout/Background.tsx`

```diff
- className="fixed inset-0 z-0 overflow-hidden pointer-events-none"
+ className="fixed inset-0 z-decorative overflow-hidden pointer-events-none"
```

### 6.2 `frontend/components/Layout/AppShell.tsx`

```diff
- <div className="relative z-10 flex h-full w-full">
+ <div className="relative z-content flex h-full w-full">
```

### 6.3 `frontend/components/Layout/Sidebar.tsx`

Два изменения:
```diff
- "h-full flex-shrink-0 overflow-hidden relative z-30 transition-colors duration-700",
+ "h-full flex-shrink-0 overflow-hidden relative z-structure transition-colors duration-700",

# Context-menu (плавающий dropdown):
- "fixed z-50 py-1.5 w-48 rounded-xl shadow-2xl backdrop-blur-xl border",
+ "fixed z-overlay py-1.5 w-48 rounded-xl shadow-2xl backdrop-blur-xl border",
```

### 6.4 `frontend/components/Layout/RightDock.tsx`

```diff
- className="hidden md:flex absolute right-0 top-0 h-full w-[260px] lg:w-[280px] flex-col p-6 gap-4 items-end z-20 pointer-events-none"
+ className="hidden md:flex absolute right-0 top-0 h-full w-[260px] lg:w-[280px] flex-col p-6 gap-4 items-end z-floating-low pointer-events-none"
```

### 6.5 `frontend/components/Layout/FloatingButtons.tsx`

```diff
- className="absolute bottom-6 left-0 h-12 z-40 pointer-events-none"
+ className="absolute bottom-6 left-0 h-12 z-floating-high pointer-events-none"
```

### 6.6 `frontend/components/Chat/ChatContainer.tsx`

```diff
- <div className="absolute top-3 right-3 md:top-6 md:right-[120px] lg:right-[130px] z-30">
+ <div className="absolute top-3 right-3 md:top-6 md:right-[120px] lg:right-[130px] z-floating-high">
```

⚠ Важно: SOS поднимается с z-30 на z-floating-high (=40), что ВЫШЕ RightDock (z-floating-low =30). Это правильно — SOS-кнопка визуально находится в той же зоне что и аватар, и должна быть приоритетнее.

### 6.7 `frontend/components/Layout/TipCard.tsx`

Внутренний z-index `z-10` (для close-кнопки) — **локальный** в пределах самой карточки. Оставляем как есть, но с комментарием — это не глобальный z-stack:

```diff
  <Button
    size="icon"
    variant="ghost"
    onClick={handleDismiss}
    aria-label="Закрыть совет дня"
    className={cn(
-     "absolute right-2 top-2 size-6 rounded-full z-10",
+     // z-10 — локальный stacking context самой карточки, не глобальный
+     // (карточка создаёт свой контекст через position: relative + transform)
+     "absolute right-2 top-2 size-6 rounded-full z-10",
      t.tipCloseBtn,
    )}
  >
```

(Только комментарий, кода не трогаем — оригинальное поведение корректно благодаря локальному stacking context от `motion.div`/`Card`.)

### 6.8 `frontend/components/ui/Dialog.tsx`

Два изменения (overlay vs content):
```diff
# DialogOverlay:
- "fixed inset-0 z-50 bg-black/40 backdrop-blur-sm data-[state=open]:..."
+ "fixed inset-0 z-modal-backdrop bg-black/40 backdrop-blur-sm data-[state=open]:..."

# DialogContent:
- "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-2xl rounded-2xl",
+ "fixed left-[50%] top-[50%] z-modal grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-2xl rounded-2xl",
```

### 6.9 Toaster в `AppShell.tsx`

`sonner` Toaster по умолчанию использует свой высокий z-index, но мы хотим его контролировать. Sonner поддерживает CSS-vars через свой класс `[data-sonner-toaster]`. Добавляем в `globals.css`:

```css
[data-sonner-toaster] {
  z-index: var(--z-toast);
}
```

Это не трогает компонент `AppShell` — глобальный CSS правит z автоматически.

### 6.10 Сводка z-stack после рефакторинга

| Класс | Значение | Используется в |
|---|---|---|
| `z-decorative` | 0 | Background |
| `z-content` | 10 | AppShell wrapper |
| `z-structure` | 20 | Sidebar |
| `z-floating-low` | 30 | RightDock |
| `z-floating-high` | 40 | SOSButton (в ChatContainer), FloatingButtons |
| `z-overlay` | 50 | Sidebar context-menu |
| `z-modal-backdrop` | 60 | DialogOverlay |
| `z-modal` | 70 | DialogContent (CrisisPanel, RenameDialog) |
| `z-toast` | 80 | Sonner Toaster (через CSS) |

**Конфликты разрешены:**
- ✅ Sidebar (z-structure=20) и SOSButton (z-floating-high=40) — теперь в разных слоях. SOS всегда выше.
- ✅ Context-menu (z-overlay=50) и Dialog (z-modal=70, z-modal-backdrop=60) — Dialog всегда выше. Если оба открыты одновременно (теоретически), Dialog перекроет context-menu. Это правильно — модальный диалог имеет приоритет.

## 7. globals.css: финальная структура

После рефакторинга `frontend/app/globals.css` имеет такую структуру (порядок секций важен — переопределения сначала, утилиты потом):

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ===========================================================================
 * Дизайн-токены Кайроса (Сессия 21+).
 *
 * ЭТО ИСТОЧНИК ПРАВДЫ для палитры, glass-эффектов, z-layers и типографики.
 * Все остальные слои (tailwind.config.ts, useThemeTokens.ts) ссылаются СЮДА.
 *
 * Порядок секций:
 *   1. Z-layers (тема-независимые)
 *   2. Palette (тема-независимые: warm, accent, crisis, neutral)
 *   3. Semantic aliases (light defaults в :root)
 *   4. Glass tokens (light defaults в :root)
 *   5. Typography & sizing
 *   6. .dark — переопределения для тёмной темы
 *   7. Глобальные стили (body, scrollbar, motion-reduce, focus-rings)
 *
 * Спека: docs/superpowers/specs/2026-05-06-css-variables-foundation-design.md
 * =========================================================================== */

:root {
  /* ===== Z-LAYERS ===== */
  --z-decorative:     0;
  --z-content:       10;
  --z-structure:     20;
  --z-floating-low:  30;
  --z-floating-high: 40;
  --z-overlay:       50;
  --z-modal-backdrop: 60;
  --z-modal:         70;
  --z-toast:         80;

  /* ===== PALETTE (полные определения смотри в спеке §4.2) ===== */
  --color-warm-50: 250 247 242;
  /* ... все 30 значений (warm/accent/crisis × 10 уровней) + 11 neutral ... */

  /* ===== SEMANTIC ALIASES — light theme defaults ===== */
  --bg-base:        var(--color-warm-50);
  --bg-elevated:    var(--color-warm-100);
  --bg-sunken:      var(--color-warm-200);
  --text-primary:   var(--color-warm-900);
  --text-secondary: var(--color-warm-700);
  --text-muted:     var(--color-warm-600);
  --text-inverted:  var(--color-warm-50);
  --border-subtle:  var(--color-warm-200);
  --border-default: var(--color-warm-300);

  /* ===== GLASS TOKENS — light theme defaults ===== */
  --surface-rgb:    255 255 255;
  --surface-alpha-low:  0.6;
  --surface-alpha-high: 0.7;
  --surface-border-rgb: 255 255 255;
  --surface-border-alpha-low:  0.4;
  --surface-border-alpha-high: 0.6;

  --glass-blur-sm:   4px;
  --glass-blur:      8px;
  --glass-blur-md:  12px;
  --glass-blur-lg:  16px;
  --glass-blur-xl:  24px;
  --glass-blur-2xl: 40px;

  --glass-sidebar-bg:     rgb(var(--surface-rgb) / var(--surface-alpha-low));
  --glass-sidebar-border: rgb(var(--surface-border-rgb) / var(--surface-border-alpha-low));
  --glass-panel-bg:       rgb(var(--surface-rgb) / var(--surface-alpha-high));
  --glass-panel-border:   rgb(var(--surface-border-rgb) / var(--surface-border-alpha-high));

  --overlay-bg-light: rgba(255, 255, 255, 0.20);
  --overlay-bg-dark:  rgba(0, 0, 0, 0.50);

  /* ===== TYPOGRAPHY & SIZING ===== */
  --font-sans: var(--font-golos), ui-sans-serif, system-ui, sans-serif;
  --header-height: 56px;
  --footer-height: 40px;
  --sidebar-width: 240px;
  --right-dock-width-md: 260px;
  --right-dock-width-lg: 280px;
}

.dark {
  /* ===== SEMANTIC ALIASES — dark theme overrides ===== */
  --bg-base:        var(--color-neutral-950);
  --bg-elevated:    var(--color-neutral-900);
  --bg-sunken:      var(--color-neutral-800);
  --text-primary:   var(--color-neutral-50);
  --text-secondary: 255 255 255;
  --text-muted:     255 255 255;
  --text-inverted:  var(--color-neutral-900);
  --border-subtle:  var(--color-neutral-800);
  --border-default: var(--color-neutral-700);

  /* ===== GLASS TOKENS — dark theme overrides ===== */
  --surface-rgb:    0 0 0;
  --surface-alpha-low:  0.3;
  --surface-alpha-high: 0.4;
  --surface-border-rgb: 255 255 255;
  --surface-border-alpha-low:  0.1;
  --surface-border-alpha-high: 0.1;
}

/* ===========================================================================
 * Глобальные стили
 * =========================================================================== */

html, body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  @apply bg-warm-50 text-warm-900;
  min-height: 100vh;
}

.dark body {
  @apply bg-neutral-950 text-white;
}

/* Скроллбар (как сейчас) */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { @apply bg-warm-300 rounded-full; }
::-webkit-scrollbar-thumb:hover { @apply bg-warm-400; }
.dark ::-webkit-scrollbar-thumb { @apply bg-white/20; }
.dark ::-webkit-scrollbar-thumb:hover { @apply bg-white/30; }

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { @apply bg-warm-300/50 rounded-full; }
.dark .custom-scrollbar::-webkit-scrollbar-thumb { @apply bg-white/10 rounded-full; }

/* prefers-reduced-motion (как сейчас) */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* @supports backdrop-filter fallback (как сейчас) */
@supports not (backdrop-filter: blur(16px)) {
  .backdrop-blur-md, .backdrop-blur-xl, .backdrop-blur-2xl, .backdrop-blur-\[16px\] {
    background-color: rgba(255, 255, 255, 0.85);
  }
  .dark .backdrop-blur-md, .dark .backdrop-blur-xl, .dark .backdrop-blur-2xl, .dark .backdrop-blur-\[16px\] {
    background-color: rgba(0, 0, 0, 0.7);
  }
}

/* ===========================================================================
 * Sonner Toaster — глобальный z-index через CSS-vars
 * =========================================================================== */
[data-sonner-toaster] {
  z-index: var(--z-toast);
}

/* ===========================================================================
 * Focus-ring улучшения (Сессия 21).
 *
 * До этого фокус был виден только на стандартных кнопках (через Button
 * primitive). На stekле / тёмных пузырях / inputs на стеклянной обёртке
 * focus ring был почти невидим.
 *
 * Глобальный baseline для любых интерактивных элементов:
 * - Видимый offset-ring: 2px от элемента
 * - Цвет ring: текущий accent-400
 * - Цвет offset: bg-base (auto-switch между темами через CSS-var)
 *
 * Если компонент сам задаёт focus-visible:* — он переопределит этот baseline.
 * =========================================================================== */
:where(button, a, [role="button"], input, textarea, select, [tabindex]):focus-visible {
  outline: 2px solid rgb(var(--color-accent-400));
  outline-offset: 2px;
  /* В тёмной теме accent-400 (77 147 168) хорошо виден на neutral-950.
   * В светлой теме — на warm-50. Тестировано визуально. */
}
```

⚠ **Сохранены без изменений:** `body`-стили, scrollbar, `prefers-reduced-motion`, `@supports backdrop-filter`. Не ломаем то что работает.

⚠ **`@apply bg-warm-50` остаётся в body** — это работает потому что `bg-warm-50` после рефактора tailwind.config читает `var(--color-warm-50)`. Семантически идентично, источник изменился.

## 8. Tab-порядок и a11y

### 8.1 Текущая проблема

В Сессии 19 manual a11y test показал что Tab проходит:
1. sidebar items
2. кнопки внизу слева (settings, toggle)
3. SOS-кнопка
4. **«пропадает на 2 нажатия»** ← здесь и проблема
5. tel: ссылки в дисклеймере под input
6. theme toggle (правый верх)
7. avatar (правый верх)

### 8.2 Анализ

«Пропадает на 2 нажатия» = textarea и submit-кнопка в `InputArea`. Tab их фокусирует, но **focus ring не виден** на тёмном glass-фоне input'а.

Текущий CSS для input wrapper:
```
"bg-white/10 border border-white/20 focus-within:bg-white/15 focus-within:ring-2 focus-within:ring-white/30"
```

`ring-white/30` на `bg-white/10` (тёмная тема) — это ring **с alpha 0.3** на полупрозрачном фоне. Контраст недостаточен.

### 8.3 Решение

**Глобальный focus-ring baseline в `globals.css`** (см. часть 7) — `2px solid accent-400 + 2px offset`. Это переопределяет почти-невидимые `ring-white/30` на видимый контрастный outline для ВСЕХ интерактивных элементов.

Дополнительно проверяем что **DOM-порядок логичен**:

```
DOM:
1. Sidebar (новый разговор + список бесед)
2. FloatingButtons (settings, toggle) — слева внизу
3. main (поле ввода + кнопка отправки) — центр
4. RightDock (theme toggle, avatar, TipCard) — справа
```

Внутри `ChatContainer` SOSButton рендерится absolute поверх main, но в DOM-порядке он находится **первым** в children main. Tab по логике DOM:
1. sidebar
2. floating buttons
3. SOS-button
4. message bubbles (если есть, кнопки feedback на каждом)
5. textarea + submit
6. RightDock (theme + avatar)

**Это уже логичный порядок.** Проблема была только в видимости фокуса, не в самом DOM. Фикс глобальным focus-ring достаточен.

### 8.4 Проверка после рефакторинга

После Phase 9 manual a11y test должен показать:
- Каждое нажатие Tab → виден чёткий accent-ring вокруг элемента
- Никаких «пропаданий» — ring видим на любом фоне (стекло/сплошной/градиент)
- ESC закрывает модалки и context-menu (без изменений — Radix Dialog уже это умеет)
- `prefers-reduced-motion: reduce` отключает все motion-эффекты (работает с Сессии 19)

## 9. ADR (Architectural Decision Records)

### ADR-1: CSS Variables как единственный источник правды

**Контекст:** Tailwind config содержит хардкоженные хексы. Любая миграция с Tailwind требует переписывания десятков JSX с `className="bg-warm-50 dark:..."`.

**Решение:** Палитра, z-layers, glass-токены живут в `frontend/app/globals.css` как CSS variables. `tailwind.config.ts` становится тонкой обёрткой, читающей CSS-vars через `var(--name)`.

**Альтернатива (отклонена):** оставить хексы в Tailwind config. Слабость: lock-in. Любой инструмент кроме Tailwind не имеет доступа к этим значениям.

**Альтернатива (отклонена):** TypeScript-объект с константами. Слабость: CSS не может читать TS, придётся дублировать в CSS-vars в любом случае.

### ADR-2: Семантические z-layers вместо magic numbers

**Контекст:** В коде 10+ мест с magic numbers `z-0`, `z-30`, `z-50`. Конфликты (Sidebar и SOS оба на `z-30`).

**Решение:** 9 семантических уровней с шагом 10 (`z-decorative=0`, `z-content=10`, ..., `z-toast=80`). Между группами щель для будущих вставок без сдвига номеров.

**Альтернатива (отклонена):** 3 буквальных слоя как изначально предлагал пользователь (decorative / structural / interactive). Слабость: внутри «interactive» нужны под-уровни (overlay, modal, toast), иначе context-menu и Dialog конкурируют.

**Что мы сохраняем семантически:** 9 уровней группируются в 3 концептуальные группы пользователя — Decorative (0), Structural (10-20), Interactive (30-80).

### ADR-3: `useThemeTokens` API не меняется

**Контекст:** В существующем коде `useThemeTokens()` вызывается в 100+ местах. Изменение API ломает массу call-sites.

**Решение:** API хука остаётся идентичным. Внутри возвращаются те же Tailwind-классы (`bg-warm-50`, `text-warm-900` и т. д.). Под капотом эти Tailwind-классы теперь читают значения из CSS-vars. **0 изменений в местах вызова useThemeTokens.**

**Альтернатива (отклонена):** переписать `useThemeTokens` чтобы возвращал CSS-var-выражения напрямую. Слабость: огромный сплошной диф по всему коду, риск ввести регрессии.

**Будущее:** когда захочется мигрировать конкретный компонент с Tailwind на CSS Modules — можно сделать его `useThemeTokens` локальный вариант, или просто использовать CSS-vars напрямую через `style={{ background: 'var(--glass-panel-bg)' }}`. Алиасы в `tailwind.config.ts` (`glass-sidebar`, `glass-panel`) — задел именно для этого.

### ADR-4: `SIDEBAR_WIDTH` остаётся TS-константой

**Контекст:** Размер сайдбара 240px используется в `Sidebar.tsx` (motion `width: SIDEBAR_WIDTH`), `FloatingButtons.tsx` (импортирует ту же константу), CSS-var `--sidebar-width`.

**Решение:** TS-константа `SIDEBAR_WIDTH = 240` остаётся в `Sidebar.tsx` (для motion-анимаций где нужно числовое значение), CSS-var `--sidebar-width: 240px` — для CSS-доступа. Комментарий «keep in sync» в обоих местах.

**Альтернатива (отклонена):** читать CSS-var через `getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width')`. Слабость: runtime-зависимость, может не сработать при SSR, парсинг строки `"240px"`. Перебор для одного значения.

### ADR-5: Глобальный focus-ring через `:where()` selector

**Контекст:** Tailwind `focus-visible:ring-*` работает на конкретных компонентах, но требует ручной настройки везде. Многие интерактивные элементы (textarea в InputArea, links в Sidebar) не имеют видимого фокуса.

**Решение:** В `globals.css` глобальный baseline через `:where(button, a, [role="button"], input, textarea, select, [tabindex]):focus-visible { outline: ... }`. `:where()` имеет нулевую specificity, поэтому любой компонент может переопределить если нужно.

**Альтернатива (отклонена):** проходить по каждому компоненту и добавлять `focus-visible:ring-*` руками. Слабость: легко пропустить, не масштабируется на новые компоненты.

## 10. Что НЕ делается в этой спеке

Чёткие границы — что вне scope:

- ❌ **Миграция компонентов на CSS Modules** или другой стек. Делаем фундамент, дальше — точечно по мере необходимости.
- ❌ **Переписывание `useThemeTokens`**. API сохраняется. Внутренние классы остаются Tailwind. Когда созреет переход — отдельная сессия.
- ❌ **Полная замена `bg-warm-N`/`text-warm-N` на семантические `bg-bg-base`/`text-text-primary`**. Это бы упростило тёмную тему, но затронет ~50 файлов. Делаем только z-layers сейчас. Семантические алиасы добавляются в Tailwind config как **задел** — компоненты могут начать использовать их **точечно** в новых файлах, но массово не мигрируем.
- ❌ **Изменения в `useTheme`, `useSidebar`, `useSession`** — ничего там не трогаем.
- ❌ **Backend** — никаких бекенд-изменений.
- ❌ **Tailwind v4** — остаёмся на v3.4 (стабильность важнее).
- ❌ **Audit Tab-порядка через DOM-rearrangement** — DOM-порядок уже логичен (см. §8.3). Только focus-ring.

## 11. Тестирование

### 11.1 Автоматические проверки

**Type-check:** `npm run type-check` должен проходить чисто. Если Tailwind v3 не валидирует синтаксис `rgb(var(--name) / <alpha-value>)` — это уровень CSS, не TypeScript. Type-check всё равно ловит ошибки в JSX.

**Production build:** `npm run build` должен собрать все 5 страниц без ошибок. Особенно важно — Tailwind генерирует CSS из config'а: если `var(--name)` синтаксис неправильный, build упадёт с ошибкой PostCSS.

**Smoke check CSS-var разрешения** (Bash, после build):
```bash
cd frontend
npm run build
ls .next/static/css/*.css
# Открыть один из CSS файлов → искать строки `var(--color-warm-50)` и `var(--z-`
# Если они есть — Tailwind корректно сгенерировал классы со ссылками на CSS-vars
```

### 11.2 Manual visual regression

Это **критическая часть** Phase 9. CSS-vars подменяют цвета не визуально — если сделать ошибку (опечатка в RGB-тройке, неверный alias), компоненты всё равно отрисуются, но **не теми цветами**. Type-check этого не поймает.

**После каждой фазы — пользователь должен визуально проверить:**

| Сценарий | Что должно остаться идентичным |
|---|---|
| Светлая тема, `/chat` пустой | Тёплый бежевый фон, glassSidebar полупрозрачно-белый, EmptyState сверкает |
| Светлая тема, диалог | Пузыри: бот стеклянный, юзер accent-500 (синий) |
| Светлая тема, открыть SOS | CrisisPanel модалка: glass-белый фон + 4 номера |
| Тёмная тема, `/chat` пустой | Чёрный neutral-950 фон, glassSidebar полупрозрачно-чёрный |
| Тёмная тема, тоггл темы | Sun/Moon крутится, всё перекрашивается мгновенно |
| Сайдбар свернуть/развернуть | Анимация плавная, центральный контент расширяется |
| Settings → выбрать обои | Фон меняется, ничего не «прыгает» |

**Если хоть один из этих сценариев выглядит иначе чем сейчас (до Phase 9) — это регрессия.** Нужно искать опечатку в CSS-vars.

### 11.3 Z-stack regression

**Manual:**
1. Открыть SOSButton → видна **поверх** RightDock-аватара (если они визуально пересекаются).
2. Открыть CrisisPanel → видна поверх ВСЕГО, включая SOS-кнопку.
3. ПКМ на сессии в Sidebar → context-menu виден поверх Sidebar и main, но **под** Dialog'ом если тот открыт.
4. Toast (например, после удаления беседы) → виден поверх всего.

### 11.4 A11y regression

1. Tab по странице — каждый элемент получает **видимый accent-ring** на любом фоне (стекло, сплошной, градиент).
2. ESC закрывает CrisisPanel и RenameDialog (Radix unchanged).
3. `prefers-reduced-motion` (DevTools → Rendering) → анимации обрезаны до 0.01ms (как сейчас).

### 11.5 Cross-browser

После Phase 9 — Chrome (primary), Firefox (CSS-vars поддерживаются с 2017), Safari (поддерживаются с 2016). Все 3 справятся.

## 12. Риски и митигации

| Риск | Вероятность | Митигация |
|---|---|---|
| Опечатка в RGB-тройке (например `250 247 224` вместо `242`) → цвет немного отличается | Высокая | Сверка с текущими хексами при ревью. После имплементации — manual visual regression |
| Tailwind v3 не парсит `rgb(var(--name) / <alpha-value>)` синтаксис | Низкая (стандартная фича Tailwind 3.3+) | Build-test после каждого изменения tailwind.config |
| `:where(...):focus-visible` слишком широкий, ломает custom focus styles в Button primitive | Средняя | `:where()` имеет нулевую specificity → любой `focus-visible:` в компоненте переопределит |
| Sonner Toaster не respect глобальный `[data-sonner-toaster] { z-index }` | Низкая (стандартный Sonner API) | Проверить визуально что toast виден поверх Dialog'а |
| Дублирование `SIDEBAR_WIDTH` (TS const + CSS-var) разойдётся в будущем | Низкая | Комментарий-маркер `// SYNC: must match --sidebar-width in globals.css` в обоих местах |
| Существующее `useThemeTokens.ts` использует `backdrop-blur-md`/`backdrop-blur-2xl` — после переопределения в config меняются их значения | Высокая | См. **точная мапа** ниже — сохраняем дефолтные значения Tailwind через CSS-vars |

### 12.1 Точная мапа `backdropBlur` (важно — сохранение визуала)

Tailwind v3 дефолты:
- `backdrop-blur-sm` = 4px
- `backdrop-blur` (default) = 8px
- `backdrop-blur-md` = 12px
- `backdrop-blur-lg` = 16px
- `backdrop-blur-xl` = 24px
- `backdrop-blur-2xl` = 40px

В существующем коде используются: `backdrop-blur-md` (TipCard hover, RightDock items), `backdrop-blur-xl` (msgAi), `backdrop-blur-2xl` (glass panel, inputWrapper), и кастомный `backdrop-blur-[16px]` (glass sidebar).

**Решение:** имена `--glass-blur-*` соответствуют дефолтам Tailwind:

```css
:root {
  --glass-blur-sm:  4px;
  --glass-blur:     8px;
  --glass-blur-md: 12px;
  --glass-blur-lg: 16px;
  --glass-blur-xl: 24px;
  --glass-blur-2xl: 40px;
}
```

И в `tailwind.config.ts`:

```ts
backdropBlur: {
  sm:      "var(--glass-blur-sm)",
  DEFAULT: "var(--glass-blur)",
  md:      "var(--glass-blur-md)",
  lg:      "var(--glass-blur-lg)",
  xl:      "var(--glass-blur-xl)",
  "2xl":   "var(--glass-blur-2xl)",
},
```

**Это сохраняет 100% визуальную совместимость** — все `backdrop-blur-*` классы в коде продолжают работать как сейчас, просто значения теперь читаются из CSS-vars.

⚠ Кастомные классы `backdrop-blur-[16px]` (используется в `useThemeTokens.glassSidebar` для тёмной темы) — это **inline arbitrary values** Tailwind, они **не зависят** от `tailwind.config.ts`. Эти классы продолжат работать идентично текущему поведению. Можно оставить как есть, или **в будущей сессии** заменить на семантический `backdrop-blur-lg` (16px = `--glass-blur-lg`) — это эквивалент.

## 13. Готовность к реализации

После одобрения этого дизайна — переход в writing-plans skill для пошагового плана.

**Phases (план будет детализирован):**

1. **Phase 1 — globals.css фундамент**: добавить блок CSS-vars в `globals.css`. На этом этапе Tailwind ещё не использует их (старый config). Build остаётся работать как раньше.

2. **Phase 2 — tailwind.config.ts мост**: переписать config на использование CSS-vars через `var(--name)`. Build verify — все цвета должны рендериться идентично.

3. **Phase 3 — z-layers миграция**: заменить magic numbers `z-0/10/20/30/40/50` на семантические имена в 9 файлах.

4. **Phase 4 — focus-ring и Sonner**: добавить глобальный `:where(...):focus-visible` и `[data-sonner-toaster] { z-index }` в globals.css.

5. **Phase 5 — manual visual regression**: пользователь проверяет все темы / страницы / scenarios. Если что-то отличается — фикс.

6. **Phase 6 — документация**: CLAUDE.md (Сессия 21) + PROGRESS.md.

---

*Этот документ — спека закладывания фундамента CSS Variables. Оригинальный план Phase 9 (3-слойная архитектура) расширен после feedback пользователя про tailwind-lock-in.*

*История правок:*

- *Сессия 21 (2026-05-06): создание после ручного тестирования Сессий 19 + 20. Зафиксировано 5 ADR. Объём расширен с z-layers-only до полного CSS-vars фундамента (палитра, glass, semantic aliases, typography).*


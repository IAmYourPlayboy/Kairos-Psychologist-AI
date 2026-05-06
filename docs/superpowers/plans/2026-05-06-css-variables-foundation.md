# CSS Variables Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести палитру, glass-эффекты, z-layers и типографику в CSS custom properties (`:root` + `.dark`). Tailwind config становится тонкой обёрткой через `var(--name)`. Сохраняем 100% визуальную совместимость и не меняем API хуков.

**Architecture:** 6 phases по нарастающей. Phase 1 закладывает CSS-vars в globals.css (Tailwind пока их игнорирует). Phase 2 — мост в tailwind.config через `var(--name)`. Phase 3 — миграция magic z-numbers на семантические имена в 9 файлах. Phase 4 — глобальный focus-ring + Sonner z-toast. Phase 5 — manual visual regression от пользователя. Phase 6 — документация.

**Tech Stack:** CSS custom properties, Tailwind v3.4, Next.js 16, Sonner.

**Spec:** `docs/superpowers/specs/2026-05-06-css-variables-foundation-design.md`

**Working directory:** `D:/Kairos/.claude/worktrees/phase-9-layers/`. Все пути в плане относительны этой директории, если не указано иначе.

**Behavioral guidelines (from `skills/behavioral-guidelines.md`):**
1. Think Before Coding — каждое изменение имеет явный «зачем»
2. Simplicity First — никаких новых пакетов, никаких новых файлов в `lib/`, никаких неспрошенных абстракций
3. Surgical Changes — трогаем ровно те строки которые надо. Не трогаем «соседний код для красоты»
4. Goal-Driven — критерий успеха каждого таска явный. Никаких «вроде работает»

---

## Файлы, которые меняются

| Файл | Действие | Что |
|---|---|---|
| `frontend/app/globals.css` | REWRITE | Добавить блок CSS-vars (z-layers, palette, semantic, glass, typography) + добавить focus-ring + добавить `[data-sonner-toaster]` z-index |
| `frontend/tailwind.config.ts` | REWRITE | Палитру и backdropBlur перевести через `var(--name)`, добавить `zIndex` секцию, добавить semantic aliases (`bg-base`, `text-primary`, etc.) |
| `frontend/components/Layout/Background.tsx` | MODIFY | `z-0` → `z-decorative` (1 строка) |
| `frontend/components/Layout/AppShell.tsx` | MODIFY | `z-10` → `z-content` (1 строка) |
| `frontend/components/Layout/Sidebar.tsx` | MODIFY | `z-30` → `z-structure`, `z-50` (context-menu) → `z-overlay` (2 строки) |
| `frontend/components/Layout/RightDock.tsx` | MODIFY | `z-20` → `z-floating-low` (1 строка) |
| `frontend/components/Layout/FloatingButtons.tsx` | MODIFY | `z-40` → `z-floating-high` (1 строка) |
| `frontend/components/Chat/ChatContainer.tsx` | MODIFY | SOSButton wrapper `z-30` → `z-floating-high` (1 строка) |
| `frontend/components/Layout/TipCard.tsx` | MODIFY | Только комментарий — z-10 локальный (без изменения значения) |
| `frontend/components/ui/Dialog.tsx` | MODIFY | `z-50` (overlay) → `z-modal-backdrop`, `z-50` (content) → `z-modal` (2 строки) |
| `CLAUDE.md` | MODIFY | Добавить запись Сессии 21 в «История ключевых решений» + версия 3.6 → 3.7 |
| `PROGRESS.md` | MODIFY | Добавить запись 21.0 + версия 2.7 → 2.8 |

**Не трогаем:** `useThemeTokens.ts`, `useTheme.ts`, `useSidebar.ts`, `useSession.ts`, любой компонент в `Chat/`, `Crisis/`, `Dossier/`, `Feedback/`, `ui/Button.tsx`, `ui/Card.tsx`, `ui/Avatar.tsx`. Бэкенд — никаких изменений.

---

## Phase 1: CSS-vars фундамент в globals.css

Цель: добавить CSS-vars блок в `globals.css`. На этом этапе Tailwind ещё не использует их (мы тронем `tailwind.config.ts` только в Phase 2). Build остаётся работать как раньше — это **аддитивное изменение**, оно ничего не ломает.

Критерий успеха фазы: `npm run build` проходит, в DevTools на странице `/chat` видны CSS-vars (например, `:root --color-warm-50: 250 247 242`).

### Task 1.1: Добавить блок CSS-vars в globals.css

**Files:**
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Прочитать текущий globals.css**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
cat frontend/app/globals.css
```

Зафиксировать в голове: текущий файл содержит `@tailwind base/components/utilities` + `:root` с двумя переменными (`--header-height: 56px`, `--footer-height: 40px`) + body styles + scrollbar + prefers-reduced-motion + @supports backdrop-filter fallback. Всё это **сохраняем**, **добавляем** CSS-vars блок и `[data-sonner-toaster]` правило.

- [ ] **Step 2: Полностью переписать globals.css**

Заменить ВЕСЬ файл `frontend/app/globals.css` на:

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
 * Спека: docs/superpowers/specs/2026-05-06-css-variables-foundation-design.md
 * =========================================================================== */

:root {
  /* ===== Z-LAYERS (тема-независимые) =====
   * Семантические уровни наложения. 9 уровней в 3 концептуальных группах:
   *   Decorative   — фон, декорации (pointer-events: none)
   *   Structural   — контент и навигационные панели
   *   Interactive  — плавающие controls, overlays, modals, toasts
   * Между группами щель в 10 единиц для будущих вставок без сдвига номеров.
   */
  --z-decorative:     0;
  --z-content:       10;
  --z-structure:     20;
  --z-floating-low:  30;
  --z-floating-high: 40;
  --z-overlay:       50;
  --z-modal-backdrop: 60;
  --z-modal:         70;
  --z-toast:         80;

  /* ===== PALETTE (тема-независимая) =====
   * RGB-тройки (без rgb()/без запятых) для Tailwind alpha-channel синтаксиса.
   * Использование: rgb(var(--color-warm-50) / 0.8) — warm-50 с alpha 0.8.
   */

  /* warm — тёплая нейтральная база */
  --color-warm-50:  250 247 242;
  --color-warm-100: 244 239 231;
  --color-warm-200: 232 223 208;
  --color-warm-300: 212 197 174;
  --color-warm-400: 184 164 136;
  --color-warm-500: 157 136 107;
  --color-warm-600: 126 109  84;
  --color-warm-700:  95  82  64;
  --color-warm-800:  63  54  43;
  --color-warm-900:  31  27  22;

  /* accent — спокойный синий */
  --color-accent-50:  238 244 248;
  --color-accent-100: 214 227 237;
  --color-accent-200: 174 206 219;
  --color-accent-300: 122 177 194;
  --color-accent-400:  77 147 168;
  --color-accent-500:  53 117 136;
  --color-accent-600:  40  89 106;
  --color-accent-700:  29  65  76;
  --color-accent-800:  20  43  51;
  --color-accent-900:  11  23  25;

  /* crisis — приглушённый красный */
  --color-crisis-50:  250 240 238;
  --color-crisis-100: 244 217 212;
  --color-crisis-200: 232 176 166;
  --color-crisis-300: 217 132 122;
  --color-crisis-400: 199  87  79;
  --color-crisis-500: 165  58  54;
  --color-crisis-600: 127  42  41;
  --color-crisis-700:  92  30  29;
  --color-crisis-800:  62  20  20;
  --color-crisis-900:  31  10  10;

  /* neutral — нейтральная шкала (для тёмной темы) */
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

  /* ===== SEMANTIC ALIASES (light theme defaults) =====
   * Эти переменные имеют РАЗНЫЕ значения в .dark.
   */
  --bg-base:        var(--color-warm-50);
  --bg-elevated:    var(--color-warm-100);
  --bg-sunken:      var(--color-warm-200);
  --text-primary:   var(--color-warm-900);
  --text-secondary: var(--color-warm-700);
  --text-muted:     var(--color-warm-600);
  --text-inverted:  var(--color-warm-50);
  --border-subtle:  var(--color-warm-200);
  --border-default: var(--color-warm-300);

  /* ===== GLASS TOKENS (light theme defaults) ===== */
  --surface-rgb:    255 255 255;
  --surface-alpha-low:  0.6;
  --surface-alpha-high: 0.7;
  --surface-border-rgb: 255 255 255;
  --surface-border-alpha-low:  0.4;
  --surface-border-alpha-high: 0.6;

  /* Blur values согласованы с Tailwind дефолтами — сохраняет визуал. */
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
  /* ===== SEMANTIC ALIASES (dark theme overrides) ===== */
  --bg-base:        var(--color-neutral-950);
  --bg-elevated:    var(--color-neutral-900);
  --bg-sunken:      var(--color-neutral-800);
  --text-primary:   var(--color-neutral-50);
  --text-secondary: 255 255 255;
  --text-muted:     255 255 255;
  --text-inverted:  var(--color-neutral-900);
  --border-subtle:  var(--color-neutral-800);
  --border-default: var(--color-neutral-700);

  /* ===== GLASS TOKENS (dark theme overrides) ===== */
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

html,
body {
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

/* Скроллбар — ненавязчивый, темовый */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  @apply bg-warm-300 rounded-full;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-warm-400;
}

.dark ::-webkit-scrollbar-thumb {
  @apply bg-white/20;
}

.dark ::-webkit-scrollbar-thumb:hover {
  @apply bg-white/30;
}

/* Custom scrollbar для отдельных скролл-областей в сайдбаре */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  @apply bg-warm-300/50 rounded-full;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  @apply bg-white/10 rounded-full;
}

/* prefers-reduced-motion: вырубаем все анимации длиннее 200ms */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Fallback для старых браузеров без backdrop-filter */
@supports not (backdrop-filter: blur(16px)) {
  .backdrop-blur-md,
  .backdrop-blur-xl,
  .backdrop-blur-2xl,
  .backdrop-blur-\[16px\] {
    background-color: rgba(255, 255, 255, 0.85);
  }
  .dark .backdrop-blur-md,
  .dark .backdrop-blur-xl,
  .dark .backdrop-blur-2xl,
  .dark .backdrop-blur-\[16px\] {
    background-color: rgba(0, 0, 0, 0.7);
  }
}
```

⚠ Замечу что сюда **ещё не добавлены** focus-ring (`:where(...):focus-visible`) и `[data-sonner-toaster]` блок. Они добавляются в Phase 4 — отдельной фазой, чтобы Phase 1 был чисто аддитивным фундаментом.

- [ ] **Step 3: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: `tsc --noEmit` без ошибок (это CSS, TypeScript его не видит — должно проходить).

- [ ] **Step 4: Production build smoke**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
rm -rf .next
npm run build 2>&1 | tail -15
```

Expected: успешный build, 5 страниц статика (`/`, `/_not-found`, `/chat`, `/profile`, `/settings`). Если build упал на CSS parsing — это значит синтаксис в `globals.css` ошибочен. Прочитать ошибку, найти место, починить.

- [ ] **Step 5: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/app/globals.css
git commit -m "feat(frontend): add CSS variables foundation in globals.css (Session 21 Phase 1)"
```

---

**Phase 1 Checkpoint:** После этой фазы:
- `globals.css` содержит CSS-vars для z-layers, палитры, semantic aliases, glass, typography
- Tailwind ещё их **не использует** — это будет Phase 2
- Существующие классы `bg-warm-50`, `bg-neutral-950` работают через Tailwind как раньше (значения хексов в config'е)
- Build чистый, type-check чистый

Фактически **визуально ничего не изменилось**. Это правильно — Phase 1 закладывает фундамент.

---

## Phase 2: tailwind.config.ts мост на CSS-vars

Цель: переписать `tailwind.config.ts` так, чтобы цвета, z-layers, backdropBlur читались из CSS-vars через `var(--name)`. После этой фазы `bg-warm-50` физически тот же цвет, но источник — CSS-var.

Критерий успеха фазы: `npm run build` проходит, в `.next/static/css/*.css` встречаются строки с `var(--color-warm-N)` или `var(--z-N)`.

### Task 2.1: Переписать tailwind.config.ts

**Files:**
- Modify: `frontend/tailwind.config.ts`

- [ ] **Step 1: Полностью заменить tailwind.config.ts**

Заменить ВЕСЬ файл `frontend/tailwind.config.ts` на:

```ts
import type { Config } from "tailwindcss";

/**
 * Tailwind конфигурация Кайроса (Сессия 21+).
 *
 * Сам файл — ТОНКАЯ ОБЁРТКА: значения читаются из CSS variables в
 * frontend/app/globals.css. Если хочешь поменять цвет — иди в globals.css.
 *
 * Зачем: дизайн-токены не привязаны к Tailwind. В будущем компонент можно
 * будет мигрировать на CSS Modules / Panda CSS / любой другой стек —
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
      // Z-LAYERS — семантические имена слоёв вместо magic numbers.
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
      // COLORS — все палитры из CSS-vars + поддержка alpha-channel.
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
        // Переопределяем Tailwind-дефолтную neutral палитру через CSS-vars,
        // чтобы и она была переопределяема для будущего dark-mode тюнинга.
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
        // SEMANTIC ALIASES — auto-switch между темами через .dark на <html>.
        // На этапе Сессии 21 ИСПОЛЬЗУЕМ ТОЧЕЧНО (или вообще не используем);
        // существующий код продолжит писать bg-warm-50 / text-warm-900.
        // Это задел для будущих компонентов / частичной миграции.
        // ====================================================================
        "bg-base":        "rgb(var(--bg-base) / <alpha-value>)",
        "bg-elevated":    "rgb(var(--bg-elevated) / <alpha-value>)",
        "bg-sunken":      "rgb(var(--bg-sunken) / <alpha-value>)",
        "text-primary":   "rgb(var(--text-primary) / <alpha-value>)",
        "text-secondary": "rgb(var(--text-secondary) / <alpha-value>)",
        "text-muted":     "rgb(var(--text-muted) / <alpha-value>)",
        "text-inverted":  "rgb(var(--text-inverted) / <alpha-value>)",
        "border-subtle":  "rgb(var(--border-subtle) / <alpha-value>)",
        "border-default": "rgb(var(--border-default) / <alpha-value>)",
      },

      // ====================================================================
      // FONT FAMILY (без изменений vs предыдущей версии)
      // ====================================================================
      fontFamily: {
        sans: ["var(--font-golos)", "ui-sans-serif", "system-ui", "sans-serif"],
      },

      // ====================================================================
      // ANIMATION (без изменений vs предыдущей версии)
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
      // BACKDROP-BLUR через CSS-vars.
      // Значения СОВПАДАЮТ с дефолтами Tailwind (4/8/12/16/24/40px) —
      // существующие классы backdrop-blur-md/-xl/-2xl продолжают работать
      // идентично текущему визуалу.
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

- [ ] **Step 2: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 3: Production build**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
rm -rf .next
npm run build 2>&1 | tail -15
```

Expected: успешный build, 5 страниц статика. Если упало с PostCSS-ошибкой про `var(...)` синтаксис — это значит Tailwind не понял `rgb(var(--name) / <alpha-value>)`. Маловероятно (стандартная фича Tailwind 3.3+), но если так — прочитать ошибку, понять что именно сломалось.

- [ ] **Step 4: Smoke check сгенерированного CSS**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
ls .next/static/css/*.css
# Найти первый CSS-файл и грепнуть
grep -c "var(--color-warm" .next/static/css/*.css | head -1
grep -c "var(--z-" .next/static/css/*.css | head -1
```

Expected: оба grep'а показывают НЕ-нулевое количество строк. Это значит Tailwind корректно сгенерировал CSS со ссылками на наши CSS-vars.

- [ ] **Step 5: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/tailwind.config.ts
git commit -m "feat(frontend): tailwind.config bridges CSS variables (Session 21 Phase 2)"
```

---

**Phase 2 Checkpoint:** После этой фазы:
- Tailwind генерирует CSS-классы (`bg-warm-50`, `z-30`, `backdrop-blur-md`) — но значения теперь читаются из CSS-vars
- Визуально страница выглядит **идентично** — те же цвета, те же blur, те же z-индексы
- Если открыть DevTools → проверить computed style на любом элементе → видны `rgb(var(--color-warm-50) / 1)` вместо `#FAF7F2`
- Build чистый

Если **визуально что-то выглядит иначе** после Phase 2 — это значит RGB-тройка не совпадает с хексом. Проверить: открыть `globals.css`, для проблемного цвета сверить RGB-тройку с хексом из старого `tailwind.config.ts.bak` (через `git diff main..HEAD -- frontend/tailwind.config.ts`).

---

## Phase 3: Миграция z-classes в 9 компонентах

Цель: заменить magic `z-0/10/20/30/40/50` на семантические имена. После этой фазы каждый z-класс самодокументируем.

Критерий успеха фазы: все z-классы в `frontend/components/` и `frontend/app/` используют семантические имена. `git grep "z-30\|z-40\|z-50" frontend/components frontend/app` возвращает только TipCard локальный z-10 (это допустимо, см. §6.7 спеки).

### Task 3.1: Background.tsx — z-decorative

**Files:**
- Modify: `frontend/components/Layout/Background.tsx`

- [ ] **Step 1: Заменить `z-0` на `z-decorative`**

Найти в `frontend/components/Layout/Background.tsx` строку:
```tsx
className="fixed inset-0 z-0 overflow-hidden pointer-events-none"
```

Заменить на:
```tsx
className="fixed inset-0 z-decorative overflow-hidden pointer-events-none"
```

- [ ] **Step 2: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 3: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Layout/Background.tsx
git commit -m "refactor(frontend): Background uses z-decorative semantic class"
```

### Task 3.2: AppShell.tsx — z-content

**Files:**
- Modify: `frontend/components/Layout/AppShell.tsx`

- [ ] **Step 1: Заменить `z-10` на `z-content`**

Найти в `frontend/components/Layout/AppShell.tsx` строку:
```tsx
<div className="relative z-10 flex h-full w-full">
```

Заменить на:
```tsx
<div className="relative z-content flex h-full w-full">
```

- [ ] **Step 2: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 3: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Layout/AppShell.tsx
git commit -m "refactor(frontend): AppShell wrapper uses z-content semantic class"
```

### Task 3.3: Sidebar.tsx — z-structure + z-overlay

**Files:**
- Modify: `frontend/components/Layout/Sidebar.tsx`

- [ ] **Step 1: Прочитать текущее состояние**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -n "z-30\|z-50" frontend/components/Layout/Sidebar.tsx
```

Expected: 2 совпадения — `z-30` на motion.aside и `z-50` на context-menu div.

- [ ] **Step 2: Заменить `z-30` на `z-structure` (motion.aside)**

Найти строку:
```tsx
"h-full flex-shrink-0 overflow-hidden relative z-30 transition-colors duration-700",
```

Заменить на:
```tsx
"h-full flex-shrink-0 overflow-hidden relative z-structure transition-colors duration-700",
```

- [ ] **Step 3: Заменить `z-50` на `z-overlay` (context-menu)**

Найти строку:
```tsx
"fixed z-50 py-1.5 w-48 rounded-xl shadow-2xl backdrop-blur-xl border",
```

Заменить на:
```tsx
"fixed z-overlay py-1.5 w-48 rounded-xl shadow-2xl backdrop-blur-xl border",
```

- [ ] **Step 4: Verify оба замены сделаны**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -n "z-30\|z-50" frontend/components/Layout/Sidebar.tsx
```

Expected: пустой вывод. Если что-то осталось — повторить замену.

- [ ] **Step 5: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 6: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Layout/Sidebar.tsx
git commit -m "refactor(frontend): Sidebar uses z-structure and z-overlay semantic classes"
```

### Task 3.4: RightDock.tsx — z-floating-low

**Files:**
- Modify: `frontend/components/Layout/RightDock.tsx`

- [ ] **Step 1: Заменить `z-20` на `z-floating-low`**

Найти строку:
```tsx
className="hidden md:flex absolute right-0 top-0 h-full w-[260px] lg:w-[280px] flex-col p-6 gap-4 items-end z-20 pointer-events-none"
```

Заменить на:
```tsx
className="hidden md:flex absolute right-0 top-0 h-full w-[260px] lg:w-[280px] flex-col p-6 gap-4 items-end z-floating-low pointer-events-none"
```

- [ ] **Step 2: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 3: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Layout/RightDock.tsx
git commit -m "refactor(frontend): RightDock uses z-floating-low semantic class"
```

### Task 3.5: FloatingButtons.tsx — z-floating-high

**Files:**
- Modify: `frontend/components/Layout/FloatingButtons.tsx`

- [ ] **Step 1: Заменить `z-40` на `z-floating-high`**

Найти строку:
```tsx
className="absolute bottom-6 left-0 h-12 z-40 pointer-events-none"
```

Заменить на:
```tsx
className="absolute bottom-6 left-0 h-12 z-floating-high pointer-events-none"
```

- [ ] **Step 2: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 3: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Layout/FloatingButtons.tsx
git commit -m "refactor(frontend): FloatingButtons use z-floating-high semantic class"
```

### Task 3.6: ChatContainer.tsx — SOSButton z-floating-high

**Files:**
- Modify: `frontend/components/Chat/ChatContainer.tsx`

- [ ] **Step 1: Заменить `z-30` на `z-floating-high`**

Найти строку:
```tsx
<div className="absolute top-3 right-3 md:top-6 md:right-[120px] lg:right-[130px] z-30">
```

Заменить на:
```tsx
<div className="absolute top-3 right-3 md:top-6 md:right-[120px] lg:right-[130px] z-floating-high">
```

⚠ Важно: SOS поднимается на `z-floating-high` (=40), что **выше** `z-floating-low` RightDock (=30). Это правильно — SOS-кнопка визуально находится в той же зоне что и аватар RightDock, и должна быть приоритетнее.

- [ ] **Step 2: Verify нет других z-30 в ChatContainer**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -n "z-30\|z-50" frontend/components/Chat/ChatContainer.tsx
```

Expected: пустой вывод (другие z-индексы в ChatContainer отсутствуют).

- [ ] **Step 3: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 4: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Chat/ChatContainer.tsx
git commit -m "refactor(frontend): SOSButton wrapper uses z-floating-high (above RightDock)"
```

### Task 3.7: TipCard.tsx — добавить комментарий к локальному z-10

**Files:**
- Modify: `frontend/components/Layout/TipCard.tsx`

⚠ В TipCard z-10 — это **локальный stacking context** для close-кнопки внутри карточки, не глобальный. Значение оставляем, но добавляем комментарий чтобы будущий разработчик не подумал что это конфликтует с `z-content` (=10) на AppShell wrapper.

- [ ] **Step 1: Найти close-кнопку в TipCard**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -n "z-10" frontend/components/Layout/TipCard.tsx
```

Expected: одно совпадение — внутри `<Button>` для close.

- [ ] **Step 2: Добавить комментарий перед классом**

Найти блок (около строк 70-78):
```tsx
            <Button
              size="icon"
              variant="ghost"
              onClick={handleDismiss}
              aria-label="Закрыть совет дня"
              className={cn(
                "absolute right-2 top-2 size-6 rounded-full z-10",
                t.tipCloseBtn,
              )}
            >
```

Заменить на:
```tsx
            <Button
              size="icon"
              variant="ghost"
              onClick={handleDismiss}
              aria-label="Закрыть совет дня"
              className={cn(
                // z-10 локальный (внутри stacking context самой карточки —
                // motion.div + Card создают свой контекст). НЕ конфликтует
                // с глобальным z-content (тоже =10) на AppShell wrapper.
                "absolute right-2 top-2 size-6 rounded-full z-10",
                t.tipCloseBtn,
              )}
            >
```

- [ ] **Step 3: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 4: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/Layout/TipCard.tsx
git commit -m "docs(frontend): clarify TipCard close-button z-10 is a local stacking context"
```

### Task 3.8: Dialog.tsx — z-modal-backdrop + z-modal

**Files:**
- Modify: `frontend/components/ui/Dialog.tsx`

- [ ] **Step 1: Заменить `z-50` в DialogOverlay на `z-modal-backdrop`**

Найти строку (около строки 21):
```tsx
"fixed inset-0 z-50 bg-black/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
```

Заменить на:
```tsx
"fixed inset-0 z-modal-backdrop bg-black/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
```

- [ ] **Step 2: Заменить `z-50` в DialogContent на `z-modal`**

Найти строку (около строки 38):
```tsx
"fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-2xl rounded-2xl",
```

Заменить на:
```tsx
"fixed left-[50%] top-[50%] z-modal grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-2xl rounded-2xl",
```

- [ ] **Step 3: Verify оба заменены**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -n "z-50" frontend/components/ui/Dialog.tsx
```

Expected: пустой вывод.

- [ ] **Step 4: Type-check**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run type-check
```

Expected: 0 ошибок.

- [ ] **Step 5: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/components/ui/Dialog.tsx
git commit -m "refactor(frontend): Dialog uses z-modal-backdrop + z-modal semantic classes"
```

### Task 3.9: Verify полная замена z-classes

- [ ] **Step 1: Глобальный grep для проверки**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -rn "\bz-0\b\|\bz-10\b\|\bz-20\b\|\bz-30\b\|\bz-40\b\|\bz-50\b" frontend/components frontend/app | grep -v "\.next" | grep -v "node_modules"
```

Expected: только одно совпадение — `frontend/components/Layout/TipCard.tsx` с `z-10` (локальный stacking context, по комментарию). Всё остальное должно быть на семантических именах.

Если grep вернёт больше — значит какой-то компонент пропустили. Найти и сделать соответствующую замену.

- [ ] **Step 2: Production build (final проверка после всех замен)**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
rm -rf .next
npm run build 2>&1 | tail -15
```

Expected: 5 страниц статика, build чистый.

- [ ] **Step 3: Smoke check сгенерированного CSS**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
grep -E "\.z-(decorative|content|structure|floating-low|floating-high|overlay|modal-backdrop|modal|toast)" .next/static/css/*.css | head -10
```

Expected: видны строки вида `.z-decorative{z-index:var(--z-decorative)}`. Это значит Tailwind корректно сгенерировал классы для всех 9 z-layers (хотя `z-toast` пока никем не используется — он добавится в Phase 4 через Sonner).

- [ ] **Step 4: Empty checkpoint commit для отметки**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git commit --allow-empty -m "test(frontend): Phase 3 z-layer migration verified — no magic numbers remain"
```

---

**Phase 3 Checkpoint:** После этой фазы:
- 8 z-классов заменены на семантические имена в 8 файлах (Sidebar заменил 2)
- 1 z-10 в TipCard оставлен с комментарием (локальный stacking context)
- Glob grep чистый — нет magic numbers в frontend/components и frontend/app
- Z-stack теперь самодокументируем

Визуально страница может слегка отличаться:
- SOS-кнопка теперь точно поверх RightDock-аватара (раньше был конфликт z-30 vs z-30 — поведение зависело от DOM-порядка, теперь явно SOS выше)
- Context-menu теперь точно НИЖЕ Dialog'а если оба открыты (раньше z-50 = z-50 — конфликт)

Это **правильные** изменения — устранение бывших скрытых конфликтов. Если в результате что-то выглядит странно — скорее всего раньше работало по случайности.

---

## Phase 4: Focus-ring и Sonner Toaster

Цель: добавить глобальный focus-ring через `:where(...):focus-visible` (исправляет проблему «Tab пропадает на 2 нажатия» в Сессии 19) и направить Sonner Toaster на `--z-toast`.

Критерий успеха фазы: Tab по странице вызывает видимый accent-ring на каждом интерактивном элементе. Toast виден поверх Dialog'а.

### Task 4.1: Добавить focus-ring и Sonner z-toast в globals.css

**Files:**
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Прочитать текущий globals.css**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
cat frontend/app/globals.css | tail -30
```

Найти в конце файла блок `@supports not (backdrop-filter: blur(16px))`. После него добавим два новых блока.

- [ ] **Step 2: Добавить два блока в конец globals.css**

В конец файла `frontend/app/globals.css` (после закрывающей `}` блока `@supports not (backdrop-filter: blur(16px))`) добавить:

```css

/* ===========================================================================
 * Sonner Toaster — глобальный z-index через CSS-vars.
 * Sonner создаёт элемент с data-sonner-toaster атрибутом; правим его z
 * напрямую, чтобы тосты всегда были выше модалок.
 * =========================================================================== */
[data-sonner-toaster] {
  z-index: var(--z-toast);
}

/* ===========================================================================
 * Focus-ring улучшения (Сессия 21).
 *
 * До этого фокус был виден только на компонентах с явным focus-visible:ring-*
 * (Button, FloatingButtons). На стеклянных пузырях / inputs на стеклянной
 * обёртке focus ring был почти невидим — это создавало проблему «Tab
 * пропадает на 2 нажатия» в Сессии 19 manual a11y test.
 *
 * Глобальный baseline для любых интерактивных элементов:
 * - Видимый offset-ring: 2px от элемента
 * - Цвет ring: текущий accent-400
 *
 * :where() имеет нулевую specificity — любой компонент может переопределить
 * через свой focus-visible:* без конфликтов.
 * =========================================================================== */
:where(button, a, [role="button"], input, textarea, select, [tabindex]):focus-visible {
  outline: 2px solid rgb(var(--color-accent-400));
  outline-offset: 2px;
}
```

- [ ] **Step 3: Production build**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
rm -rf .next
npm run build 2>&1 | tail -10
```

Expected: 5 страниц статика, build чистый.

- [ ] **Step 4: Smoke check — focus-ring правило существует в CSS**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
grep -c "data-sonner-toaster" .next/static/css/*.css
grep -c ":focus-visible" .next/static/css/*.css
```

Expected: оба grep'а возвращают НЕ-нулевое количество. Это значит правила попали в финальный CSS.

- [ ] **Step 5: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add frontend/app/globals.css
git commit -m "feat(frontend): add global focus-ring and Sonner toast z-index (Session 21 Phase 4)"
```

---

**Phase 4 Checkpoint:** После этой фазы:
- Все интерактивные элементы имеют видимый accent-400 outline на фокусе
- Toast виден поверх Dialog'а (через `[data-sonner-toaster] { z-index: var(--z-toast) }`)
- Build чистый
- Phase 5 (manual regression) проверит что фокус действительно виден визуально

---

## Phase 5: Manual visual regression checklist

Цель: пользователь визуально проверяет что после Phase 1-4 ничего не изменилось (кроме намеренных улучшений: видимый focus-ring, разрешённые z-конфликты).

⚠ **Phase 5 — это исключительно manual проверка.** Code-side задач нет, только пользовательские шаги. Если что-то не работает — фикс в worktree, потом re-test.

### Task 5.1: Запустить full stack

- [ ] **Step 1: Pre-flight — backend работает (или запустить)**

Если backend остановлен с прошлой сессии — запустить из `D:/Kairos/backend/` (через venv):

```powershell
cd D:\Kairos\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001
```

(или CMD/Git Bash эквиваленты — см. инструкции из Сессии 20).

⚠ Backend этим Phase 9 не трогается, так что любая stable версия (текущий main или предыдущая) подойдёт.

- [ ] **Step 2: Запустить frontend dev из worktree**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers/frontend
npm run dev
```

Открыть `http://localhost:3000` (или :3001 если 3000 занят).

- [ ] **Step 3: Очистить localStorage перед тестом**

В браузере DevTools → Application → Local Storage → правый клик на `localhost` → Clear → F5.

Это нужно чтобы отключить персистированную тему/обои/чаты, и стартовать с чистого состояния.

### Task 5.2: Visual regression — light theme

⚠ Все checkbox'ы — это **manual checks** для пользователя. Если хоть один не пройден — это регрессия, нужно отчитаться и фиксить.

- [ ] **Light тема: пустой `/chat`**
  - Тёплый бежевый фон (`warm-50`)
  - Glass-сайдбар полупрозрачно-белый
  - EmptyState ✨ парит, текст «Здесь можно говорить как есть»

- [ ] **Light тема: написать «привет»**
  - Пузырь юзера справа — `accent-500` синий
  - Пузырь бота слева — стеклянный
  - SOS-кнопка вверху справа — нейтральная (LifeBuoy)

- [ ] **Light тема: нажать SOS**
  - Открывается CrisisPanel модалка
  - Glass-белая подложка с 4 номерами
  - Esc/клик вне/× закрывают

- [ ] **Light тема: переключить на dark theme** (Sun/Moon в правом верхнем)
  - Иконка крутится
  - Фон становится `neutral-950` (почти чёрный)
  - Glass-сайдбар становится полупрозрачно-чёрным
  - Все пузыри / кнопки / text перерисовались
  - **Никаких артефактов** (мигание, неполный rerender)

### Task 5.3: Visual regression — dark theme

- [ ] **Dark тема: написать «всё бессмысленно, нет выхода» (high crisis)**
  - SOS становится красным, медленная пульсация (`animate-pulse-slow`)
  - CrisisInlineCard под ответом — красноватая на тёмном фоне, читаема

- [ ] **Dark тема: написать «хочу умереть» (immediate crisis)**
  - CrisisPanel автооткрывается (если LLM сработал нормально — Сессия 20 это улучшила)
  - SOS яркий красный, быстрая пульсация
  - Модалка читаема в тёмной теме

- [ ] **Dark тема: переключить на light theme**
  - Снова всё перерисовывается мгновенно
  - Тоггл иконка крутится в обратном направлении

### Task 5.4: Z-stack regression

- [ ] **SOS поверх RightDock-аватара**
  - На широком viewport (≥1024px) SOS-кнопка и аватар RightDock находятся в правой верхней зоне
  - SOS должен быть **визуально поверх** аватара (раньше был конфликт z-30 vs z-30 — теперь SOS=floating-high=40, RightDock=floating-low=30)

- [ ] **Sidebar context-menu НЕ конфликтует с Dialog**
  - ПКМ на сессии в Sidebar → context-menu открывается
  - Если какой-то Dialog (CrisisPanel или RenameDialog) открыт одновременно — Dialog поверх context-menu (z-modal=70 > z-overlay=50)

- [ ] **Toast поверх всего**
  - Удалить беседу через context-menu → toast «Беседа удалена»
  - Toast виден даже если в этот момент открыт Dialog (z-toast=80 > z-modal=70)

### Task 5.5: A11y regression — focus visibility

- [ ] **Tab по странице (с очищенным localStorage / pустой `/chat`)**
  - F5, потом много раз Tab
  - **Каждый интерактивный элемент** должен показывать видимый `accent-400` outline (2px solid + 2px offset)
  - Никаких «пропаданий» на 2 нажатия как в Сессии 19

- [ ] **Tab по `/profile`**
  - Открыть `/profile` (через клик по аватару RightDock)
  - Tab проходит по всем интерактивным элементам с видимым outline

- [ ] **Tab по `/settings`**
  - Открыть `/settings` (через FloatingButtons settings)
  - Tab проходит по theme buttons и wallpaper picker'у с видимым outline

### Task 5.6: Если всё ОК — empty checkpoint commit

- [ ] **Step 1: Empty commit для отметки**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git commit --allow-empty -m "test(frontend): Phase 5 manual visual regression passed"
```

Если что-то **не прошло** — не коммитить. Описать пользователю проблему, разобраться, починить в worktree, повторить regression.

---

**Phase 5 Checkpoint:** После этой фазы:
- Визуально страница идентична состоянию до Phase 9 (кроме намеренных улучшений)
- Focus-ring виден на всех интерактивных элементах
- Z-stack конфликты разрешены
- Готовность к merge в main

---

## Phase 6: Документация

Цель: записать решение в CLAUDE.md (Сессия 21) + PROGRESS.md.

### Task 6.1: Обновить CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Найти Сессию 20 entry**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
grep -n "Сессия 20" CLAUDE.md | head -3
```

Expected: запись Сессии 20 (PerceptionReport robustness) в секции «История ключевых решений».

- [ ] **Step 2: Добавить Сессию 21 entry после Сессии 20**

В CLAUDE.md, в секции «История ключевых решений», ПОСЛЕ полной записи Сессии 20 (последний буллет про спеку и план), ПЕРЕД маркером `---` или следующей секцией, добавить:

```markdown
**Сессия 21** (Май 2026): 🎨 **CSS Variables Foundation для Кайроса.** Архитектурный фундамент для будущей миграции с Tailwind. Ключевые решения:

- **CSS variables как единственный источник правды.** Палитра (warm/accent/crisis/neutral × 10-11 уровней), z-layers (9 семантических), glass-tokens, typography — всё в `frontend/app/globals.css` как `:root` + `.dark` блоки.
- **Tailwind config — тонкая обёртка.** Цвета и z через `var(--name)` синтаксис: `rgb(var(--color-warm-50) / <alpha-value>)`. Если завтра захочется мигрировать компонент на CSS Modules / Panda / styled — он будет читать те же CSS-vars, никаких ломающих изменений.
- **9 семантических z-layers вместо magic numbers.** `z-decorative` (0) / `z-content` (10) / `z-structure` (20) / `z-floating-low` (30) / `z-floating-high` (40) / `z-overlay` (50) / `z-modal-backdrop` (60) / `z-modal` (70) / `z-toast` (80). Группировка в 3 концептуальные группы: Decorative / Structural / Interactive. Между группами щель в 10 единиц.
- **Разрешены 2 ранее скрытых z-конфликта.** Sidebar и SOSButton были оба на `z-30` (теперь z-structure=20 vs z-floating-high=40). Sidebar context-menu и Dialog были оба на `z-50` (теперь z-overlay=50 vs z-modal=70).
- **Глобальный focus-ring через `:where(...):focus-visible`** в `globals.css`. Решает проблему «Tab пропадает на 2 нажатия» из manual a11y test Сессии 19. `:where()` имеет нулевую specificity — любой компонент может переопределить.
- **Sonner Toaster z-index через `[data-sonner-toaster]` правило в globals.css.** Toasts всегда выше Dialog (z-toast=80 > z-modal=70).
- **`useThemeTokens` API сохранён 1-в-1.** 0 изменений в 100+ местах вызова. API не меняется — внутренние значения теперь читаются из CSS-vars прозрачно.
- **Backdrop-blur значения** (`--glass-blur-*`) точно совпадают с Tailwind дефолтами (4/8/12/16/24/40px) — 100% визуальная совместимость.

**5 ADR зафиксированы в спеке:**
- ADR-1: CSS Variables как единственный источник правды
- ADR-2: 9 семантических z-layers вместо magic numbers
- ADR-3: useThemeTokens API не меняется
- ADR-4: SIDEBAR_WIDTH остаётся TS-константой (компромисс между TS-доступом и CSS-доступом)
- ADR-5: глобальный focus-ring через `:where()` selector

**Не трогали:** `useThemeTokens`, `useTheme`/`useSidebar`/`useSession`, любые компоненты Chat/Crisis/Dossier/Feedback (кроме z-class в ChatContainer SOSButton wrapper), backend, бизнес-логика.

Дизайн: `docs/superpowers/specs/2026-05-06-css-variables-foundation-design.md`
План: `docs/superpowers/plans/2026-05-06-css-variables-foundation.md`
```

- [ ] **Step 3: Обновить шапку CLAUDE.md**

В CLAUDE.md, найти строку:
```
> **Версия**: 3.6 | **Дата**: Май 2026 (Сессия 20)
```

Заменить на:
```
> **Версия**: 3.7 | **Дата**: Май 2026 (Сессия 21)
```

- [ ] **Step 4: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add CLAUDE.md
git commit -m "docs(claude-md): record Session 21 (CSS Variables Foundation)"
```

### Task 6.2: Обновить PROGRESS.md

**Files:**
- Modify: `PROGRESS.md`

- [ ] **Step 1: Найти запись 20.0 в «История правок»**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
tail -10 PROGRESS.md
```

Expected: строки `*Версия: 2.7*` и `*20.0: ...*`.

- [ ] **Step 2: Добавить 21.0 entry ПОСЛЕ 20.0**

Найти строку:
```
- *20.0: 🛡️ **Устойчивость PerceptionReport.** ...
```

ПОСЛЕ неё (на следующей строке) добавить:

```
- *21.0: 🎨 **CSS Variables Foundation.** Палитра (warm/accent/crisis/neutral × 10-11 уровней), z-layers (9 семантических: decorative/content/structure/floating-low/floating-high/overlay/modal-backdrop/modal/toast), glass-tokens, typography — всё переехало в `frontend/app/globals.css` как `:root` + `.dark`. `tailwind.config.ts` стал тонкой обёрткой через `var(--name)`. Разрешены 2 z-конфликта (Sidebar vs SOSButton, context-menu vs Dialog). Глобальный focus-ring через `:where(...):focus-visible`. Sonner Toaster через `[data-sonner-toaster]` правило. `useThemeTokens` API сохранён 1-в-1. 5 ADR в спеке. Не трогали бекенд / бизнес-логику. Дизайн: `docs/superpowers/specs/2026-05-06-css-variables-foundation-design.md`. План: `docs/superpowers/plans/2026-05-06-css-variables-foundation.md`.*
```

- [ ] **Step 3: Обновить версию и дату внизу файла**

Найти строки:
```
*Последнее обновление: Сессия 20, Май 2026*
```
Заменить на:
```
*Последнее обновление: Сессия 21, Май 2026*
```

И строку:
```
*Версия: 2.7*
```
Заменить на:
```
*Версия: 2.8*
```

- [ ] **Step 4: Commit**

```bash
cd D:/Kairos/.claude/worktrees/phase-9-layers
git add PROGRESS.md
git commit -m "docs(progress): record Session 21 (CSS Variables Foundation)"
```

---

**Phase 6 Checkpoint:** После этой фазы:
- CLAUDE.md и PROGRESS.md содержат полную запись Сессии 21
- Версии обновлены: CLAUDE.md 3.6 → 3.7, PROGRESS.md 2.7 → 2.8
- Готовность к merge в main

---

## Готово!

После всех 6 phases:
- ✅ CSS Variables в `globals.css` — единый источник правды для палитры, z-layers, glass, typography
- ✅ `tailwind.config.ts` читает CSS-vars через `var(--name)` — тонкая обёртка
- ✅ 9 файлов используют семантические z-classes
- ✅ Глобальный focus-ring через `:where()` в `globals.css`
- ✅ Sonner Toaster на `--z-toast`
- ✅ Существующие классы (`bg-warm-50`, `backdrop-blur-md` etc) работают идентично — 100% визуальная совместимость
- ✅ `useThemeTokens` API без изменений — 0 правок в call-sites
- ✅ CLAUDE.md и PROGRESS.md задокументировали Сессию 21

**Manual smoke** (после merge в main):
- Очистить localStorage, проверить light/dark темы, кризисные сценарии — должны работать как до Phase 9
- Tab по странице — выявить визуальные регрессии focus-ring
- В DevTools проверить computed styles — цвета должны быть `rgb(R G B / A)`, не `#hex` (это знак что CSS-vars работают)

**Если на любом шаге что-то не сработает** — стоп, разобраться, не двигаться дальше. Это рефакторинг с visual side-effect — каждая мелочь имеет значение.

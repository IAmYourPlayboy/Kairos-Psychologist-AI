# Frontend Figma Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести визуальные сильные стороны черновика Figma Make (`D:/Figma Files/`) в текущий фронтенд (`d:/Kairos/frontend/`) — glassmorphism, dark/light тема, сайдбар сессий, плавающие элементы, motion-анимации — без потери кризисной логики, perception layer и совместимости с ФЗ-152.

**Architecture:** Поверх существующего Next.js App Router фронтенда строится новый `AppShell` (фон + сайдбар + правый dock). Все темовые стили проходят через единый хук `useThemeTokens`. Кризисные компоненты, `useChat`, `DossierView`, `Feedback` сохраняют API — меняется только обёртка и Tailwind-классы. Сайдбар работает через локальный Dexie до появления бэкенд-эндпоинтов `GET/PATCH/DELETE /api/sessions`.

**Tech Stack:** Next.js 16 (App Router), React 18.3, TypeScript strict, Tailwind v3, Dexie 4, motion (Framer Motion v12), lucide-react, sonner, Radix UI (Avatar+Dialog+Slot), clsx + tailwind-merge, CVA, Golos Text via next/font.

**Spec:** `docs/superpowers/specs/2026-05-06-frontend-figma-redesign-design.md`

**Working directory:** `d:/Kairos/frontend/`. Все пути в этом плане относительны этой директории, если не указано иначе.

**Запрещённые паттерны:** ни в одном компоненте этот план не вводит клиентскую имитацию ответов бота. Все ответы приходят через `useChat → POST /api/chat`. Никаких шаблонных строк типа «Я понимаю ваши чувства», «Всё будет хорошо», «Держись» — это `forbidden_phrases.py` и проверяется кодом-ревью.

**Реализационные отличия от спеки (сознательные):**

- Wallpaper persist — через `localStorage`, не Dexie (спек упоминает Dexie). Причина: MVP, синхронный доступ, не нужно ждать промис при первом рендере. Если позже понадобится синхронизация между устройствами — переедем в Dexie без UI-изменений.
- `SessionMeta` тип объявлен в `hooks/useSessions.ts` (а не в `lib/types.ts` как просит спек). Причина: тип используется только этим хуком, нет смысла его экспортировать из общего модуля.
- В `lib/api.ts` НЕ добавляются `getSessions/deleteSession/renameSession` — пока бэкенд-эндпоинты `/api/sessions` не появились. Когда появятся (отдельный блок PROGRESS.md, не входит в этот план) — добавятся точечно, `useSessions.ts` переключит источник без изменений UI.

---

## Phase 1: Зависимости, темовая база, AppShell skeleton

Цель: установить новые npm-пакеты, добавить dark mode через класс на `<html>`, создать хуки `useTheme` + `useThemeTokens` + `useSidebar`, утилиту `cn()`, и пустой `AppShell` который оборачивает `{children}` без логики (только структура слоёв). После этой фазы приложение всё ещё работает как раньше (старый `ChatContainer` рендерится в `AppShell` без визуальных изменений).

### Task 1.1: Установить npm-зависимости

**Files:**
- Modify: `d:/Kairos/frontend/package.json`

- [ ] **Step 1: Запустить установку (одной командой)**

```bash
cd d:/Kairos/frontend && npm install motion@^12 lucide-react@^0.487 sonner@^2 clsx@^2 tailwind-merge@^3 class-variance-authority@^0.7 @radix-ui/react-avatar@^1 @radix-ui/react-dialog@^1 @radix-ui/react-slot@^1
```

Expected: пакеты добавлены в `dependencies`, `node_modules` обновлён. Если `legacy-peer-deps` уже в `.npmrc` (проверь — было в коммите `eb074ec`), команда пройдёт чисто.

- [ ] **Step 2: Проверить что Next dev server стартует**

```bash
cd d:/Kairos/frontend && npm run dev
```

Expected: сервер слушает на `http://localhost:3000`, страница `/chat` открывается без ошибок. Прерви процесс через Ctrl+C.

- [ ] **Step 3: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: `tsc --noEmit` без ошибок.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/package.json frontend/package-lock.json && git commit -m "chore(frontend): add motion, lucide, sonner, radix, cva, clsx, tw-merge"
```

---

### Task 1.2: Включить dark mode в Tailwind

**Files:**
- Modify: `d:/Kairos/frontend/tailwind.config.ts`

- [ ] **Step 1: Добавить `darkMode: "class"`**

Открой `tailwind.config.ts` и добавь поле `darkMode: "class"` в корне config-объекта (рядом с `content`):

```ts
const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    // ... остаётся как есть
  },
  plugins: [],
};
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок (это просто строковое поле).

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/tailwind.config.ts && git commit -m "feat(frontend): enable Tailwind dark mode via class strategy"
```

---

### Task 1.3: Утилита `cn()` (clsx + tailwind-merge)

**Files:**
- Create: `d:/Kairos/frontend/lib/cn.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/lib/cn.ts
/**
 * Утилита для объединения Tailwind-классов:
 * - clsx собирает условные классы
 * - tailwind-merge корректно резолвит конфликты (например, p-4 + p-2 → p-2)
 *
 * Пример:
 *   cn("px-4 py-2", isActive && "bg-blue-500", "px-6")
 *   // → "py-2 bg-blue-500 px-6"
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/lib/cn.ts && git commit -m "feat(frontend): add cn() utility (clsx + tailwind-merge)"
```

---

### Task 1.4: Хук `useTheme` (auto-detect + persist)

**Files:**
- Create: `d:/Kairos/frontend/hooks/useTheme.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/hooks/useTheme.ts
"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "kairos-theme";

export type Theme = "dark" | "light";

/**
 * Определить начальную тему: сохранённая в localStorage > авто по часу.
 * Авто: 21:00–06:59 локального времени → dark, иначе → light.
 *
 * Срабатывает только в браузере. На сервере возвращает "light"
 * (anti-flash скрипт в <head> применит правильный класс до гидратации).
 */
function detectInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    // localStorage недоступен (приватный режим) — fallback на авто
  }
  const hour = new Date().getHours();
  return hour >= 21 || hour < 7 ? "dark" : "light";
}

/**
 * Хук темы: возвращает theme + isDark + toggle.
 * При смене темы обновляет класс `.dark` на <html> и сохраняет в localStorage.
 */
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const initial = detectInitialTheme();
    setThemeState(initial);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // тихо игнорируем
    }
  }, [theme, mounted]);

  const toggle = useCallback(() => {
    setThemeState((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
  }, []);

  return { theme, isDark: theme === "dark", toggle, setTheme, mounted };
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/hooks/useTheme.ts && git commit -m "feat(frontend): add useTheme hook with auto-detect and localStorage persist"
```

---

### Task 1.5: Хук `useThemeTokens` (порт из Figma)

**Files:**
- Create: `d:/Kairos/frontend/lib/theme-tokens.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/lib/theme-tokens.ts
"use client";

import { useTheme } from "@/hooks/useTheme";

/**
 * Темовые токены: единая точка маппинга isDark → набор Tailwind классов.
 *
 * Порт из Figma Make AppContext.tsx::useThemeTokens с адаптацией под
 * нашу палитру (warm/accent/crisis) для светлой темы.
 *
 * Используй так:
 *   const t = useThemeTokens();
 *   <div className={cn("rounded-xl p-4", t.glassPanel)}>...</div>
 */
export function useThemeTokens() {
  const { isDark } = useTheme();
  return {
    overlay: isDark ? "bg-black/50" : "bg-white/20",

    glassSidebar: isDark
      ? "bg-black/30 border-white/10 backdrop-blur-[16px]"
      : "bg-white/60 border-white/40 backdrop-blur-md shadow-sm",
    glassPanel: isDark
      ? "bg-black/40 border-white/10 backdrop-blur-2xl"
      : "bg-white/70 border-white/60 backdrop-blur-2xl shadow-xl",

    textMain: isDark ? "text-white" : "text-warm-900",
    textMuted: isDark ? "text-white/60" : "text-warm-700",

    btnHover: isDark
      ? "hover:bg-white/20 hover:text-white"
      : "hover:bg-warm-900/5 hover:text-warm-900",
    divider: isDark ? "bg-white/10" : "bg-warm-900/10",

    btnPrimary: isDark
      ? "bg-white text-black hover:bg-white/80"
      : "bg-accent-700 text-white hover:bg-accent-800 shadow-md",

    msgUser: isDark
      ? "bg-white text-black shadow-[0_4px_24px_-4px_rgba(255,255,255,0.2)]"
      : "bg-accent-500 text-white shadow-md",
    msgAi: isDark
      ? "bg-white/10 backdrop-blur-xl border border-white/10 text-white shadow-md"
      : "bg-white/85 backdrop-blur-xl border border-warm-200 text-warm-900 shadow-sm",

    inputWrapper: isDark
      ? "bg-white/10 border border-white/20 focus-within:bg-white/15 focus-within:ring-2 focus-within:ring-white/30"
      : "bg-white border border-warm-200 focus-within:ring-2 focus-within:ring-accent-400/30 shadow-xl",

    floatingBtn: isDark
      ? "bg-white/10 hover:bg-white/20 text-white shadow-[0_0_15px_rgba(0,0,0,0.5)] border border-white/20"
      : "bg-white/95 hover:bg-warm-50 text-warm-900 shadow-md border border-warm-200",

    tipCard: isDark
      ? "bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-400/30 text-amber-50"
      : "bg-gradient-to-br from-amber-50 to-orange-100/80 border border-amber-300/60 text-amber-900",
    tipIcon: isDark
      ? "text-amber-300 bg-amber-500/20 border border-amber-400/20"
      : "text-amber-600 bg-amber-200/60 border border-amber-300",
    tipCloseBtn: isDark
      ? "text-amber-200/50 hover:text-amber-200 hover:bg-amber-500/30"
      : "text-amber-600 hover:text-amber-800 hover:bg-amber-300/50",
  };
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/lib/theme-tokens.ts && git commit -m "feat(frontend): add useThemeTokens hook (port from Figma Make)"
```

---

### Task 1.6: Хук `useSidebar` (open/closed + persist)

**Files:**
- Create: `d:/Kairos/frontend/hooks/useSidebar.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/hooks/useSidebar.ts
"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "kairos.sidebar-open";

/**
 * Хук для управления состоянием левого сайдбара (открыт/свёрнут).
 *
 * Persist в localStorage. На мобильных по умолчанию закрыт
 * (определяется по window.matchMedia при первом маунте).
 */
export function useSidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let initial: boolean;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "true" || saved === "false") {
        initial = saved === "true";
      } else {
        // Первый визит: на мобильных закрыт, на десктопе открыт.
        initial = window.matchMedia("(min-width: 768px)").matches;
      }
    } catch {
      initial = window.matchMedia("(min-width: 768px)").matches;
    }
    setIsOpen(initial);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    try {
      localStorage.setItem(STORAGE_KEY, String(isOpen));
    } catch {
      // тихо
    }
  }, [isOpen, mounted]);

  const toggle = useCallback(() => setIsOpen((v) => !v), []);
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  return { isOpen, toggle, open, close, mounted };
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/hooks/useSidebar.ts && git commit -m "feat(frontend): add useSidebar hook with persist and mobile auto-collapse"
```

---

### Task 1.7: Anti-flash `ThemeScript`

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/ThemeScript.tsx`

- [ ] **Step 1: Создать директорию и файл**

```tsx
// frontend/components/Layout/ThemeScript.tsx
/**
 * Inline-скрипт, который выставляет класс `.dark` на <html> ДО гидратации React.
 * Это предотвращает «вспышку светлой темы» при первой загрузке.
 *
 * Логика идентична detectInitialTheme() в hooks/useTheme.ts —
 * keep them in sync.
 *
 * Подключается в <head> в app/layout.tsx первым ребёнком.
 */
export function ThemeScript() {
  const code = `
(function() {
  try {
    var saved = null;
    try { saved = localStorage.getItem('kairos-theme'); } catch (e) {}
    var theme = (saved === 'dark' || saved === 'light') ? saved : null;
    if (!theme) {
      var h = new Date().getHours();
      theme = (h >= 21 || h < 7) ? 'dark' : 'light';
    }
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
})();
  `.trim();
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/ThemeScript.tsx && git commit -m "feat(frontend): add ThemeScript for anti-flash dark mode"
```

---

### Task 1.8: Каркас `AppShell` (без логики)

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/AppShell.tsx`

- [ ] **Step 1: Создать файл с минимальной структурой**

```tsx
// frontend/components/Layout/AppShell.tsx
"use client";

import { Toaster } from "sonner";

import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";

/**
 * Корневой shell приложения.
 *
 * MVP-фаза: только контейнер с фоном и Toaster.
 * В Phase 2 добавим Background, в Phase 3 — Sidebar и RightDock.
 *
 * children — рендерит контент конкретной страницы (chat / profile / settings).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark, mounted } = useTheme();

  return (
    <div
      className={cn(
        "relative flex h-[100dvh] w-[100dvw] overflow-hidden font-sans transition-colors duration-700",
        // До маунта рендерим без класса (anti-flash скрипт уже выставил .dark на <html>).
        // После маунта класс контролируется хуком (через .dark на <html>).
        mounted && isDark ? "bg-neutral-950" : "bg-warm-50",
      )}
    >
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />

      {/* Слой контента */}
      <main className="relative z-10 flex h-full w-full">
        {children}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/AppShell.tsx && git commit -m "feat(frontend): add AppShell skeleton with Toaster and theme-aware background"
```

---

### Task 1.9: Подключить `ThemeScript` и `AppShell` в `app/layout.tsx`

**Files:**
- Modify: `d:/Kairos/frontend/app/layout.tsx`

- [ ] **Step 1: Заменить содержимое layout.tsx**

```tsx
// frontend/app/layout.tsx
import type { Metadata, Viewport } from "next";
import { Golos_Text } from "next/font/google";

import { AppShell } from "@/components/Layout/AppShell";
import { ThemeScript } from "@/components/Layout/ThemeScript";

import "./globals.css";

const golos = Golos_Text({
  subsets: ["cyrillic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-golos",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Кайрос — первая психологическая помощь",
  description:
    "Сервис первой психологической помощи. Не заменяет психолога — заполняет пустоту, где психолога нет рядом.",
  keywords: [
    "психологическая помощь",
    "кризис",
    "поддержка",
    "первая помощь",
    "AI",
  ],
  authors: [{ name: "Kairos Team" }],
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={golos.variable} suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className="font-sans antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Запустить dev-сервер и проверить визуально**

```bash
cd d:/Kairos/frontend && npm run dev
```

Открой `http://localhost:3000/chat` в браузере. Expected:
- Никаких ошибок в консоли браузера или терминала
- Старый чат-интерфейс рендерится поверх AppShell-обёртки
- Если ты в браузере посмотришь `<html>` после полуночи, на нём должен быть класс `dark`. Днём — без класса.
- Прерви dev-сервер (Ctrl+C)

- [ ] **Step 3: Type-check + lint**

```bash
cd d:/Kairos/frontend && npm run type-check && npm run lint
```

Expected: без ошибок.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/app/layout.tsx && git commit -m "feat(frontend): wire ThemeScript and AppShell into root layout"
```

---

### Task 1.10: Расширить `globals.css` — dark body, motion-reduce, scrollbar

**Files:**
- Modify: `d:/Kairos/frontend/app/globals.css`

- [ ] **Step 1: Заменить содержимое**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ===========================================================================
 * Глобальные стили Кайроса
 * =========================================================================== */

:root {
  /* Высота шапки/футера для отступов */
  --header-height: 56px;
  --footer-height: 40px;
}

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

- [ ] **Step 2: Запустить dev-сервер и проверить визуально**

```bash
cd d:/Kairos/frontend && npm run dev
```

Открой страницу. Expected:
- Скроллбар тонкий и нейтральный
- В DevTools переключи `prefers-reduced-motion: reduce` (Rendering tab) → анимации замораживаются
- Прерви dev-сервер.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/app/globals.css && git commit -m "feat(frontend): extend globals.css with dark body, custom scrollbar, motion-reduce, blur fallback"
```

---

**Phase 1 Checkpoint:** После этой фазы у нас есть:
- Все нужные npm-пакеты установлены
- Dark mode включён в Tailwind, переключается через `useTheme`
- `useThemeTokens` — единая точка маппинга isDark → Tailwind классы
- `useSidebar` — open/closed с persist
- `cn()` — утилита для классов
- `AppShell` — пустой каркас, оборачивает дочерние страницы
- `ThemeScript` — anti-flash при загрузке
- Старый `ChatContainer` всё ещё работает (рендерится через AppShell без визуальных изменений)
- `prefers-reduced-motion` уважается глобально

Перед началом Phase 2 — **остановись и отмотай в браузере** что текущее состояние работает, чтобы не нести баги дальше.


---

## Phase 2: Background, RightDock, ThemeToggle, базовые UI-примитивы

Цель: сделать визуально видимые изменения — фоновое изображение с темовым overlay, переключатель темы в правом верхнем углу, плавающую кнопку настроек слева внизу. Также создаём `Button`/`Card`/`Avatar`/`Dialog` shadcn-style примитивы (нужны в следующих фазах).

### Task 2.1: Скачать локальные wallpapers

**Files:**
- Create: `d:/Kairos/frontend/public/wallpapers/forest.jpg`
- Create: `d:/Kairos/frontend/public/wallpapers/mountains.jpg`
- Create: `d:/Kairos/frontend/public/wallpapers/ocean.jpg`
- Create: `d:/Kairos/frontend/public/wallpapers/stars.jpg`

- [ ] **Step 1: Создать директорию**

```bash
mkdir -p d:/Kairos/frontend/public/wallpapers
```

- [ ] **Step 2: Скачать 4 фото с Unsplash (один раз, локально, чтобы потом не ходить на CDN)**

```bash
cd d:/Kairos/frontend/public/wallpapers
curl -L -o forest.jpg "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=1920&q=80&fm=jpg"
curl -L -o mountains.jpg "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920&q=80&fm=jpg"
curl -L -o ocean.jpg "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80&fm=jpg"
curl -L -o stars.jpg "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?w=1920&q=80&fm=jpg"
```

Expected: четыре JPG-файла размером ~150–400 KB каждый. Проверь через `ls -lh d:/Kairos/frontend/public/wallpapers`.

- [ ] **Step 3: Опционально — оптимизировать через `sharp`/`imagemin` (если уже установлены)**

Можно пропустить на MVP, Next.js при build сам оптимизирует через `next/image`.

- [ ] **Step 4: Commit (assets — это не код, но трекаем)**

```bash
cd d:/Kairos && git add frontend/public/wallpapers/ && git commit -m "feat(frontend): add local wallpapers (forest, mountains, ocean, stars)"
```

---

### Task 2.2: Тип `Wallpaper` и список обоев

**Files:**
- Create: `d:/Kairos/frontend/lib/wallpapers.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/lib/wallpapers.ts
/**
 * Список доступных обоев. Все файлы локально в /public/wallpapers/.
 *
 * Никаких внешних URL (ФЗ-152: персональные данные не передаются на иностранные CDN).
 */

export interface Wallpaper {
  id: string;
  src: string; // относительный путь от /public
  thumbSrc: string; // тот же файл (Next/Image сам сделает thumbnail)
  label: string;
}

export const WALLPAPERS: Wallpaper[] = [
  { id: "forest",    src: "/wallpapers/forest.jpg",    thumbSrc: "/wallpapers/forest.jpg",    label: "Лес" },
  { id: "mountains", src: "/wallpapers/mountains.jpg", thumbSrc: "/wallpapers/mountains.jpg", label: "Горы" },
  { id: "ocean",     src: "/wallpapers/ocean.jpg",     thumbSrc: "/wallpapers/ocean.jpg",     label: "Океан" },
  { id: "stars",     src: "/wallpapers/stars.jpg",     thumbSrc: "/wallpapers/stars.jpg",     label: "Звёзды" },
];

export const DEFAULT_WALLPAPER_ID = "forest";

export function getWallpaperById(id: string | null | undefined): Wallpaper {
  if (!id) return WALLPAPERS[0];
  return WALLPAPERS.find((w) => w.id === id) ?? WALLPAPERS[0];
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/lib/wallpapers.ts && git commit -m "feat(frontend): add wallpapers registry"
```

---

### Task 2.3: Хук `useWallpaper` (persist выбора)

**Files:**
- Create: `d:/Kairos/frontend/hooks/useWallpaper.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/hooks/useWallpaper.ts
"use client";

import { useCallback, useEffect, useState } from "react";

import {
  DEFAULT_WALLPAPER_ID,
  getWallpaperById,
  type Wallpaper,
} from "@/lib/wallpapers";

const STORAGE_KEY = "kairos.wallpaper-id";

export function useWallpaper() {
  const [wallpaperId, setWallpaperIdState] = useState<string>(DEFAULT_WALLPAPER_ID);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setWallpaperIdState(saved);
    } catch {
      // тихо
    }
    setMounted(true);
  }, []);

  const setWallpaperId = useCallback((id: string) => {
    setWallpaperIdState(id);
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      // тихо
    }
  }, []);

  const wallpaper: Wallpaper = getWallpaperById(wallpaperId);

  return { wallpaperId, wallpaper, setWallpaperId, mounted };
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/hooks/useWallpaper.ts && git commit -m "feat(frontend): add useWallpaper hook with localStorage persist"
```

---

### Task 2.4: Компонент `Background`

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/Background.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Layout/Background.tsx
"use client";

import Image from "next/image";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";
import { useWallpaper } from "@/hooks/useWallpaper";

/**
 * Слой фона: одна большая картинка + темовый overlay.
 *
 * Картинка статичная, через next/image для оптимизации.
 * Overlay меняется по теме (dark — bg-black/50, light — bg-white/20)
 * через useThemeTokens.
 *
 * Никаких видеообоев, никаких внешних CDN. Только локальные JPG.
 */
export function Background() {
  const { wallpaper } = useWallpaper();
  const t = useThemeTokens();

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 z-0 overflow-hidden pointer-events-none"
    >
      <Image
        key={wallpaper.id}
        src={wallpaper.src}
        alt=""
        fill
        priority
        sizes="100vw"
        className="object-cover scale-105 transition-transform duration-[20s] ease-linear"
      />
      <div className={cn("absolute inset-0 transition-colors duration-700", t.overlay)} />
    </div>
  );
}
```

- [ ] **Step 2: Подключить в `AppShell`**

В `frontend/components/Layout/AppShell.tsx` добавь импорт и рендер `<Background />` ПЕРЕД `<main>`:

```tsx
"use client";

import { Toaster } from "sonner";

import { Background } from "@/components/Layout/Background";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark, mounted } = useTheme();

  return (
    <div
      className={cn(
        "relative flex h-[100dvh] w-[100dvw] overflow-hidden font-sans transition-colors duration-700",
        mounted && isDark ? "bg-neutral-950" : "bg-warm-50",
      )}
    >
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />
      <Background />
      <main className="relative z-10 flex h-full w-full">{children}</main>
    </div>
  );
}
```

- [ ] **Step 3: Запустить dev и проверить**

```bash
cd d:/Kairos/frontend && npm run dev
```

Expected: на всех страницах виден фон с лесом (или другой если ты менял `kairos.wallpaper-id` в DevTools localStorage). Контент чата — поверх. Прерви dev.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/Background.tsx frontend/components/Layout/AppShell.tsx && git commit -m "feat(frontend): add Background layer with wallpapers and themed overlay"
```

---

### Task 2.5: UI-примитив `Button` (CVA + Slot)

**Files:**
- Create: `d:/Kairos/frontend/components/ui/Button.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/ui/Button.tsx
"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/cn";

/**
 * Универсальная кнопка в духе shadcn/ui.
 *
 * Варианты: default (primary), ghost (прозрачная), destructive (красная),
 * outline (рамка). Размеры: sm, md, lg, icon.
 *
 * Конкретный вид (тёмный/светлый) задаётся темовыми токенами от useThemeTokens
 * в местах использования. Здесь только структура и базовое поведение.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400 focus-visible:ring-offset-0 disabled:pointer-events-none disabled:opacity-50 active:scale-95",
  {
    variants: {
      variant: {
        default: "bg-accent-700 text-white hover:bg-accent-800 shadow-sm",
        ghost: "bg-transparent",
        destructive: "bg-crisis-500 text-white hover:bg-crisis-600 shadow-sm",
        outline: "border border-warm-300 bg-transparent hover:bg-warm-100",
      },
      size: {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-5 text-[15px]",
        icon: "size-10 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/ui/Button.tsx && git commit -m "feat(frontend): add Button primitive (CVA + Radix Slot)"
```

---

### Task 2.6: UI-примитив `Card`

**Files:**
- Create: `d:/Kairos/frontend/components/ui/Card.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/ui/Card.tsx
"use client";

import * as React from "react";

import { cn } from "@/lib/cn";

/**
 * Card primitives. Стиль (light/dark) задаётся через темовые токены
 * (useThemeTokens.glassPanel или glassSidebar) на стороне потребителя.
 *
 * Здесь только структура: Card / CardHeader / CardContent / CardFooter.
 */

export const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("rounded-2xl border", className)}
    {...props}
  />
));
Card.displayName = "Card";

export const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col gap-1.5 p-5", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-5 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-5 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/ui/Card.tsx && git commit -m "feat(frontend): add Card primitives"
```

---

### Task 2.7: UI-примитив `Avatar` (Radix)

**Files:**
- Create: `d:/Kairos/frontend/components/ui/Avatar.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/ui/Avatar.tsx
"use client";

import * as React from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";

import { cn } from "@/lib/cn";

/**
 * Avatar primitives на базе Radix.
 * Image grace fallback на AvatarFallback (если URL не загрузился).
 */

export const Avatar = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Root>
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex size-10 shrink-0 overflow-hidden rounded-full",
      className,
    )}
    {...props}
  />
));
Avatar.displayName = AvatarPrimitive.Root.displayName;

export const AvatarImage = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Image>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Image>
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Image
    ref={ref}
    className={cn("aspect-square h-full w-full object-cover", className)}
    {...props}
  />
));
AvatarImage.displayName = AvatarPrimitive.Image.displayName;

export const AvatarFallback = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Fallback>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Fallback>
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Fallback
    ref={ref}
    className={cn(
      "flex h-full w-full items-center justify-center rounded-full",
      className,
    )}
    {...props}
  />
));
AvatarFallback.displayName = AvatarPrimitive.Fallback.displayName;
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/ui/Avatar.tsx && git commit -m "feat(frontend): add Avatar primitives (Radix)"
```

---

### Task 2.8: UI-примитив `Dialog` (Radix)

**Files:**
- Create: `d:/Kairos/frontend/components/ui/Dialog.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/ui/Dialog.tsx
"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "@/lib/cn";

/**
 * Dialog primitives на базе Radix.
 *
 * Использование:
 *   <Dialog open={isOpen} onOpenChange={setIsOpen}>
 *     <DialogContent className={t.glassPanel}>
 *       <DialogHeader>
 *         <DialogTitle>...</DialogTitle>
 *       </DialogHeader>
 *       ...
 *     </DialogContent>
 *   </Dialog>
 *
 * Esc и клик вне закрывают автоматически. Trap-focus встроен.
 */

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogPortal = DialogPrimitive.Portal;
export const DialogClose = DialogPrimitive.Close;

export const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-2xl rounded-2xl",
        "data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
        "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-md opacity-70 transition-opacity hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400">
        <X className="size-4" />
        <span className="sr-only">Закрыть</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

export const DialogHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("flex flex-col gap-1.5 text-left", className)}
    {...props}
  />
);
DialogHeader.displayName = "DialogHeader";

export const DialogFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",
      className,
    )}
    {...props}
  />
);
DialogFooter.displayName = "DialogFooter";

export const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

export const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm opacity-70", className)}
    {...props}
  />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/ui/Dialog.tsx && git commit -m "feat(frontend): add Dialog primitives (Radix)"
```

---

### Task 2.9: `ThemeToggle` компонент

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/ThemeToggle.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Layout/ThemeToggle.tsx
"use client";

import { motion } from "motion/react";
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";
import { useThemeTokens } from "@/lib/theme-tokens";

/**
 * Кнопка переключения темы. Размещается в RightDock.
 * Иконка крутится при смене (motion).
 */
export function ThemeToggle() {
  const { isDark, toggle, mounted } = useTheme();
  const t = useThemeTokens();

  if (!mounted) return <div className="size-11" aria-hidden="true" />;

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={isDark ? "Включить светлую тему" : "Включить тёмную тему"}
      className={cn(
        "rounded-full size-11 backdrop-blur-xl transition-all duration-300 hover:scale-110 active:scale-90 border-none",
        t.glassSidebar,
        t.textMain,
        t.btnHover,
      )}
    >
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 0 : 90, scale: isDark ? 1 : 1.1 }}
        transition={{ duration: 0.4, ease: "backOut" }}
      >
        {isDark ? <Moon className="size-5" /> : <Sun className="size-5" />}
      </motion.div>
    </Button>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/ThemeToggle.tsx && git commit -m "feat(frontend): add ThemeToggle component"
```

---

### Task 2.10: `TipCard` (статичные «советы дня»)

**Files:**
- Create: `d:/Kairos/frontend/lib/tips.ts`
- Create: `d:/Kairos/frontend/components/Layout/TipCard.tsx`

- [ ] **Step 1: Создать список советов**

```ts
// frontend/lib/tips.ts
/**
 * Статичные «советы дня» — НЕ персонализированные.
 *
 * Важно: эти советы — общие психологические рекомендации, а не вытяжка
 * из досье пользователя. Не показываем тут содержимое разговоров —
 * это создаёт ощущение слежки.
 *
 * Список — в духе SFBT/MI: мягкие напоминания о ресурсе.
 */

export interface Tip {
  id: string;
  text: string;
}

export const TIPS: Tip[] = [
  { id: "walk", text: "Прогулка пять минут — иногда этого достаточно, чтобы голова стала яснее." },
  { id: "water", text: "Стакан воды и три медленных вдоха. Это маленький, но настоящий сброс." },
  { id: "name", text: "То, что чувствуешь — назови словом. Иногда этого хватает." },
  { id: "reach", text: "Если тяжело — позвонить кому-то близкому это не слабость." },
  { id: "small", text: "Сделай одну маленькую вещь, которая тебе по силам прямо сейчас." },
  { id: "rest", text: "Отдохнуть — тоже работа. Не нужно её заслуживать." },
  { id: "breath", text: "Дыхание 4-4-6: вдох на 4, пауза на 4, выдох на 6. Повтори трижды." },
];

/**
 * Возвращает совет дня по дате (детерминированно — один в сутки).
 */
export function getTipOfTheDay(): Tip {
  const dayOfYear = Math.floor(
    (Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) /
      (24 * 60 * 60 * 1000),
  );
  return TIPS[dayOfYear % TIPS.length];
}
```

- [ ] **Step 2: Создать TipCard**

```tsx
// frontend/components/Layout/TipCard.tsx
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Lightbulb, X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";
import { getTipOfTheDay } from "@/lib/tips";

const STORAGE_KEY = "kairos.tip-dismissed-day";

function getDayKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
}

/**
 * Плавающая карточка «Совет дня» в правом доке.
 * Закрывается × → не показывается до следующего дня.
 */
export function TipCard() {
  const t = useThemeTokens();
  const tip = getTipOfTheDay();

  const [isVisible, setIsVisible] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem(STORAGE_KEY) !== getDayKey();
    } catch {
      return true;
    }
  });

  const handleDismiss = () => {
    setIsVisible(false);
    try {
      localStorage.setItem(STORAGE_KEY, getDayKey());
    } catch {
      // тихо
    }
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, height: 0 }}
          animate={{ opacity: 1, scale: 1, height: "auto" }}
          exit={{ opacity: 0, scale: 0.95, height: 0, filter: "blur(4px)" }}
          transition={{ duration: 0.3 }}
          className="w-[200px] mt-4 overflow-hidden pointer-events-auto"
        >
          <Card className={cn("backdrop-blur-3xl rounded-3xl relative", t.tipCard)}>
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
              <X className="size-3" />
            </Button>
            <CardHeader className="flex flex-col items-start gap-2 pb-2 pt-4 px-4">
              <div
                className={cn(
                  "size-8 rounded-xl flex items-center justify-center shadow-inner shrink-0",
                  t.tipIcon,
                )}
              >
                <Lightbulb className="size-4" />
              </div>
              <div className="font-semibold text-[13px] leading-tight">
                Совет дня
              </div>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <p className="text-[12px] leading-[1.5] font-medium opacity-90">
                {tip.text}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

- [ ] **Step 3: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/lib/tips.ts frontend/components/Layout/TipCard.tsx && git commit -m "feat(frontend): add daily tips and TipCard component"
```

---

### Task 2.11: `RightDock` (без SOS пока — добавим в Phase 5)

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/RightDock.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Layout/RightDock.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { ThemeToggle } from "@/components/Layout/ThemeToggle";
import { TipCard } from "@/components/Layout/TipCard";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";
import { useThemeTokens } from "@/lib/theme-tokens";

/**
 * Правый плавающий dock: тоггл темы + аватар (ведёт на /profile) + TipCard.
 *
 * SOS-кнопка добавляется в Phase 5 — она требует доступа к crisisLevel
 * из useChat-контекста, поэтому будет рендериться внутри ChatContainer
 * и абсолютно позиционироваться в этой же области.
 *
 * Скрывается на узких экранах (<768px) — на мобиле тоггл темы доступен
 * через /settings, аватар через жест влево к сайдбару.
 */
export function RightDock() {
  const t = useThemeTokens();
  const { isDark } = useTheme();
  const pathname = usePathname();
  const isOnProfile = pathname.startsWith("/profile");

  return (
    <aside
      className="hidden md:flex absolute right-0 top-0 h-full w-[260px] lg:w-[280px] flex-col p-6 gap-4 items-end z-20 pointer-events-none"
      aria-label="Дополнительная панель"
    >
      <div className="flex items-center gap-3 pointer-events-auto">
        <ThemeToggle />
        <Link
          href={isOnProfile ? "/chat" : "/profile"}
          aria-label={isOnProfile ? "Вернуться в чат" : "Открыть профиль"}
        >
          <Avatar
            className={cn(
              "size-11 cursor-pointer ring-2 ring-transparent transition-all duration-300 hover:scale-105 active:scale-95 shadow-md",
              isOnProfile && (isDark ? "ring-white/50" : "ring-accent-500/50"),
            )}
          >
            <AvatarFallback
              className={cn(
                "backdrop-blur-xl font-medium border",
                t.glassSidebar,
                t.textMain,
              )}
            >
              <User className="size-5" />
            </AvatarFallback>
          </Avatar>
        </Link>
      </div>

      <TipCard />
    </aside>
  );
}
```

- [ ] **Step 2: Подключить в `AppShell`**

В `frontend/components/Layout/AppShell.tsx`:

```tsx
"use client";

import { Toaster } from "sonner";

import { Background } from "@/components/Layout/Background";
import { RightDock } from "@/components/Layout/RightDock";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark, mounted } = useTheme();

  return (
    <div
      className={cn(
        "relative flex h-[100dvh] w-[100dvw] overflow-hidden font-sans transition-colors duration-700",
        mounted && isDark ? "bg-neutral-950" : "bg-warm-50",
      )}
    >
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />
      <Background />
      <main className="relative z-10 flex h-full w-full">{children}</main>
      <RightDock />
    </div>
  );
}
```

- [ ] **Step 3: Запустить dev и проверить**

```bash
cd d:/Kairos/frontend && npm run dev
```

Expected:
- В правом верхнем углу — тоггл темы + аватар + плавающая карточка совета
- Тоггл темы действительно переключает фон/обои/прочее
- Клик на аватар ведёт на `/profile`
- × на карточке совета закрывает её до завтра
- Прерви dev

- [ ] **Step 4: Type-check + lint**

```bash
cd d:/Kairos/frontend && npm run type-check && npm run lint
```

Expected: без ошибок.

- [ ] **Step 5: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/RightDock.tsx frontend/components/Layout/AppShell.tsx && git commit -m "feat(frontend): add RightDock with ThemeToggle, Avatar, TipCard"
```

---

**Phase 2 Checkpoint:** После этой фазы:
- На всех страницах виден фоновый JPG с тёплым/тёмным overlay
- В правом верхнем углу — кнопка темы (Sun/Moon) и аватар
- Тоггл темы реально работает: меняется overlay, классы, всё
- Карточка «Совет дня» появляется, закрывается, помнит до следующего дня
- Все UI-примитивы готовы (Button, Card, Avatar, Dialog) для следующих фаз
- Старый ChatContainer всё ещё видно в центре (без визуального redesign — это в Phase 4)

---

## Phase 3: Sidebar с историей сессий

Цель: построить левый сайдбар с активной сессией + кнопкой «Новый разговор» + плавающими кнопками настроек/тоггла. Сайдбар работает через локальный Dexie (`listSessions()`), пока бэкенд-эндпоинты не появились. Когда эндпоинт `GET /api/sessions` будет — переключим источник в одном месте (`useSessions`).

### Task 3.1: Хук `useSessions` (локальный Dexie + готовность к API)

**Files:**
- Create: `d:/Kairos/frontend/hooks/useSessions.ts`

- [ ] **Step 1: Создать файл**

```ts
// frontend/hooks/useSessions.ts
"use client";

import { useCallback, useEffect, useState } from "react";

import {
  deleteSession as dbDeleteSession,
  listSessions,
  type LocalSession,
} from "@/lib/db";

/**
 * Список сессий пользователя/гостя.
 *
 * MVP: источник — локальный Dexie. Пока бэкенд-эндпоинты GET/PATCH/DELETE
 * /api/sessions не появились (Блок ~16 PROGRESS.md).
 *
 * Когда появятся — переключаем `loadSessions` на API и оставляем Dexie
 * только как офлайн-кэш. UI не меняется.
 */

export interface SessionMeta {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

const TITLE_STORAGE_KEY = "kairos.session-titles";

function readTitles(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(TITLE_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

function writeTitles(map: Record<string, string>) {
  try {
    localStorage.setItem(TITLE_STORAGE_KEY, JSON.stringify(map));
  } catch {
    // тихо
  }
}

function defaultTitle(s: LocalSession): string {
  const date = new Date(s.createdAt);
  return `Беседа ${date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" })}`;
}

export function useSessions() {
  const [sessions, setSessions] = useState<SessionMeta[] | null>(null);

  const reload = useCallback(async () => {
    const local = await listSessions(50);
    const titles = readTitles();
    const meta: SessionMeta[] = local.map((s) => ({
      id: s.id,
      title: titles[s.id] ?? defaultTitle(s),
      createdAt: s.createdAt,
      updatedAt: s.updatedAt,
      messageCount: s.messageCount,
    }));
    setSessions(meta);
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const renameSession = useCallback(
    async (id: string, title: string) => {
      const titles = readTitles();
      titles[id] = title;
      writeTitles(titles);
      await reload();
    },
    [reload],
  );

  const deleteSession = useCallback(
    async (id: string) => {
      await dbDeleteSession(id);
      const titles = readTitles();
      delete titles[id];
      writeTitles(titles);
      await reload();
    },
    [reload],
  );

  return { sessions, reload, renameSession, deleteSession };
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/hooks/useSessions.ts && git commit -m "feat(frontend): add useSessions hook (local Dexie, ready for /api/sessions)"
```

---

### Task 3.2: Расширить `useSession` — поддержка переключения сессий

**Files:**
- Modify: `d:/Kairos/frontend/hooks/useSession.ts`

- [ ] **Step 1: Добавить функции `switchToSession` и проверить guestId/sessionId работают как раньше**

Новый код файла (полностью):

```ts
"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * Хук управления session_id и guest_id для гостевого пользователя.
 *
 * - guest_id хранится в localStorage навсегда.
 * - session_id хранится в localStorage (поменяли с sessionStorage в Phase 3),
 *   потому что теперь у нас мульти-сессии: пользователь может иметь несколько
 *   бесед и переключаться между ними. Активная сессия — та, что в localStorage.
 */

const GUEST_ID_KEY = "kairos.guest_id";
const SESSION_ID_KEY = "kairos.session_id";

function generateUuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useSession() {
  const [guestId, setGuestId] = useState<string | null>(null);
  const [sessionId, setSessionIdState] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let gid = localStorage.getItem(GUEST_ID_KEY);
    if (!gid) {
      gid = generateUuid();
      localStorage.setItem(GUEST_ID_KEY, gid);
    }
    setGuestId(gid);

    let sid = localStorage.getItem(SESSION_ID_KEY);
    if (!sid) {
      sid = generateUuid();
      localStorage.setItem(SESSION_ID_KEY, sid);
    }
    setSessionIdState(sid);
  }, []);

  const resetSession = useCallback(() => {
    if (typeof window === "undefined") return;
    const newSid = generateUuid();
    localStorage.setItem(SESSION_ID_KEY, newSid);
    setSessionIdState(newSid);
  }, []);

  const switchToSession = useCallback((id: string) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(SESSION_ID_KEY, id);
    setSessionIdState(id);
  }, []);

  return { guestId, sessionId, resetSession, switchToSession };
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/hooks/useSession.ts && git commit -m "feat(frontend): support session switching (move sessionId to localStorage)"
```

---

### Task 3.3: `RenameChatDialog` (Radix Dialog)

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/RenameChatDialog.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Layout/RenameChatDialog.tsx
"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/Dialog";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";

interface RenameChatDialogProps {
  open: boolean;
  initialTitle: string;
  onClose: () => void;
  onConfirm: (newTitle: string) => void;
}

export function RenameChatDialog({
  open,
  initialTitle,
  onClose,
  onConfirm,
}: RenameChatDialogProps) {
  const t = useThemeTokens();
  const [value, setValue] = useState(initialTitle);

  useEffect(() => {
    if (open) setValue(initialTitle);
  }, [open, initialTitle]);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed) {
      onClose();
      return;
    }
    onConfirm(trimmed);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className={cn(t.glassPanel, t.textMain, "max-w-sm")}>
        <DialogHeader>
          <DialogTitle>Переименовать беседу</DialogTitle>
        </DialogHeader>
        <input
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          placeholder="Новое название..."
          className={cn(
            "w-full px-3 py-2 rounded-xl outline-none transition-colors text-base",
            t.inputWrapper,
            t.textMain,
          )}
        />
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className={t.textMain}>
            Отмена
          </Button>
          <Button onClick={submit}>Сохранить</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/RenameChatDialog.tsx && git commit -m "feat(frontend): add RenameChatDialog component"
```

---

### Task 3.4: `Sidebar` компонент

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/Sidebar.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Layout/Sidebar.tsx
"use client";

import { Fragment, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion } from "motion/react";
import { Edit2, MessageSquare, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { RenameChatDialog } from "@/components/Layout/RenameChatDialog";
import { cn } from "@/lib/cn";
import { useSession } from "@/hooks/useSession";
import { useSessions, type SessionMeta } from "@/hooks/useSessions";
import { useSidebar } from "@/hooks/useSidebar";
import { useThemeTokens } from "@/lib/theme-tokens";

const SIDEBAR_WIDTH = 240;

/**
 * Левый сайдбар: «новый разговор» + список сессий.
 *
 * MVP: один активный чат по умолчанию (uклон в single-chat).
 * Кнопка + создаёт новую сессию. Текущая остаётся в списке.
 *
 * Контекстное меню: ПКМ или двойной клик → переименовать / удалить.
 */
export function Sidebar() {
  const t = useThemeTokens();
  const router = useRouter();
  const pathname = usePathname();
  const { isOpen } = useSidebar();
  const { sessionId, resetSession, switchToSession } = useSession();
  const { sessions, renameSession, deleteSession } = useSessions();

  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    session: SessionMeta;
  } | null>(null);
  const [renameTarget, setRenameTarget] = useState<SessionMeta | null>(null);

  const isOnChat = pathname === "/chat" || pathname === "/";

  const handleNewChat = () => {
    resetSession();
    if (!isOnChat) router.push("/chat");
  };

  const handleSelectSession = (s: SessionMeta) => {
    switchToSession(s.id);
    if (!isOnChat) router.push("/chat");
  };

  const handleContextMenu = (e: React.MouseEvent, s: SessionMeta) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, session: s });
  };

  // Закрываем контекстное меню при клике вне
  if (typeof window !== "undefined" && contextMenu) {
    setTimeout(() => {
      const close = () => {
        setContextMenu(null);
        window.removeEventListener("click", close);
      };
      window.addEventListener("click", close);
    }, 0);
  }

  return (
    <>
      <motion.aside
        initial={false}
        animate={{
          width: isOpen ? SIDEBAR_WIDTH : 0,
          borderRightWidth: isOpen ? 1 : 0,
        }}
        transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
        className={cn(
          "h-full flex-shrink-0 overflow-hidden relative z-30 transition-colors duration-700",
          t.glassSidebar,
        )}
        style={{ willChange: "width" }}
        aria-label="История бесед"
      >
        <div
          className="h-full flex flex-col p-4 pb-28"
          style={{ width: SIDEBAR_WIDTH }}
        >
          <Button
            onClick={handleNewChat}
            className={cn(
              "w-full justify-start gap-3 h-12 px-4 rounded-xl",
              t.btnPrimary,
            )}
          >
            <Plus className="size-4" />
            Новый разговор
          </Button>

          <div className="h-6" />

          <div
            className={cn(
              "text-xs font-semibold tracking-wider uppercase mb-2 px-2 opacity-60",
              t.textMain,
            )}
          >
            Ваши беседы
          </div>

          <div className="flex-1 overflow-y-auto pr-1 -mr-1 flex flex-col gap-0.5 custom-scrollbar">
            {sessions === null ? (
              <div className={cn("text-xs px-2 py-3", t.textMuted)}>
                Загружаю…
              </div>
            ) : sessions.length === 0 ? (
              <div className={cn("text-xs px-2 py-3 leading-relaxed", t.textMuted)}>
                История появится после первого сообщения.
              </div>
            ) : (
              sessions.map((s, idx) => {
                const isActive = sessionId === s.id;
                return (
                  <Fragment key={s.id}>
                    <Button
                      variant="ghost"
                      onContextMenu={(e) => handleContextMenu(e, s)}
                      onDoubleClick={(e) => handleContextMenu(e, s)}
                      onClick={() => handleSelectSession(s)}
                      className={cn(
                        "w-full font-medium justify-start h-11 px-3 rounded-xl group",
                        t.textMuted,
                        t.btnHover,
                        isActive && t.btnHover && "bg-white/10 dark:bg-white/15",
                      )}
                    >
                      <MessageSquare
                        className={cn(
                          "size-4 mr-2 opacity-60 transition-transform group-hover:scale-110",
                          isActive && "opacity-100",
                        )}
                      />
                      <span className="truncate">{s.title}</span>
                    </Button>
                    {idx < sessions.length - 1 && (
                      <div className={cn("h-px mx-3", t.divider)} />
                    )}
                  </Fragment>
                );
              })
            )}
          </div>
        </div>
      </motion.aside>

      {/* Контекстное меню */}
      {contextMenu && (
        <div
          className={cn(
            "fixed z-50 py-1.5 w-48 rounded-xl shadow-2xl backdrop-blur-xl border",
            t.glassPanel,
            t.textMain,
          )}
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            type="button"
            className={cn(
              "flex items-center gap-3 px-3 py-2 text-sm cursor-pointer mx-1.5 rounded-md w-[calc(100%-12px)]",
              t.btnHover,
            )}
            onClick={() => {
              setRenameTarget(contextMenu.session);
              setContextMenu(null);
            }}
          >
            <Edit2 className="size-4" /> Переименовать
          </button>
          <div className={cn("h-px my-1", t.divider)} />
          <button
            type="button"
            className="flex items-center gap-3 px-3 py-2 text-sm cursor-pointer mx-1.5 rounded-md text-crisis-500 hover:bg-crisis-500/10 w-[calc(100%-12px)]"
            onClick={async () => {
              if (
                !confirm(
                  `Удалить беседу «${contextMenu.session.title}»? Сообщения будут удалены безвозвратно.`,
                )
              ) {
                setContextMenu(null);
                return;
              }
              await deleteSession(contextMenu.session.id);
              if (sessionId === contextMenu.session.id) {
                resetSession();
              }
              toast.success("Беседа удалена");
              setContextMenu(null);
            }}
          >
            <Trash2 className="size-4" /> Удалить
          </button>
        </div>
      )}

      {/* Диалог переименования */}
      <RenameChatDialog
        open={renameTarget !== null}
        initialTitle={renameTarget?.title ?? ""}
        onClose={() => setRenameTarget(null)}
        onConfirm={async (newTitle) => {
          if (!renameTarget) return;
          await renameSession(renameTarget.id, newTitle);
          toast.success("Беседа переименована");
          setRenameTarget(null);
        }}
      />
    </>
  );
}

export { SIDEBAR_WIDTH };
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/Sidebar.tsx && git commit -m "feat(frontend): add Sidebar with sessions list, rename, delete"
```

---

### Task 3.5: `FloatingButtons` (Settings + Toggle Sidebar)

**Files:**
- Create: `d:/Kairos/frontend/components/Layout/FloatingButtons.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Layout/FloatingButtons.tsx
"use client";

import { useRouter, usePathname } from "next/navigation";
import { motion } from "motion/react";
import { PanelLeft, Settings as SettingsIcon } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { SIDEBAR_WIDTH } from "@/components/Layout/Sidebar";
import { cn } from "@/lib/cn";
import { useSidebar } from "@/hooks/useSidebar";
import { useThemeTokens } from "@/lib/theme-tokens";

/**
 * Две плавающие кнопки в левом нижнем углу:
 *  - Settings — открыть/закрыть страницу /settings
 *  - PanelLeft — свернуть/развернуть сайдбар
 *
 * Положение анимируется в зависимости от того, открыт ли сайдбар:
 *  - открыт: настройки слева внизу, тоггл — у правого края сайдбара
 *  - закрыт: и тоггл, и настройки оба в левом нижнем углу (стэк)
 */
export function FloatingButtons() {
  const t = useThemeTokens();
  const router = useRouter();
  const pathname = usePathname();
  const { isOpen, toggle } = useSidebar();

  const isOnSettings = pathname.startsWith("/settings");

  return (
    <div
      className="absolute bottom-6 left-0 h-12 z-40 pointer-events-none"
      style={{ width: SIDEBAR_WIDTH }}
    >
      {/* Settings */}
      <motion.div
        initial={false}
        animate={{ x: 16, y: isOpen ? 0 : -52 }}
        transition={{ type: "spring", bounce: 0.25, duration: 0.6 }}
        className="absolute pointer-events-auto"
      >
        <Button
          variant="ghost"
          size="icon"
          aria-label={isOnSettings ? "Закрыть настройки" : "Открыть настройки"}
          className={cn("size-10 rounded-full", t.floatingBtn, isOnSettings && "ring-2 ring-accent-400")}
          onClick={() => router.push(isOnSettings ? "/chat" : "/settings")}
        >
          <motion.div
            className="size-full flex items-center justify-center"
            whileHover={{ rotate: 90 }}
            transition={{ duration: 0.4 }}
          >
            <SettingsIcon className="size-5" />
          </motion.div>
        </Button>
      </motion.div>

      {/* Toggle sidebar */}
      <motion.div
        initial={false}
        animate={{
          x: isOpen ? SIDEBAR_WIDTH - 16 - 40 : 16,
          y: 0,
        }}
        transition={{ type: "spring", bounce: 0.25, duration: 0.6 }}
        className="absolute pointer-events-auto"
      >
        <Button
          variant="ghost"
          size="icon"
          aria-label={isOpen ? "Свернуть сайдбар" : "Развернуть сайдбар"}
          className={cn("size-10 rounded-xl", t.floatingBtn)}
          onClick={toggle}
        >
          <motion.div
            className="size-full flex items-center justify-center"
            whileHover={{ x: -2 }}
            transition={{ type: "spring", bounce: 0.5 }}
          >
            <PanelLeft className="size-5" />
          </motion.div>
        </Button>
      </motion.div>
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/FloatingButtons.tsx && git commit -m "feat(frontend): add FloatingButtons (Settings + sidebar toggle)"
```

---

### Task 3.6: Подключить `Sidebar` и `FloatingButtons` в `AppShell`

**Files:**
- Modify: `d:/Kairos/frontend/components/Layout/AppShell.tsx`

- [ ] **Step 1: Полная замена содержимого**

```tsx
"use client";

import { Toaster } from "sonner";

import { Background } from "@/components/Layout/Background";
import { FloatingButtons } from "@/components/Layout/FloatingButtons";
import { RightDock } from "@/components/Layout/RightDock";
import { Sidebar } from "@/components/Layout/Sidebar";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark, mounted } = useTheme();

  return (
    <div
      className={cn(
        "relative flex h-[100dvh] w-[100dvw] overflow-hidden font-sans transition-colors duration-700",
        mounted && isDark ? "bg-neutral-950" : "bg-warm-50",
      )}
    >
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />
      <Background />

      <div className="relative z-10 flex h-full w-full">
        <Sidebar />
        <FloatingButtons />
        <main className="flex-1 flex flex-col h-full w-full relative overflow-hidden">
          {children}
        </main>
        <RightDock />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Запустить dev и проверить**

```bash
cd d:/Kairos/frontend && npm run dev
```

Expected:
- Слева — сайдбар «Новый разговор» + список бесед
- Внизу слева — две плавающие кнопки (Settings + Toggle)
- ПКМ на сессию → меню «Переименовать / Удалить»
- Тоггл на мобильном виде (DevTools, ширина < 768px) — сайдбар закрыт по умолчанию
- Прерви dev

- [ ] **Step 3: Type-check + lint**

```bash
cd d:/Kairos/frontend && npm run type-check && npm run lint
```

Expected: без ошибок.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/components/Layout/AppShell.tsx && git commit -m "feat(frontend): wire Sidebar and FloatingButtons into AppShell"
```

---

**Phase 3 Checkpoint:** После этой фазы:
- Левый сайдбар работает: показывает беседы (из Dexie), переключает активную, переименовывает, удаляет
- Кнопка «+» создаёт новую сессию (resetSession → новый UUID)
- Плавающие кнопки слева внизу: Settings + Toggle
- На мобильных сайдбар закрыт по умолчанию
- Контекстное меню (ПКМ / двойной клик) на беседе работает
- Активная сессия подсвечена

---

## Phase 4: Чат — переписываем ChatContainer, EmptyState, MessageBubble, InputArea

Цель: переодеть основной чат под Figma-стиль (glassmorphism, асимметричные пузыри, motion-анимации появления, новый input). Логика `useChat` не трогается — меняется только разметка и классы. Шапка чата уезжает: правый верхний угол (theme toggle, avatar, SOS) теперь в RightDock; кнопки «Профиль / Завершить» — внутри ChatContainer как меньшие control'ы.

### Task 4.1: `EmptyState` — приветственное сообщение

**Files:**
- Create: `d:/Kairos/frontend/components/Chat/EmptyState.tsx`

- [ ] **Step 1: Создать файл**

```tsx
// frontend/components/Chat/EmptyState.tsx
"use client";

import { motion } from "motion/react";
import { Sparkles } from "lucide-react";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";

/**
 * Приветственное сообщение на пустом экране.
 *
 * Никаких кликабельных карточек-затравок (см. spec, Section 6.5):
 * пользователь сам формулирует, что у него происходит.
 *
 * Тексты согласованы с философией Кайроса: «не замена», «рядом»,
 * без обесценивания и без «всё будет хорошо».
 */
export function EmptyState() {
  const t = useThemeTokens();

  return (
    <div className="flex flex-col items-center justify-center text-center max-w-xl mx-auto py-12 px-4">
      <motion.div
        className={cn(
          "size-16 rounded-full flex items-center justify-center mb-6 shadow-2xl backdrop-blur-md border",
          t.glassSidebar,
          t.textMain,
        )}
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        aria-hidden="true"
      >
        <Sparkles className="size-8" />
      </motion.div>
      <h2
        className={cn(
          "text-2xl md:text-3xl font-semibold tracking-tight mb-4",
          t.textMain,
        )}
      >
        Здесь можно говорить как есть
      </h2>
      <p className={cn("text-base leading-relaxed max-w-md", t.textMuted)}>
        Я — Кайрос. Не психолог и не врач, но я рядом, если тебе тяжело.
        Расскажи, что у тебя сейчас, — постараюсь помочь. Если это срочно,
        нажми SOS в правом верхнем углу.
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Chat/EmptyState.tsx && git commit -m "feat(frontend): add EmptyState welcome screen"
```

---

### Task 4.2: `MessageBubble` — restyle с glassmorphism

**Files:**
- Modify: `d:/Kairos/frontend/components/Chat/MessageBubble.tsx`

- [ ] **Step 1: Полная замена содержимого**

```tsx
"use client";

import { motion } from "motion/react";

import HumanTypingEffect from "./HumanTypingEffect";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  /**
   * Анимировать печать (для бота).
   * По умолчанию true — для свежих сообщений.
   * Для сообщений из истории / при перезагрузке — передавать false.
   */
  animateTyping?: boolean;
  onTypingComplete?: () => void;
  timestamp?: string;
}

/**
 * Пузырь сообщения в чате.
 *
 * Стиль: асимметричные радиусы (как в мессенджерах), glassmorphism для бота,
 * сплошной accent-цвет для пользователя.
 *
 * Анимация появления: spring с разных сторон (юзер — справа, бот — слева).
 */
export default function MessageBubble({
  role,
  content,
  animateTyping = true,
  onTypingComplete,
  timestamp,
}: MessageBubbleProps) {
  const t = useThemeTokens();
  const isBot = role === "assistant";

  return (
    <motion.div
      layout
      initial={{
        opacity: 0,
        scale: 0.7,
        y: 30,
        x: isBot ? -20 : 20,
      }}
      animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
      transition={{
        type: "spring",
        stiffness: 380,
        damping: 26,
      }}
      className={cn(
        "flex items-end gap-2 mb-3",
        isBot ? "justify-start" : "justify-end",
      )}
      style={{ transformOrigin: isBot ? "bottom left" : "bottom right" }}
    >
      <div
        className={cn(
          "relative max-w-[85%] sm:max-w-[75%] px-4 py-2.5 text-[15px] leading-[1.45] break-words shadow-sm",
          isBot ? "rounded-[20px] rounded-bl-[4px]" : "rounded-[20px] rounded-br-[4px] font-medium",
          isBot ? t.msgAi : t.msgUser,
        )}
      >
        {isBot && animateTyping ? (
          <HumanTypingEffect
            text={content}
            onComplete={onTypingComplete}
            speed="normal"
          />
        ) : (
          <span className="whitespace-pre-wrap">{content}</span>
        )}
        {timestamp && (
          <span
            className={cn(
              "block text-[10px] font-medium opacity-60 mt-1",
              isBot ? "text-right" : "text-right",
            )}
          >
            {timestamp}
          </span>
        )}
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок (props совместимы — `animateTyping`, `onTypingComplete`, `role`, `content` те же).

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Chat/MessageBubble.tsx && git commit -m "refactor(frontend): restyle MessageBubble (glassmorphism, motion, asymmetric radii)"
```

---

### Task 4.3: `TypingIndicator` — restyle

**Files:**
- Modify: `d:/Kairos/frontend/components/Chat/TypingIndicator.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { motion } from "motion/react";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";

/**
 * Индикатор «бот думает» — три точки с пульсацией.
 * Стилизован под glassmorphism пузырь бота.
 */
export default function TypingIndicator() {
  const t = useThemeTokens();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className="flex justify-start mb-3"
      role="status"
      aria-label="Бот печатает ответ"
    >
      <div
        className={cn(
          "rounded-[20px] rounded-bl-[4px] px-4 py-3 inline-flex items-center gap-1.5",
          t.msgAi,
        )}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50 animate-bounce [animation-delay:-0.3s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50 animate-bounce [animation-delay:-0.15s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50 animate-bounce" />
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Chat/TypingIndicator.tsx && git commit -m "refactor(frontend): restyle TypingIndicator with glassmorphism"
```

---

### Task 4.4: `InputArea` — restyle (без attach-меню, без mic)

**Files:**
- Modify: `d:/Kairos/frontend/components/Chat/InputArea.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";

interface InputAreaProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Поле ввода + кнопка отправки.
 *
 * Стиль: glassmorphism rounded-[28px] контейнер, кнопка-стрелка справа.
 * НЕТ голосового ввода (mic) и НЕТ прикрепления файлов на MVP —
 * это лишний функционал для кризисной помощи (см. spec).
 *
 * Особенности:
 * - Enter — отправить, Shift+Enter — новая строка
 * - Авторазмер высоты (до ~6 строк)
 * - Дисклеймер про 112 / 8-800 — внизу под полем
 */
export default function InputArea({
  onSend,
  disabled = false,
  placeholder = "Напиши, что у тебя сейчас...",
}: InputAreaProps) {
  const t = useThemeTokens();
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 144)}px`;
  }, [text]);

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="w-full px-4 sm:px-6 pb-3 sm:pb-4">
      <div className="max-w-3xl mx-auto">
        <div
          className={cn(
            "w-full rounded-[28px] backdrop-blur-2xl flex px-3 py-2 items-end gap-2 transition-all duration-300",
            t.inputWrapper,
          )}
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={disabled}
            aria-label="Сообщение"
            className={cn(
              "flex-1 resize-none bg-transparent border-none outline-none text-[15px] py-1.5 px-1 min-w-0 leading-relaxed",
              t.textMain,
              "placeholder:opacity-50",
              disabled && "opacity-50 cursor-not-allowed",
            )}
          />
          <Button
            type="button"
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            aria-label="Отправить"
            size="icon"
            className={cn(
              "size-10 rounded-full shrink-0",
              text.trim() ? cn(t.btnPrimary, "shadow-lg") : "bg-transparent",
              !text.trim() && cn(t.textMuted, t.btnHover),
            )}
          >
            <motion.div
              className="size-full flex items-center justify-center"
              whileHover={text.trim() ? { y: -1, scale: 1.1 } : undefined}
              transition={{ type: "spring", bounce: 0.5 }}
            >
              <ArrowUp className="size-[18px]" />
            </motion.div>
          </Button>
        </div>

        <p
          className={cn(
            "text-[11px] font-medium mt-2 text-center",
            t.textMuted,
          )}
        >
          Это не замена врачу или психологу. В кризисе звони{" "}
          <a href="tel:112" className="underline">
            112
          </a>{" "}
          или{" "}
          <a href="tel:88003334434" className="underline">
            8-800-333-44-34
          </a>
          .
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Chat/InputArea.tsx && git commit -m "refactor(frontend): restyle InputArea (glassmorphism, theme-aware, no attach/mic)"
```

---

### Task 4.5: `ChatContainer` — переписать без шапки, с новым layout

**Files:**
- Modify: `d:/Kairos/frontend/components/Chat/ChatContainer.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { useEffect, useRef, useState } from "react";

import CrisisInlineCard from "@/components/Crisis/CrisisInlineCard";
import CrisisPanel from "@/components/Crisis/CrisisPanel";
import SOSButton from "@/components/Crisis/SOSButton";
import MessageFeedback from "@/components/Feedback/MessageFeedback";
import SessionFeedback from "@/components/Feedback/SessionFeedback";
import { cn } from "@/lib/cn";
import { useChat } from "@/hooks/useChat";
import { useSidebar } from "@/hooks/useSidebar";
import { useThemeTokens } from "@/lib/theme-tokens";

import { EmptyState } from "./EmptyState";
import InputArea from "./InputArea";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

/**
 * Главный контейнер чата.
 *
 * Шапки больше нет — её функции ушли в RightDock (тоггл темы, аватар, SOS).
 * SOS-кнопка — единственное, что выходит за пределы чата визуально:
 * она абсолютно позиционируется в правом верхнем углу через RightDock-зону,
 * но рендерится здесь, потому что зависит от crisisLevel из useChat.
 *
 * Layout:
 *   [SOS top-right]
 *   [scrollable messages area]
 *     EmptyState (если нет сообщений)
 *     или MessageBubble * N + CrisisInlineCard + MessageFeedback + TypingIndicator
 *   [SessionFeedback (когда нажали "Завершить")]
 *   [Error bar]
 *   [InputArea]
 */
export default function ChatContainer() {
  const t = useThemeTokens();
  const chat = useChat();
  const { isOpen: isSidebarOpen } = useSidebar();
  const [crisisPanelOpen, setCrisisPanelOpen] = useState(false);
  const [sessionEnded, setSessionEnded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Авто-скролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat.messages, chat.isTyping]);

  // Авто-открытие кризисной панели при immediate
  useEffect(() => {
    if (chat.crisisLevel === "immediate" && !crisisPanelOpen) {
      setCrisisPanelOpen(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chat.crisisLevel]);

  // Контакты из последнего ответа бота (для модалки SOS)
  const lastBotMessage = [...chat.messages]
    .reverse()
    .find((m) => m.role === "assistant");
  const contactsForPanel = lastBotMessage?.crisisContacts ?? [];

  return (
    <div className="flex flex-col h-full w-full relative overflow-hidden">
      {/* SOS — абсолютно в правом верхнем углу контентной области.
          На md+ — выше RightDock-аватара (т.к. RightDock отрисован после
          этого main, но имеет свой z-index). На мобиле — справа сверху.

          Позиция: top-6 right-6 (десктоп) / top-3 right-3 (мобила).
          На md+ нужно учесть ширину RightDock — 280px — и сдвинуть SOS
          в его зону (сделаем right-[100px] чтобы быть слева от аватара). */}
      <div className="absolute top-3 right-3 md:top-6 md:right-[120px] lg:right-[130px] z-30">
        <SOSButton
          crisisLevel={chat.crisisLevel}
          onClick={() => setCrisisPanelOpen(true)}
        />
      </div>

      {/* Scrollable messages area */}
      <div
        className={cn(
          "flex-1 overflow-y-auto overflow-x-hidden w-full p-4 sm:p-6 lg:p-8 md:pr-[260px] lg:pr-[280px] flex flex-col custom-scrollbar transition-all duration-500",
          !isSidebarOpen && "md:pl-16 lg:pl-24",
        )}
      >
        <div className="w-full max-w-3xl mx-auto flex-1 flex flex-col">
          {chat.messages.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState />
            </div>
          ) : (
            <div className="w-full flex flex-col mt-auto pt-10">
              {chat.messages.map((msg, idx) => {
                const isLast = idx === chat.messages.length - 1;
                return (
                  <div key={msg.id}>
                    <MessageBubble
                      role={msg.role}
                      content={msg.content}
                      animateTyping={msg.role === "assistant" && isLast}
                    />
                    {msg.role === "assistant" &&
                      msg.crisisLevel &&
                      msg.crisisContacts && (
                        <CrisisInlineCard
                          level={msg.crisisLevel}
                          contacts={msg.crisisContacts}
                        />
                      )}
                    {msg.role === "assistant" && (
                      <MessageFeedback
                        messageId={msg.id}
                        onFeedback={chat.sendFeedback}
                      />
                    )}
                  </div>
                );
              })}
              {chat.isTyping && <TypingIndicator />}

              {sessionEnded && (
                <SessionFeedback
                  onSubmit={async (event) => {
                    await chat.sendFeedback(event);
                  }}
                  onSkip={() => setSessionEnded(false)}
                />
              )}

              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}

          {/* Кнопка "Завершить" — только если есть ответы бота и сессия не завершена */}
          {chat.messages.some((m) => m.role === "assistant") &&
            !sessionEnded &&
            chat.messages.length > 0 && (
              <div
                className={cn(
                  "self-center text-xs px-3 py-1 rounded-full transition-colors mb-4 cursor-pointer",
                  t.textMuted,
                  t.btnHover,
                )}
                onClick={() => setSessionEnded(true)}
              >
                Завершить и оставить отзыв
              </div>
            )}
        </div>
      </div>

      {/* Ошибка */}
      {chat.error && (
        <div
          className={cn(
            "border-t px-4 py-2 text-sm transition-all duration-500",
            "bg-crisis-100/80 border-crisis-300 text-crisis-800",
            !isSidebarOpen && "md:pl-16 lg:pl-24",
            "md:pr-[260px] lg:pr-[280px]",
          )}
        >
          <div className="max-w-3xl mx-auto">⚠️ {chat.error}</div>
        </div>
      )}

      {/* Поле ввода */}
      <div
        className={cn(
          "transition-all duration-500",
          !isSidebarOpen && "md:pl-16 lg:pl-24",
          "md:pr-[260px] lg:pr-[280px]",
        )}
      >
        <InputArea
          onSend={chat.sendMessage}
          disabled={chat.isTyping}
          placeholder={
            chat.messages.length === 0
              ? "Расскажи, что у тебя сейчас..."
              : "Напиши сообщение..."
          }
        />
      </div>

      {/* Модалка кризисных контактов */}
      <CrisisPanel
        isOpen={crisisPanelOpen}
        onClose={() => setCrisisPanelOpen(false)}
        contacts={contactsForPanel}
      />
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Запустить dev и проверить визуально**

```bash
cd d:/Kairos/frontend && npm run dev
```

Тест-сценарии (выполни все):
1. Открой `/chat` → видно EmptyState («Здесь можно говорить как есть»)
2. Напиши сообщение → пузырь юзера справа (синий/белый), ответ бота слева (стеклянный)
3. Под ответом бота — thumbs up/down + (опционально) CrisisInlineCard если бэкенд поднял уровень
4. Можно жать SOS вверху справа → открывается CrisisPanel
5. Переключи тему — все пузыри/инпут/EmptyState поменяли стиль
6. Сверни сайдбар → центральная область плавно расширяется
7. Создай новую беседу через «+» → пустой EmptyState

Прерви dev.

- [ ] **Step 4: Lint**

```bash
cd d:/Kairos/frontend && npm run lint
```

Expected: без ошибок.

- [ ] **Step 5: Commit**

```bash
cd d:/Kairos && git add frontend/components/Chat/ChatContainer.tsx && git commit -m "refactor(frontend): rewrite ChatContainer with new layout (no header, RightDock-aware, SOS top-right)"
```

---

### Task 4.6: Очистить `app/chat/page.tsx`

**Files:**
- Modify: `d:/Kairos/frontend/app/chat/page.tsx`

- [ ] **Step 1: Уже минимальный — проверить и оставить**

Файл уже сводится к рендеру `<ChatContainer />`. Никаких изменений не требуется. Если в нём остался лишний код после старого редизайна — почисти. Финальное содержимое:

```tsx
import ChatContainer from "@/components/Chat/ChatContainer";

export const metadata = {
  title: "Чат — Кайрос",
};

/**
 * Главная страница чата.
 *
 * MVP: один экран, без онбординга и регистрации.
 * Сразу даём пользователю возможность написать.
 */
export default function ChatPage() {
  return <ChatContainer />;
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit (только если файл изменился)**

Если изменений не было — пропусти этот шаг.

```bash
cd d:/Kairos && git add frontend/app/chat/page.tsx && git commit -m "chore(frontend): keep chat page minimal (just ChatContainer)"
```

---

**Phase 4 Checkpoint:** После этой фазы:
- Чат полностью переодет: glassmorphism пузыри, motion-анимации появления, новый input
- EmptyState с приветственным сообщением (без карточек-затравок) показан на пустом чате
- SOS-кнопка в правом верхнем углу контентной области, видна всегда
- TypingIndicator в стиле бот-пузыря
- InputArea без attach-меню и mic — только текст
- Сайдбар сворачивается → центральная область расширяется плавно
- Тёмная и светлая темы работают на всех элементах
- HumanTypingEffect сохранён (анимация набора текста ботом)

---

## Phase 5: Кризисные компоненты — restyle (логика не меняется!)

Цель: переодеть SOS-кнопку, CrisisPanel, CrisisInlineCard, MessageFeedback, SessionFeedback под новый стиль. **API всех компонентов и поведение остаются идентичными.** Это самая чувствительная фаза — после неё критически проверить что:
- SOS-кнопка по-прежнему всегда видна
- CrisisPanel автоматически открывается при `crisis_level === "immediate"`
- Все номера кликабельны как `tel:`
- Никаких новых кнопок «закрыть кризисное предупреждение» с возможностью спрятать SOS навсегда

### Task 5.1: `SOSButton` — restyle с glassmorphism

**Files:**
- Modify: `d:/Kairos/frontend/components/Crisis/SOSButton.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { motion } from "motion/react";
import { LifeBuoy } from "lucide-react";

import { cn } from "@/lib/cn";
import type { CrisisLevel } from "@/lib/types";

interface SOSButtonProps {
  crisisLevel: CrisisLevel;
  onClick: () => void;
}

/**
 * Кнопка SOS. Всегда видна. Стиль и пульсация зависят от crisisLevel.
 *
 * Поведение НЕ изменилось по сравнению с прошлой версией.
 * Изменился ТОЛЬКО стиль: glassmorphism + lucide-иконка вместо текста "SOS"
 * на нормальном уровне; на crisis-уровнях — красная заливка + текст "SOS".
 */
export default function SOSButton({ crisisLevel, onClick }: SOSButtonProps) {
  const isAlert = crisisLevel === "high" || crisisLevel === "immediate";
  const isElevated = crisisLevel === "elevated";

  const baseClasses =
    "rounded-full font-semibold text-sm transition-all duration-300 shadow-lg backdrop-blur-xl border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400";

  const stateClasses = (() => {
    if (crisisLevel === "immediate")
      return "bg-crisis-500 hover:bg-crisis-600 text-white border-crisis-400 animate-pulse";
    if (crisisLevel === "high")
      return "bg-crisis-400 hover:bg-crisis-500 text-white border-crisis-300 animate-pulse-slow";
    if (isElevated)
      return "bg-crisis-200/80 hover:bg-crisis-300 text-crisis-900 border-crisis-300/60";
    // normal
    return "bg-white/30 hover:bg-white/50 text-crisis-700 dark:bg-white/15 dark:text-white/90 dark:hover:bg-white/25 border-white/40 dark:border-white/20";
  })();

  return (
    <motion.button
      type="button"
      onClick={onClick}
      aria-label="Открыть кризисные контакты"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        baseClasses,
        stateClasses,
        isAlert ? "px-4 py-2 flex items-center gap-1.5" : "size-11 flex items-center justify-center",
      )}
    >
      <LifeBuoy className={cn(isAlert ? "size-4" : "size-5")} />
      {isAlert && <span>SOS</span>}
    </motion.button>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок (props идентичны прошлой версии: `crisisLevel`, `onClick`).

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Crisis/SOSButton.tsx && git commit -m "refactor(frontend): restyle SOSButton (glassmorphism, lucide icon, same API)"
```

---

### Task 5.2: `CrisisPanel` — переписать на Radix Dialog

**Files:**
- Modify: `d:/Kairos/frontend/components/Crisis/CrisisPanel.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { Phone } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/Dialog";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";
import type { CrisisContact } from "@/lib/types";

interface CrisisPanelProps {
  isOpen: boolean;
  onClose: () => void;
  contacts?: CrisisContact[];
}

const DEFAULT_CONTACTS: CrisisContact[] = [
  {
    name: "Экстренные службы",
    phone: "112",
    description: "Единый номер (работает без SIM-карты)",
  },
  {
    name: "МЧС — психологическая помощь",
    phone: "8-800-333-44-34",
    description: "Бесплатно, круглосуточно, анонимно",
  },
  {
    name: "Детский телефон доверия",
    phone: "8-800-2000-122",
    description: "Бесплатно, круглосуточно, анонимно (до 18 лет)",
  },
  {
    name: "Линия «0-24»",
    phone: "8-800-700-84-60",
    description: "Утрата, насилие, суицид — бесплатно, круглосуточно",
  },
];

/**
 * Модальная панель с кризисными контактами.
 *
 * Поведение: открывается по клику на SOS или автоматически из ChatContainer
 * при crisis_level === "immediate". Закрывается по Esc / клику вне / ×.
 *
 * API идентичен прошлой версии: { isOpen, onClose, contacts? }.
 */
export default function CrisisPanel({
  isOpen,
  onClose,
  contacts,
}: CrisisPanelProps) {
  const t = useThemeTokens();
  const list = contacts && contacts.length > 0 ? contacts : DEFAULT_CONTACTS;

  return (
    <Dialog open={isOpen} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className={cn(t.glassPanel, t.textMain, "max-w-md")}>
        <DialogHeader>
          <DialogTitle>Кому позвонить прямо сейчас</DialogTitle>
          <DialogDescription className={t.textMuted}>
            Эти службы работают в России. Звонок бесплатный, анонимный.
          </DialogDescription>
        </DialogHeader>

        <ul className="space-y-2.5">
          {list.map((contact) => (
            <li key={contact.phone}>
              <a
                href={`tel:${contact.phone.replace(/[^\d+]/g, "")}`}
                className={cn(
                  "block rounded-xl p-3 border transition-all duration-200 hover:scale-[1.01] active:scale-[0.99]",
                  t.glassSidebar,
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="size-9 rounded-full bg-crisis-500/20 text-crisis-500 flex items-center justify-center shrink-0">
                    <Phone className="size-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={cn("text-base font-bold", t.textMain)}>
                      {contact.phone}
                    </div>
                    <div className={cn("text-sm font-medium", t.textMain)}>
                      {contact.name}
                    </div>
                    <div className={cn("text-xs mt-0.5", t.textMuted)}>
                      {contact.description}
                    </div>
                  </div>
                </div>
              </a>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок (props идентичны).

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Crisis/CrisisPanel.tsx && git commit -m "refactor(frontend): rewrite CrisisPanel using Radix Dialog with glassmorphism"
```

---

### Task 5.3: `CrisisInlineCard` — restyle

**Files:**
- Modify: `d:/Kairos/frontend/components/Crisis/CrisisInlineCard.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { motion } from "motion/react";
import { AlertTriangle, Phone } from "lucide-react";

import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";
import type { CrisisContact, CrisisLevel } from "@/lib/types";

interface CrisisInlineCardProps {
  level: CrisisLevel;
  contacts: CrisisContact[];
}

/**
 * Карточка кризисных контактов внутри ленты сообщений.
 * Появляется под ответом бота при crisis_level != normal.
 *
 * Стиль: rounded-2xl, прозрачный crisis-цвет, мягкая анимация появления.
 */
export default function CrisisInlineCard({
  level,
  contacts,
}: CrisisInlineCardProps) {
  const { isDark } = useTheme();

  if (level === "normal" || contacts.length === 0) return null;

  const headers: Record<Exclude<CrisisLevel, "normal">, string> = {
    elevated: "На всякий случай — телефоны помощи",
    high: "Если станет тяжело, позвони сюда",
    immediate: "Прямо сейчас позвони сюда",
  };

  const colorClass: Record<Exclude<CrisisLevel, "normal">, string> = {
    elevated: isDark
      ? "border-amber-400/30 bg-amber-500/10 text-amber-100"
      : "border-warm-300 bg-warm-100/80 text-warm-900",
    high: isDark
      ? "border-crisis-400/40 bg-crisis-500/15 text-crisis-50"
      : "border-crisis-300 bg-crisis-50 text-crisis-900",
    immediate: isDark
      ? "border-crisis-400/60 bg-crisis-500/25 text-crisis-50"
      : "border-crisis-500 bg-crisis-100 text-crisis-900",
  };

  const styledLevel = level as Exclude<CrisisLevel, "normal">;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "rounded-2xl border-2 p-3 my-2 max-w-[80%] backdrop-blur-md",
        colorClass[styledLevel],
      )}
    >
      <div className="flex items-center gap-2 mb-2 text-sm font-semibold">
        <AlertTriangle className="size-4" />
        {headers[styledLevel]}
      </div>
      <ul className="space-y-1.5">
        {contacts.slice(0, 3).map((c) => (
          <li key={c.phone}>
            <a
              href={`tel:${c.phone.replace(/[^\d+]/g, "")}`}
              className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/20 transition-colors text-sm"
            >
              <Phone className="size-3.5 opacity-70" />
              <span className="font-bold">{c.phone}</span>
              <span className="opacity-80">— {c.name}</span>
            </a>
          </li>
        ))}
      </ul>
    </motion.div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Crisis/CrisisInlineCard.tsx && git commit -m "refactor(frontend): restyle CrisisInlineCard with motion and theme-aware colors"
```

---

### Task 5.4: `MessageFeedback` — restyle

**Files:**
- Modify: `d:/Kairos/frontend/components/Feedback/MessageFeedback.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { ThumbsDown, ThumbsUp } from "lucide-react";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";
import type { FeedbackEventType } from "@/lib/types";

interface MessageFeedbackProps {
  messageId: string;
  onFeedback: (event: FeedbackEventType, messageId: string) => Promise<void> | void;
}

/**
 * Thumbs up/down под каждым ответом бота. Ключевой сигнал для data flywheel.
 *
 * После клика — заменяется на тихое «Спасибо». Повторно нажать нельзя.
 * API идентичен прошлой версии.
 */
export default function MessageFeedback({
  messageId,
  onFeedback,
}: MessageFeedbackProps) {
  const t = useThemeTokens();
  const [submitted, setSubmitted] = useState<"up" | "down" | null>(null);

  const handleClick = async (kind: "up" | "down") => {
    if (submitted) return;
    setSubmitted(kind);
    const event: FeedbackEventType = kind === "up" ? "thumbs_up" : "thumbs_down";
    try {
      await onFeedback(event, messageId);
    } catch {
      // тихо игнорируем
    }
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={cn("text-xs mt-1 ml-2 select-none", t.textMuted)}
        aria-live="polite"
      >
        {submitted === "up"
          ? "Спасибо, что отметил."
          : "Спасибо, я учту это."}
      </motion.div>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-1 ml-2">
      <button
        type="button"
        onClick={() => handleClick("up")}
        aria-label="Это сообщение помогло"
        className={cn(
          "p-1.5 rounded-lg transition-all",
          t.textMuted,
          t.btnHover,
        )}
      >
        <ThumbsUp className="size-3.5" />
      </button>
      <button
        type="button"
        onClick={() => handleClick("down")}
        aria-label="Это сообщение не помогло"
        className={cn(
          "p-1.5 rounded-lg transition-all",
          t.textMuted,
          t.btnHover,
        )}
      >
        <ThumbsDown className="size-3.5" />
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Feedback/MessageFeedback.tsx && git commit -m "refactor(frontend): restyle MessageFeedback with lucide icons and theme tokens"
```

---

### Task 5.5: `SessionFeedback` — restyle

**Files:**
- Modify: `d:/Kairos/frontend/components/Feedback/SessionFeedback.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { useState } from "react";
import { motion } from "motion/react";

import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";
import type { FeedbackEventType } from "@/lib/types";

interface SessionFeedbackProps {
  onSubmit: (event: FeedbackEventType) => Promise<void> | void;
  onSkip?: () => void;
}

/**
 * Карточка обратной связи по сессии. Показывается при «Завершить сессию».
 *
 * Три варианта: felt_better / no_change / felt_worse.
 * После выбора — благодарность и закрытие.
 */
export default function SessionFeedback({
  onSubmit,
  onSkip,
}: SessionFeedbackProps) {
  const t = useThemeTokens();
  const [submitted, setSubmitted] = useState<FeedbackEventType | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async (event: FeedbackEventType) => {
    if (submitted || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onSubmit(event);
      setSubmitted(event);
    } catch {
      // тихо
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="my-6 mx-auto max-w-md"
      >
        <Card className={cn(t.glassPanel, "p-4 text-center")}>
          <p className={cn("text-sm", t.textMain)}>
            Спасибо. Это помогает мне учиться.
          </p>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="my-6 mx-auto max-w-md"
    >
      <Card className={cn(t.glassPanel)}>
        <CardContent className="p-5">
          <p className={cn("text-sm mb-4 text-center", t.textMain)}>
            Как ты сейчас, после нашего разговора?
          </p>
          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              disabled={isSubmitting}
              onClick={() => handleClick("felt_better")}
              variant="ghost"
              size="sm"
              className={cn(
                "flex-1",
                "bg-accent-100/60 hover:bg-accent-200/80 text-accent-900",
                "dark:bg-accent-500/20 dark:hover:bg-accent-500/30 dark:text-accent-50",
              )}
            >
              Стало легче
            </Button>
            <Button
              disabled={isSubmitting}
              onClick={() => handleClick("no_change")}
              variant="ghost"
              size="sm"
              className={cn(
                "flex-1",
                "bg-warm-200/60 hover:bg-warm-300/80 text-warm-900",
                "dark:bg-white/10 dark:hover:bg-white/20 dark:text-white",
              )}
            >
              Не уверен
            </Button>
            <Button
              disabled={isSubmitting}
              onClick={() => handleClick("felt_worse")}
              variant="ghost"
              size="sm"
              className={cn(
                "flex-1",
                "bg-crisis-50 hover:bg-crisis-100 text-crisis-900",
                "dark:bg-crisis-500/20 dark:hover:bg-crisis-500/30 dark:text-crisis-50",
              )}
            >
              Хуже
            </Button>
          </div>
          {onSkip && (
            <button
              type="button"
              onClick={onSkip}
              className={cn(
                "block mx-auto mt-3 text-xs transition-colors",
                t.textMuted,
              )}
            >
              Пропустить
            </button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Feedback/SessionFeedback.tsx && git commit -m "refactor(frontend): restyle SessionFeedback with glass card and theme-aware buttons"
```

---

### Task 5.6: Кризисная регрессия (manual smoke test)

Это не код — это обязательный шаг проверки перед переходом в Phase 6.

- [ ] **Step 1: Запустить full stack (фронт + бэкенд)**

В одном терминале:
```bash
cd d:/Kairos/backend && uvicorn app.main:app --reload --port 8001
```

В другом:
```bash
cd d:/Kairos/frontend && npm run dev
```

Открой `http://localhost:3000/chat`.

- [ ] **Step 2: Сценарий «нормальный диалог»**

Напиши: «Привет, как дела?»

Expected:
- Ответ бота приходит
- SOS-кнопка в правом верхнем углу — иконка `LifeBuoy`, без пульсации, прозрачно-нейтральная
- thumbs up/down под ответом

- [ ] **Step 3: Сценарий «elevated»**

Напиши: «мне очень тревожно, не могу нормально дышать»

Expected:
- Ответ бота
- SOS-кнопка изменила вид на тёплый предупреждающий (если бэкенд поднял до `elevated`)
- Под ответом может появиться `CrisisInlineCard` (mild)

- [ ] **Step 4: Сценарий «high»**

Напиши: «всё бессмысленно, нет выхода»

Expected:
- Ответ бота
- SOS — красный, медленная пульсация (`animate-pulse-slow`), показан текст «SOS»
- `CrisisInlineCard` под ответом — заметная

- [ ] **Step 5: Сценарий «immediate» — критический**

Напиши: «хочу умереть» (если бэкенд знает этот триггер) или эквивалент из crisis_situations.py.

Expected:
- 🚨 **`CrisisPanel` открывается АВТОМАТИЧЕСКИ** (без нажатия SOS)
- В модалке — список номеров, все кликабельны как `tel:`
- Esc и клик вне закрывают её
- SOS — яркий красный, быстрая пульсация

Если **CrisisPanel НЕ открылся автоматически** — это бага и blocker. Вернись в Task 4.5 и проверь логику в `useEffect` на `chat.crisisLevel === "immediate"`.

- [ ] **Step 6: Проверка темы при кризисе**

Переключи тему через RightDock-тоггл во время immediate-кризиса.

Expected:
- SOS-кнопка остаётся узнаваемо красной в обеих темах
- CrisisInlineCard читаем в обеих темах
- CrisisPanel читаем в обеих темах

- [ ] **Step 7: Если всё ок — commit (никаких изменений в коде, просто чек-пойнт)**

```bash
cd d:/Kairos && git commit --allow-empty -m "test(frontend): manual crisis regression — pass after Phase 5 restyle"
```

---

**Phase 5 Checkpoint:** После этой фазы:
- Все 5 кризисных и feedback-компонентов переодеты под новый стиль
- Поведение НЕ изменилось: API идентичен, автооткрытие panel работает, все номера кликабельны
- Manual regression test пройден на всех уровнях кризиса
- Темы корректно отображаются на crisis-компонентах в обоих режимах

---

## Phase 6: Профиль и досье — restyle

Цель: переодеть страницу `/profile` и компонент `DossierView` под общий стиль (glassmorphism, мотион), сохраняя всю API-логику работы с досье.

### Task 6.1: `DossierView` — restyle

**Files:**
- Modify: `d:/Kairos/frontend/components/Dossier/DossierView.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Folder, ShieldAlert, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";
import {
  deleteAllDossier,
  deleteFact,
  fetchDossier,
} from "@/lib/dossierApi";
import type { DossierFact } from "@/lib/types";

interface DossierViewProps {
  guestId: string;
}

/**
 * Просмотр и управление досье. Логика та же что была: fetch / delete / wipe.
 * Стиль: glassmorphism карточки, motion-анимации появления, темовые токены.
 */
export default function DossierView({ guestId }: DossierViewProps) {
  const t = useThemeTokens();
  const [facts, setFacts] = useState<DossierFact[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isWiping, setIsWiping] = useState(false);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guestId]);

  async function load() {
    try {
      const res = await fetchDossier(guestId);
      setFacts(res.facts);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить досье");
    }
  }

  async function handleDeleteFact(factId: string) {
    if (!confirm("Удалить этот факт? Это действие необратимо.")) return;
    try {
      await deleteFact(guestId, factId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    }
  }

  async function handleWipeAll() {
    if (
      !confirm(
        "Удалить ВСЁ досье? Кайрос забудет всё, что узнал о тебе. " +
          "Это действие необратимо.",
      )
    )
      return;
    setIsWiping(true);
    try {
      await deleteAllDossier(guestId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    } finally {
      setIsWiping(false);
    }
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-4">
        <Card className={cn(t.glassPanel, "p-4 text-crisis-500")}>
          ⚠️ {error}
        </Card>
      </div>
    );
  }

  if (facts === null) {
    return (
      <div className={cn("max-w-3xl mx-auto p-4", t.textMuted)}>
        Загружаю досье...
      </div>
    );
  }

  if (facts.length === 0) {
    return (
      <div className="max-w-3xl mx-auto p-4 space-y-4">
        <header>
          <h1 className={cn("text-xl font-semibold", t.textMain)}>
            Что знает Кайрос
          </h1>
        </header>
        <Card className={cn(t.glassPanel, "p-6")}>
          <p className={cn("leading-relaxed", t.textMuted)}>
            Кайрос ещё ничего не запомнил о тебе. Это появится после нескольких
            бесед — обычно через 15 минут после того, как ты замолкаешь, бот
            просматривает разговор и сохраняет важное в досье.
          </p>
        </Card>
      </div>
    );
  }

  // Группировка по папкам (folder/subfolder)
  const byFolder = facts.reduce<Record<string, DossierFact[]>>((acc, f) => {
    const key = f.subfolder ? `${f.folder}/${f.subfolder}` : f.folder;
    (acc[key] ??= []).push(f);
    return acc;
  }, {});

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      <motion.header
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={cn("text-2xl font-semibold tracking-tight", t.textMain)}>
          Что знает Кайрос
        </h1>
        <p className={cn("text-sm mt-1", t.textMuted)}>
          Это всё, что Кайрос запомнил о тебе из ваших разговоров. Ты можешь
          удалить любой факт или всё сразу.
        </p>
      </motion.header>

      {Object.entries(byFolder).map(([folder, folderFacts], folderIdx) => (
        <motion.section
          key={folder}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: folderIdx * 0.05 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <Folder className={cn("size-4", t.textMuted)} />
            <h2 className={cn("text-md font-medium", t.textMain)}>{folder}</h2>
          </div>
          <div className="space-y-2.5">
            {folderFacts.map((f) => (
              <Card
                key={f.id}
                className={cn(
                  t.glassPanel,
                  "p-4 transition-opacity",
                  f.superseded && "opacity-60",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className={cn("leading-relaxed", t.textMain)}>
                      {f.superseded && (
                        <span className={cn("text-xs mr-2", t.textMuted)}>
                          [устарело]
                        </span>
                      )}
                      {f.summary}
                    </p>
                    {f.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {f.tags.map((tag) => (
                          <span
                            key={tag}
                            className={cn(
                              "text-xs px-2 py-0.5 rounded-md",
                              t.glassSidebar,
                              t.textMuted,
                            )}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className={cn("text-xs mt-2", t.textMuted)}>
                      severity: {f.severity.toFixed(2)} · упомянуто{" "}
                      {f.times_mentioned} раз
                    </div>
                    {f.quotes.length > 0 && (
                      <details className="mt-2">
                        <summary
                          className={cn("text-xs cursor-pointer", t.textMuted)}
                        >
                          Цитаты ({f.quotes.length})
                        </summary>
                        <ul className={cn("mt-2 space-y-1 text-sm italic", t.textMain)}>
                          {f.quotes.map((q, i) => (
                            <li key={i}>«{q.text}»</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteFact(f.id)}
                    aria-label="Удалить этот факт"
                    className="text-crisis-500 hover:bg-crisis-500/10"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </motion.section>
      ))}

      <Card className={cn(t.glassPanel, "p-4 mt-6 border-crisis-500/20")}>
        <div className="flex items-start gap-3">
          <div className="size-9 rounded-full bg-crisis-500/15 text-crisis-500 flex items-center justify-center shrink-0">
            <ShieldAlert className="size-4" />
          </div>
          <div className="flex-1">
            <h3 className={cn("font-medium mb-1", t.textMain)}>
              Удалить всё досье
            </h3>
            <p className={cn("text-xs mb-3", t.textMuted)}>
              После удаления Кайрос забудет всё, что знал о тебе. Это нельзя
              отменить.
            </p>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleWipeAll}
              disabled={isWiping}
            >
              {isWiping ? "Удаляю..." : "Удалить всё досье"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd d:/Kairos/frontend && npm run type-check
```

Expected: без ошибок.

- [ ] **Step 3: Commit**

```bash
cd d:/Kairos && git add frontend/components/Dossier/DossierView.tsx && git commit -m "refactor(frontend): restyle DossierView with glass cards and motion"
```

---

### Task 6.2: `app/profile/page.tsx` — убрать старую шапку

**Files:**
- Modify: `d:/Kairos/frontend/app/profile/page.tsx`

- [ ] **Step 1: Полная замена**

```tsx
"use client";

import DossierView from "@/components/Dossier/DossierView";
import { useSession } from "@/hooks/useSession";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/lib/theme-tokens";

/**
 * Страница профиля.
 *
 * Шапка убрана: возврат в чат — через клик по аватару в RightDock.
 * Содержимое: DossierView — что Кайрос помнит о пользователе.
 */
export default function ProfilePage() {
  const { guestId } = useSession();
  const t = useThemeTokens();

  if (!guestId) {
    return (
      <div className={cn("max-w-3xl mx-auto p-4", t.textMuted)}>
        Подожди, загружаю профиль...
      </div>
    );
  }

  return (
    <div className="flex-1 w-full overflow-y-auto custom-scrollbar p-4 sm:p-6 lg:p-12 md:pr-[260px] lg:pr-[280px]">
      <DossierView guestId={guestId} />
    </div>
  );
}
```

- [ ] **Step 2: Запустить dev и проверить**

```bash
cd d:/Kairos/frontend && npm run dev
```

Открой `/profile`. Expected:
- Тот же фон и сайдбар
- Аватар в RightDock подсвечен (ты на странице профиля)
- Клик на аватар вернёт в чат
- Досье читается корректно в обеих темах
- Прерви dev

- [ ] **Step 3: Type-check + lint**

```bash
cd d:/Kairos/frontend && npm run type-check && npm run lint
```

Expected: без ошибок.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/app/profile/page.tsx && git commit -m "refactor(frontend): remove old profile page header (RightDock handles it now)"
```

---

**Phase 6 Checkpoint:**
- Профиль = досье в новом стиле, всё работает (fetch / delete / wipe)
- Аватар в RightDock — единая точка перехода между чатом и профилем
- Никакой старой шапки `← Вернуться в чат` нет
- ФЗ-152 «право на удаление» сохранено: «Удалить всё досье» работает

---

## Phase 7: Страница настроек (минимальная)

Цель: создать страницу `/settings` с переключателем темы и выбором обоев. Никаких других настроек на MVP — только эти две.

### Task 7.1: `app/settings/page.tsx`

**Files:**
- Create: `d:/Kairos/frontend/app/settings/page.tsx`

- [ ] **Step 1: Создать файл**

```tsx
"use client";

import Image from "next/image";
import { motion } from "motion/react";
import { Check, Moon, Settings as SettingsIcon, Sun } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";
import { useThemeTokens } from "@/lib/theme-tokens";
import { useWallpaper } from "@/hooks/useWallpaper";
import { WALLPAPERS } from "@/lib/wallpapers";

/**
 * Минимальная страница настроек: тема + обои.
 *
 * Полные настройки (уведомления, режим тишины, профиль заботы,
 * стиль общения) — после MVP, в отдельной сессии.
 */
export default function SettingsPage() {
  const t = useThemeTokens();
  const { isDark, setTheme } = useTheme();
  const { wallpaperId, setWallpaperId } = useWallpaper();

  return (
    <div className="flex-1 w-full overflow-y-auto custom-scrollbar p-4 sm:p-6 lg:p-12 md:pr-[260px] lg:pr-[280px]">
      <div className="max-w-3xl mx-auto space-y-8 pb-10">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <div
            className={cn(
              "size-12 rounded-2xl flex items-center justify-center shadow-lg backdrop-blur-xl border",
              t.glassSidebar,
              t.textMain,
            )}
          >
            <SettingsIcon className="size-6" />
          </div>
          <div>
            <h1 className={cn("text-2xl font-semibold tracking-tight", t.textMain)}>
              Настройки
            </h1>
            <p className={cn("text-sm mt-1", t.textMuted)}>
              Тема и обои. Остальные настройки появятся позже.
            </p>
          </div>
        </motion.div>

        {/* Тема */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <Card className={cn(t.glassPanel, "p-5")}>
            <h2 className={cn("font-medium mb-3", t.textMain)}>Тема</h2>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                onClick={() => setTheme("light")}
                className={cn(
                  "flex-1 gap-2",
                  t.btnHover,
                  !isDark
                    ? "bg-white/40 dark:bg-white/15 ring-2 ring-accent-400"
                    : "",
                )}
              >
                <Sun className="size-4" /> Светлая
              </Button>
              <Button
                variant="ghost"
                onClick={() => setTheme("dark")}
                className={cn(
                  "flex-1 gap-2",
                  t.btnHover,
                  isDark
                    ? "bg-white/15 ring-2 ring-accent-400"
                    : "",
                )}
              >
                <Moon className="size-4" /> Тёмная
              </Button>
            </div>
          </Card>
        </motion.div>

        {/* Обои */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className={cn(t.glassPanel, "p-5")}>
            <h2 className={cn("font-medium mb-3", t.textMain)}>Обои</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {WALLPAPERS.map((wp) => {
                const isActive = wallpaperId === wp.id;
                return (
                  <button
                    key={wp.id}
                    type="button"
                    onClick={() => setWallpaperId(wp.id)}
                    aria-label={`Выбрать обои "${wp.label}"`}
                    aria-pressed={isActive}
                    className={cn(
                      "relative aspect-video rounded-xl overflow-hidden border-2 transition-all duration-300 group",
                      isActive
                        ? "border-accent-400 shadow-[0_0_15px_rgba(125,179,194,0.5)]"
                        : "border-transparent hover:border-white/50",
                    )}
                  >
                    <Image
                      src={wp.thumbSrc}
                      alt={wp.label}
                      fill
                      sizes="(max-width: 640px) 50vw, 25vw"
                      className="object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                    {isActive && (
                      <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                        <div className="bg-accent-500 text-white rounded-full p-1.5 shadow-lg">
                          <Check className="size-5" />
                        </div>
                      </div>
                    )}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                      <span className="text-xs text-white font-medium">
                        {wp.label}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Запустить dev и проверить**

```bash
cd d:/Kairos/frontend && npm run dev
```

Открой `/settings`. Expected:
- Кнопка settings в FloatingButtons подсвечена
- Можно выбрать тему — переключение мгновенное
- Можно выбрать обои — фон меняется в реальном времени
- Тосты появляются (если хочешь — добавь `toast.success("Настройки сохранены")` в обработчики)
- Прерви dev

- [ ] **Step 3: Type-check + lint**

```bash
cd d:/Kairos/frontend && npm run type-check && npm run lint
```

Expected: без ошибок.

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos && git add frontend/app/settings/page.tsx && git commit -m "feat(frontend): add /settings page with theme and wallpaper picker"
```

---

**Phase 7 Checkpoint:**
- Страница `/settings` существует и работает
- Тема переключается через две кнопки + сохраняется в localStorage
- Обои выбираются из 4 локальных JPG, фон меняется live
- Никаких внешних URL, никакой записи в БД (всё через localStorage)
- FloatingButton settings подсвечивается на этой странице

---

## Phase 8: Финальный полиш и проверки

Цель: финальный проход — accessibility, Lighthouse, проверка кризисных fallback-ов и обновление PROGRESS.md.

### Task 8.1: Lighthouse audit

- [ ] **Step 1: Production build**

```bash
cd d:/Kairos/frontend && npm run build && npm run start
```

Expected: build проходит без ошибок. Сервер слушает на `:3000`.

- [ ] **Step 2: Lighthouse в Chrome DevTools**

Открой `http://localhost:3000/chat`, DevTools → Lighthouse → Mobile → "Analyze page load".

Expected (целевые числа):
- Performance: ≥ 80
- Accessibility: ≥ 90
- Best Practices: ≥ 90
- SEO: ≥ 80

Если что-то ниже — открой issues:
- Низкий Performance — проверь bundle size (`du -sh .next/static`), смотри что тяжёлое в .next/analyze
- Низкий a11y — Lighthouse покажет конкретные нарушения (часто — отсутствие `aria-label` или контраст)

- [ ] **Step 3: Записать результаты в plan-файл (опционально, но полезно)**

В корне репо создай (или обнови) `docs/superpowers/specs/2026-05-06-frontend-figma-redesign-design.md` секцию "Audit Results" с числами.

- [ ] **Step 4: Прерви prod-сервер**

Ctrl+C.

- [ ] **Step 5: Если показатели ок — commit (пустой) для отметки**

```bash
cd d:/Kairos && git commit --allow-empty -m "test(frontend): Lighthouse audit passed (Phase 8 checkpoint)"
```

---

### Task 8.2: Accessibility audit

- [ ] **Step 1: Включи `prefers-reduced-motion: reduce` в DevTools (Rendering tab)**

Открой `/chat`. Expected: анимации не пульсируют, motion-эффекты заморожены, длительность переходов ≈ 0.

- [ ] **Step 2: Tab-навигация**

Закрой сайдбар. Сделай Tab несколько раз. Expected: фокус последовательно проходит по:
1. Кнопка раскрытия сайдбара
2. Кнопка settings
3. Кнопка тоггла темы
4. Аватар (ссылка на профиль)
5. SOS-кнопка
6. Поле ввода
7. Кнопка отправки

Если что-то пропущено или порядок странный — поправь `tabindex` или порядок DOM.

- [ ] **Step 3: ESC из модалок**

Открой CrisisPanel. Нажми ESC. Expected: модалка закрывается. Открой её ещё раз и кликни вне — тоже закрывается. То же для RenameChatDialog.

- [ ] **Step 4: ScreenReader-друзья**

Включи macOS VoiceOver или NVDA на Windows. Прогони чат. Expected: все интерактивные элементы озвучены с понятной меткой.

- [ ] **Step 5: Контрастность (визуально)**

Если есть подозрение — запусти axe-core (Chrome extension) и пройди проверку.

- [ ] **Step 6: Commit (если правок не было — пустой)**

```bash
cd d:/Kairos && git commit --allow-empty -m "test(frontend): a11y audit passed (Phase 8 checkpoint)"
```

---

### Task 8.3: Crisis fallback test

Финальная проверка что fallback (когда LLM недоступен) не ломает UI.

- [ ] **Step 1: Останови backend**

Если бэкенд запущен — `Ctrl+C`.

- [ ] **Step 2: Запусти только фронт**

```bash
cd d:/Kairos/frontend && npm run dev
```

- [ ] **Step 3: Напиши сообщение**

Expected:
- В чате появляется error-bar «⚠️ Нет связи с сервером. Проверь интернет.»
- SOS-кнопка остаётся нажимаемой → CrisisPanel открывается с DEFAULT_CONTACTS (статика, не из API)
- Все номера в DEFAULT_CONTACTS кликабельны как `tel:`

Это критическое требование: **даже если бэкенд лежит, экстренные контакты должны быть доступны**. Если SOS не срабатывает или DEFAULT_CONTACTS не показываются — это blocker, разберись почему.

- [ ] **Step 4: Прерви dev**

- [ ] **Step 5: Commit (если правок не было)**

```bash
cd d:/Kairos && git commit --allow-empty -m "test(frontend): backend-down crisis fallback verified (Phase 8 checkpoint)"
```

---

### Task 8.4: Cross-browser smoke

- [ ] **Step 1: Запусти dev, открой в Chrome / Firefox / Safari (если есть macOS)**

Проверь по порядку:
- Фон рендерится
- Тема переключается
- Чат работает (отправь тестовое сообщение)
- Сайдбар открывается/закрывается
- На мобильном viewport (DevTools responsive mode, iPhone SE) — сайдбар закрыт по умолчанию, всё помещается, SOS виден

- [ ] **Step 2: Firefox-специфика**

Firefox строже к `aria-modal` — проверь что CrisisPanel читается screen reader-ом.

- [ ] **Step 3: Commit (отметка)**

```bash
cd d:/Kairos && git commit --allow-empty -m "test(frontend): cross-browser smoke verified"
```

---

### Task 8.5: Обновить PROGRESS.md и CLAUDE.md

**Files:**
- Modify: `d:/Kairos/PROGRESS.md`
- Modify: `d:/Kairos/CLAUDE.md`

- [ ] **Step 1: В PROGRESS.md добавить запись (или обновить существующий блок про фронтенд)**

Найди блок про frontend (вероятно Блок 7+ или подобный) и добавь под ним sub-секцию:

```md
### Сессия 19 (2026-05-06): Figma-based redesign

✅ Готово:
- Glassmorphism + dark/light тема (auto-detect 21–7)
- Сайдбар сессий + новый разговор + переименование
- RightDock: тема, аватар, TipCard, SOS
- ChatContainer переписан с motion-анимациями, EmptyState
- Кризисные компоненты переодеты, поведение сохранено
- /settings: тема + обои
- Локальные wallpapers (4 JPG), zero внешних CDN
- Lighthouse mobile ≥ 80, a11y ≥ 90

📂 Документы:
- spec: `docs/superpowers/specs/2026-05-06-frontend-figma-redesign-design.md`
- plan: `docs/superpowers/plans/2026-05-06-frontend-figma-redesign.md`
```

- [ ] **Step 2: В CLAUDE.md в раздел «История ключевых решений» добавить Сессию 19**

В CLAUDE.md, секция «История ключевых решений» (после Сессии 18):

```md
**Сессия 19** (Май 2026): Frontend redesign по черновику Figma Make. Ключевые решения:
- Visual: glassmorphism + dark/light тема + сайдбар сессий + плавающие элементы
- Stack: остаёмся на Next.js 16 + Tailwind v3 + Dexie. Добавлены motion, lucide, sonner, radix (avatar+dialog+slot), CVA, clsx+tailwind-merge.
- ФЗ-152: все wallpapers локально в /public/wallpapers/ (никаких Unsplash/GCS на runtime).
- Тема: auto-detect 21:00–07:00 → dark при первом визите, дальше выбор пользователя.
- Сайдбар: гибрид single+multi-chat. Один активный чат по умолчанию, кнопка «+» для новой сессии. На мобиле закрыт. Источник списка — Dexie (бэкенд эндпоинтов /api/sessions пока нет).
- Кризис: автооткрытие CrisisPanel при immediate сохранено. Никаких новых дополнительных манипуляций UI в кризисе.
- EmptyState: одно приветственное сообщение вместо карточек-затравок.
- Figma Files (D:/Figma Files/) оставлен как архивный референс — все правки в `frontend/`.
```

- [ ] **Step 3: Commit обновления документации**

```bash
cd d:/Kairos && git add PROGRESS.md CLAUDE.md && git commit -m "docs: update PROGRESS.md and CLAUDE.md for Session 19 (frontend redesign)"
```

---

### Task 8.6: Финальный smoke test и pull request preview

- [ ] **Step 1: Чистая сборка**

```bash
cd d:/Kairos/frontend && rm -rf .next && npm run build
```

Expected: build успешен, никаких warnings о deprecated/missing.

- [ ] **Step 2: Запусти prod**

```bash
cd d:/Kairos/frontend && npm run start
```

Expected: сервер на :3000 работает. Открой `/chat` — должно быть всё ок.

- [ ] **Step 3: Прогони сценарии user journey**

1. Первый визит (incognito): авто-тёмная тема (если ночь) или светлая (день) → EmptyState
2. Напиши сообщение → ответ бота, появляется в сайдбаре первая беседа
3. Создай новую беседу через «+» → пустой EmptyState, в сайдбаре две беседы
4. Переключись на первую → сообщения из неё
5. ПКМ на беседу → переименуй → название обновилось
6. Переключи тему → всё в новой палитре
7. Открой /profile → досье читается
8. Открой /settings → выбери другие обои → фон сменился

- [ ] **Step 4: Прерви prod-сервер**

- [ ] **Step 5: Финальный commit (отметка)**

```bash
cd d:/Kairos && git commit --allow-empty -m "feat(frontend): Figma redesign complete (Phase 8 done)"
```

---

**Phase 8 Checkpoint (финальный):**
- Lighthouse mobile ≥ 80 (Performance), ≥ 90 (a11y, Best Practices), ≥ 80 (SEO)
- Accessibility: keyboard nav, prefers-reduced-motion, ESC, screen reader — всё работает
- Backend-down: SOS + DEFAULT_CONTACTS остаются доступны
- Cross-browser: Chrome, Firefox, Safari, mobile viewport — рендерится корректно
- PROGRESS.md и CLAUDE.md обновлены, Сессия 19 задокументирована
- Production build проходит чисто

---

## Готово!

После всех 8 фаз frontend полностью переехал на новый дизайн с сохранением всей кризисной логики, perception layer интеграции и совместимости с ФЗ-152.

**Если что-то не сработает на одном из шагов** — не двигайся дальше «через». Открой issue (или comment в плане), разберись, потом продолжай. Это медицинский продукт; неоткатанная регрессия в кризисном модуле может стоить кому-то жизни.

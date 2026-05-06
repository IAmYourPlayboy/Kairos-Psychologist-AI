# Редизайн фронтенда Кайроса по черновику Figma Make: дизайн

> **Версия**: 1.0
> **Дата**: 2026-05-06 (Сессия 19)
> **Статус**: дизайн утверждён пользователем, ждёт review перед передачей в writing-plans
> **Заменяет**: текущий минималистичный фронтенд (`frontend/app/`, `frontend/components/Chat`) на визуально проработанный с glassmorphism, тёмной/светлой темой, сайдбаром истории сессий и плавающими элементами

---

## 1. Зачем

Пользователь сделал черновик фронтенда в Figma Make (Gemini 3.1 Pro) и хочет использовать его как визуальную базу для проекта. Черновик лежит в `D:/Figma Files/` и **остаётся неизменным** как архивный референс.

Черновик содержит сильные визуальные находки:

- Glassmorphism + фоновое изображение — ощущение «присутствия», а не клинического приложения. Подходит аудитории в дистрессе.
- Тёмная/светлая темы через единый набор токенов (`useThemeTokens`) — палитра вынесена в одну функцию, переключение чистое.
- Чат-интерфейс с асимметричными пузырями, контекстным меню на сообщениях, закладками — паттерны мессенджеров, привычно.
- Сайдбар с историей сессий + плавающие кнопки настроек/тоггла — паттерн ChatGPT, понятный.
- Мягкие пружинные анимации через `motion/react` — оживляют интерфейс, не отвлекая.

**Но** черновик нельзя перенести «как есть» по нескольким критическим причинам:

1. **Стек несовместим**: Vite + React Router 7 vs наш Next.js 16 App Router; Tailwind v4 vs наш v3.
2. **Логика противоречит ядру продукта**:
   - `Auth` обязателен до входа в чат → у нас принцип «кризис = ноль регистрации».
   - Шаблонный ответ бота `«Я понимаю ваши чувства»` → это **запрещённая фраза №1** в `forbidden_phrases.py`.
   - Нет SOS-кнопки и кризисного модуля — самой важной части продукта.
   - Нет дисклеймера / согласия на спецкатегорию ПДн (требование ФЗ-152).
   - Голосовой ввод и attachments — лишний функционал на MVP.
3. **Внешние зависимости нарушают ФЗ-152**: фоновые картинки с Unsplash, видео-обои с Google Cloud Storage — передача данных пользователя на иностранные серверы при загрузке.
4. **CSS-hell в `Root.tsx`**: одна строка с 50+ конфликтующими утилитами Tailwind.
5. **Бандл-балласт**: MUI (~280 KB) подключён, но не используется; десятки `@radix-ui/*` пакетов; `react-dnd`, `react-slick`, `recharts`, `embla` и пр. — всё это не нужно.

**Цель**: взять визуальные сильные стороны черновика (стиль, палитра, layout, анимации) и встроить их в наш текущий фронтенд (`frontend/`), сохранив всю кризисную логику, perception layer (Сессия 18), data flywheel и совместимость с ФЗ-152. Черновик не трогаем — пишем редизайн прямо в `frontend/`, где уже подключён бэкенд через `useChat`.

## 2. Что мы строим

Полный визуальный редизайн фронтенда без потери функциональности. Единственный новый функционал — мульти-сессии и переключение темы. Всё остальное — это переодевание существующих компонентов в новую визуальную систему.

```
┌──────────────────────────────────────────────────────────────────┐
│                       AppShell (новый layout)                    │
│  ┌──────────┐                                          ┌──────┐  │
│  │  Background (фоновое фото + темовый overlay)        │      │  │
│  │  ┌──────┐  ┌────────────────────────────────┐  ┌──┐ │      │  │
│  │  │Side- │  │  Чат / Профиль / Настройки    │  │  │ │      │  │
│  │  │bar   │  │  (через slot children)         │  │R │ │      │  │
│  │  │      │  │                                │  │i │ │      │  │
│  │  │список│  │  - ChatContainer               │  │g │ │      │  │
│  │  │сессий│  │  - DossierView (на /profile)   │  │h │ │      │  │
│  │  │      │  │  - SettingsView (на /settings) │  │t │ │      │  │
│  │  │+ Plus│  │                                │  │  │ │      │  │
│  │  └──────┘  └────────────────────────────────┘  │D │ │      │  │
│  │   ↑                                            │o │ │      │  │
│  │   FloatingButtons (Settings + Toggle)          │c │ │      │  │
│  │                                                │k │ │      │  │
│  │                              Theme Toggle  ────┤  │ │      │  │
│  │                              Avatar       ────┤  │ │      │  │
│  │                              SOS Button   ────┤  │ │      │  │
│  │                              TipCard      ────┘  │ │      │  │
│  │                                                  │ │      │  │
│  └──────────┘                                          └──────┘  │
└──────────────────────────────────────────────────────────────────┘
```

Архитектурно это:

- `AppShell` — корневой layout со слоями: фон → сайдбар → центральный контент → правый dock с плавающими элементами.
- `Background` — фоновое изображение + полупрозрачный overlay по теме. Картинки локально в `/public/wallpapers/`.
- `Sidebar` — список сессий + кнопка «новый разговор». На мобильных закрыт по умолчанию.
- `RightDock` — стек плавающих элементов в правом верхнем углу: тоггл темы, аватар (ведёт на /profile), **SOS-кнопка**, плавающая карточка «Совет дня».
- `FloatingButtons` — две плавающие иконки в левом нижнем углу: «настройки» и «свернуть/развернуть сайдбар».
- Контентная область — рендерит дочернюю страницу (`/chat`, `/profile`, `/settings`).

Кризисная логика (`SOSButton`, `CrisisPanel`, `CrisisInlineCard`), perception (`useChat`), feedback (`MessageFeedback`, `SessionFeedback`), досье (`DossierView`) — **их API и поведение не меняются**. Меняется только обёртка, классы, анимация.

### Принципы интеграции

1. **Логика бэкенда — священна**. Все запросы к `/api/chat`, `/api/feedback`, `/api/dossier` идут через существующие хуки и клиенты. Никаких клиентских имитаций ответов бота, никаких локальных шаблонных диалогов.
2. **Кризисный модуль не упрощается**. SOS-кнопка всегда доступна, автооткрытие `CrisisPanel` при `crisis_level === "immediate"` сохраняется.
3. **Ноль регистрации для входа в чат**. Гость заходит → сразу пишет.
4. **Тёплая тёмная/светлая тема**. По первому визиту автодетект по локальному времени (21:00–07:00 → тёмная, иначе светлая). Дальше — выбор пользователя через тоггл, persist в localStorage.
5. **ФЗ-152**: все ассеты (картинки, шрифты, видео) — локально на нашем сервере или через `next/font/google` (он проксирует). Никаких прямых ссылок на иностранные CDN.
6. **`prefers-reduced-motion`** — уважаем. Кому пружинные анимации триггерят тревожность, тому статичный UI.

## 3. Стек и зависимости

### Что остаётся

| Пакет                     | Версия       | Зачем                                           |
| ------------------------- | ------------ | ----------------------------------------------- |
| `next`                    | ^16.2.4      | App Router, SSR, file-based routing             |
| `react` + `react-dom`     | ^18.3.1      | UI                                              |
| `dexie`                   | ^4.0.10      | Локальный кэш сообщений (offline + sync)        |
| `tailwindcss`             | ^3.4.13      | Утилитарный CSS — стабильно работает с Next 16 |
| `typescript`              | ^5.6.3       | Strict mode                                     |

### Что добавляем

| Пакет                       | Версия | Размер (gz) | Зачем                                                              |
| --------------------------- | ------ | ----------- | ------------------------------------------------------------------ |
| `motion`                    | ^12.x  | ~32 KB      | Анимации (`AnimatePresence`, спринги). Замена `framer-motion`.     |
| `lucide-react`              | ^0.487 | tree-shake  | Иконки. Каждая иконка ~1 KB.                                       |
| `sonner`                    | ^2.x   | ~5 KB       | Тосты («чат удалён», «обои обновлены»).                            |
| `clsx`                      | ^2.x   | <1 KB       | Условные классы.                                                   |
| `tailwind-merge`            | ^3.x   | ~3 KB       | Резолв конфликтов Tailwind классов (для нашего `cn()`).            |
| `class-variance-authority`  | ^0.7   | ~2 KB       | CVA для `ui/Button` и подобных вариантных компонентов.             |
| `@radix-ui/react-avatar`    | ^1.x   | ~2 KB       | Аватар с fallback                                                  |
| `@radix-ui/react-dialog`    | ^1.x   | ~6 KB       | Модалки (rename chat, переписать `CrisisPanel`)                    |
| `@radix-ui/react-slot`      | ^1.x   | <1 KB       | Для CVA-компонентов (asChild)                                      |

**Итого добавочного веса:** ~50 KB gz. Lighthouse mobile должен остаться > 80.

### Что НЕ добавляем (хотя есть в Figma)

- ❌ `@mui/material`, `@mui/icons-material`, `@emotion/*` — MUI подключён в Figma но не используется ни в одном компоненте. ~280 KB балласта.
- ❌ `react-router` — несовместим с Next App Router.
- ❌ `next-themes` — пишем `useTheme` на 30 строк, библиотека не нужна.
- ❌ `canvas-confetti`, `react-dnd`, `react-slick`, `react-day-picker`, `recharts`, `embla-carousel-react`, `vaul`, `cmdk`, `input-otp`, `react-resizable-panels`, `react-responsive-masonry`, `tw-animate-css`, `react-popper`, `react-hook-form`, `date-fns` — ничего из этого не нужно для MVP.
- ❌ Большинство `@radix-ui/*` пакетов из Figma — добавляем только два, которые реально нужны (avatar, dialog). Остальные (accordion, alert-dialog, checkbox, popover и т. д.) — точечно по мере появления реальной потребности.

### Шрифт

Golos Text 400/500/600/700 через `next/font/google` с `display: 'swap'`. Уже подключён в `app/layout.tsx`. Fallback: `system-ui, sans-serif`.

## 4. Палитра и токены темы

Используем существующую палитру Кайроса (`warm`, `accent`, `crisis` из `tailwind.config.ts`) — **не выкидываем**. Расширяем её: добавляем нейтральную тёмную базу для тёмной темы, glassmorphism токены, и переносим логику переключения из Figma `useThemeTokens`.

### 4.1. Расширение `tailwind.config.ts`

Сохраняем `warm`, `accent`, `crisis` как есть. Добавляем:

- `neutral.{50..900}` — нейтрально-серая шкала для тёмной темы. (`neutral-950: #0a0a0a` — самый глубокий фон, `neutral-50: #fafafa` — на случай инверсии). Можно использовать стандартную Tailwind `neutral` или явно прописать.
- Цвет `amber` для tip-карточки — стандартная Tailwind палитра уже включает.

В `theme.extend.animation` и `keyframes` — оставляем `fade-in` и `pulse-slow`, добавляем больше при необходимости.

### 4.2. Включение dark mode в Tailwind

В `tailwind.config.ts` добавляем `darkMode: "class"` — переключение через класс `.dark` на `<html>`. В `globals.css` добавляем минимум:

```css
.dark body {
  @apply bg-neutral-950 text-white;
}
```

Этого достаточно. Все остальные dark/light варианты приходят через `useThemeTokens` (см. ниже) — это подход «темовые классы через хук», который Figma уже использует и который мы переносим 1-в-1.

### 4.3. Хук `useThemeTokens`

Порт логики из Figma `AppContext.tsx::useThemeTokens` 1-в-1 в `hooks/useThemeTokens.ts`. Это просто маппинг булевого флага `isDark` на готовые Tailwind-классы:

```ts
// frontend/hooks/useThemeTokens.ts
import { useTheme } from "@/hooks/useTheme";

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
      ? "bg-white/10 border-white/20 focus-within:bg-white/15 focus-within:ring-white/30"
      : "bg-white border-warm-200 focus-within:ring-accent-400/30 shadow-xl",

    floatingBtn: isDark
      ? "bg-white/10 hover:bg-white/20 text-white shadow-[0_0_15px_rgba(0,0,0,0.5)] border border-white/20"
      : "bg-white/95 hover:bg-warm-50 text-warm-900 shadow-md border border-warm-200",

    tipCard: isDark
      ? "bg-gradient-to-br from-amber-500/20 to-orange-500/10 border-amber-400/30 text-amber-50"
      : "bg-gradient-to-br from-amber-50 to-orange-100/80 border-amber-300/60 text-amber-900",
  };
}
```

Отличие от Figma: вместо чистого `slate-*` используем нашу `warm-*` шкалу для светлой темы — продолжаем «тёплое» направление, заданное в проекте.

### 4.4. Хук `useTheme`

```ts
// frontend/hooks/useTheme.ts
"use client";
import { useEffect, useState } from "react";

const STORAGE_KEY = "kairos-theme";

function detectInitialTheme(): "dark" | "light" {
  // Если пользователь уже выбирал тему — берём её
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "dark" || saved === "light") return saved;
  }
  // Иначе детектим по локальному времени: 21:00-06:59 → тёмная
  const hour = new Date().getHours();
  return hour >= 21 || hour < 7 ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">("light"); // SSR fallback
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const initial = detectInitialTheme();
    setTheme(initial);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme, mounted]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));
  return { theme, isDark: theme === "dark", toggle, mounted };
}
```

Важно: SSR-flash-проблему решаем рендером `document.documentElement.classList` через inline-скрипт в `<head>` (см. секцию 5.1).

### 4.5. Wallpaper (фоновое изображение)

4 статичных JPG локально в `/public/wallpapers/`:

- `forest.jpg` — лес/деревья (default)
- `mountains.jpg` — горы
- `ocean.jpg` — океан
- `stars.jpg` — звёздное небо

Размер каждого — до 300 KB после сжатия (через `next/image` с `priority` для default). Видео-обои **не делаем** на MVP — тяжело для мобильных, лишний бандл, нарушение ФЗ-152 при подгрузке с CDN.

Хранится в Dexie как `app_settings` запись — `{ wallpaperId: 'forest' }`. Меняется в `/settings`.

## 5. Структура файлов

```
frontend/
├── app/
│   ├── layout.tsx                    [REWRITE: ThemeScript + AppShell]
│   ├── page.tsx                      [KEEP: redirect /chat]
│   ├── globals.css                   [REWRITE: + dark, + scrollbar, + motion-reduce]
│   ├── chat/
│   │   └── page.tsx                  [RESTYLE: рендерит ChatContainer без своей шапки]
│   ├── profile/
│   │   └── page.tsx                  [RESTYLE: обёртка вокруг DossierView]
│   └── settings/
│       └── page.tsx                  [NEW: тема + обои]
│
├── components/
│   ├── Layout/                       [NEW directory]
│   │   ├── AppShell.tsx              [NEW] — корневой layout
│   │   ├── Background.tsx            [NEW] — фон + overlay
│   │   ├── Sidebar.tsx               [NEW] — список сессий
│   │   ├── FloatingButtons.tsx       [NEW] — settings + toggle
│   │   ├── RightDock.tsx             [NEW] — theme + avatar + SOS + tip
│   │   ├── ThemeToggle.tsx           [NEW]
│   │   ├── TipCard.tsx               [NEW] — статичные «советы дня»
│   │   ├── ThemeScript.tsx           [NEW] — inline-скрипт для anti-flash
│   │   └── RenameChatDialog.tsx      [NEW] — Radix Dialog
│   │
│   ├── Chat/
│   │   ├── ChatContainer.tsx         [REWRITE: без шапки, со стилями glassmorphism]
│   │   ├── EmptyState.tsx            [NEW] — приветственное сообщение
│   │   ├── MessageBubble.tsx         [RESTYLE: glassmorphism + асимметричные радиусы]
│   │   ├── InputArea.tsx             [REWRITE: glassmorphism, без attach-меню, без mic]
│   │   ├── TypingIndicator.tsx       [RESTYLE]
│   │   └── HumanTypingEffect.tsx     [KEEP]
│   │
│   ├── Crisis/
│   │   ├── SOSButton.tsx             [RESTYLE: glassmorphism + перенос в RightDock]
│   │   ├── CrisisPanel.tsx           [RESTYLE: Radix Dialog + glassmorphism]
│   │   └── CrisisInlineCard.tsx      [RESTYLE: стиль TipCard, но crisis-палитра]
│   │
│   ├── Dossier/
│   │   └── DossierView.tsx           [RESTYLE: обёртка glassmorphism + motion]
│   │
│   ├── Feedback/
│   │   ├── MessageFeedback.tsx       [RESTYLE: glassmorphism thumbs]
│   │   └── SessionFeedback.tsx       [RESTYLE]
│   │
│   └── ui/                           [NEW directory: shadcn-style примитивы]
│       ├── Button.tsx                [NEW] — CVA + Slot
│       ├── Card.tsx                  [NEW]
│       ├── Avatar.tsx                [NEW] — Radix Avatar
│       └── Dialog.tsx                [NEW] — Radix Dialog
│
├── hooks/
│   ├── useChat.ts                    [KEEP]
│   ├── useSession.ts                 [KEEP]
│   ├── useTheme.ts                   [NEW]
│   ├── useSidebar.ts                 [NEW] — open/closed + persist
│   └── useSessions.ts                [NEW] — список сессий из API + Dexie
│
├── lib/
│   ├── api.ts                        [KEEP, +getSessions(), +deleteSession(), +renameSession()]
│   ├── db.ts                         [KEEP, +тип SessionMeta, +listSessions()]
│   ├── types.ts                      [KEEP, +SessionMeta тип]
│   ├── useThemeTokens.ts             [NEW] — useThemeTokens
│   ├── cn.ts                         [NEW] — clsx + tailwind-merge
│   └── tips.ts                       [NEW] — массив статичных «советов дня»
│
└── public/
    └── wallpapers/                   [NEW] — 4 JPG
        ├── forest.jpg
        ├── mountains.jpg
        ├── ocean.jpg
        └── stars.jpg
```

### 5.1. Anti-flash скрипт

Чтобы при первом рендере не было «вспышки светлой темы» перед применением сохранённой/детектированной — в `<head>` встраиваем blocking inline-скрипт:

```tsx
// components/Layout/ThemeScript.tsx
export function ThemeScript() {
  const code = `
    (function() {
      try {
        var saved = localStorage.getItem('kairos-theme');
        var theme = saved;
        if (!theme) {
          var h = new Date().getHours();
          theme = (h >= 21 || h < 7) ? 'dark' : 'light';
        }
        if (theme === 'dark') document.documentElement.classList.add('dark');
      } catch(e) {}
    })();
  `;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
```

Подключается в `<head>` как первый ребёнок до контента.

## 6. Поведение и поток данных

### 6.1. Главный путь: гость пишет в чат

```
[гость открывает /]
    ↓
redirect → /chat
    ↓
AppShell mount:
  - useTheme: detectInitialTheme() → light/dark
  - useSession: получает/создаёт guest_id (localStorage) и session_id (новый UUID)
  - useSessions: загружает список сессий (GET /api/sessions?guest_id=X)
    ↓
ChatContainer.tsx:
  - useChat загружает messages из Dexie (по session_id)
  - если messages пуст → <EmptyState /> с приветственным сообщением
  - если есть → лента сообщений
    ↓
[гость пишет «мне страшно»]
    ↓
useChat.sendMessage:
  - оптимистично добавляет в messages
  - POST /api/chat
    ↓
[бэкенд: PerceptionPipeline → MessageAnalyzer LLM → main LLM]
    ↓
{ message, crisis_level, crisis_contacts, ... }
    ↓
ChatContainer рендерит:
  - <MessageBubble role="assistant">
  - если crisis_level: <CrisisInlineCard>
  - <MessageFeedback>
    ↓
[если crisis_level === "immediate"]
    ↓
ChatContainer auto-открывает <CrisisPanel> (без участия пользователя)
SOSButton переключается в стиль "immediate" (быстрая пульсация)
```

### 6.2. Мульти-сессии

Гибрид с уклоном в single-chat:

- Default: при заходе пользователь сразу в **активной сессии** (последняя или новая если первый раз).
- В сайдбаре — список всех сессий пользователя/гостя.
- Кнопка «+» в верху сайдбара — создать новую сессию. Текущая сессия не уничтожается, остаётся в списке.
- Клик на сессию — переключаемся (load из Dexie / API).
- Контекстное меню на сессии — переименовать / удалить / поделиться. Удаление каскадно стирает сообщения сессии.

**Бэкенд эндпоинты (нужны новые):**

- `GET /api/sessions?guest_id=X[&user_id=Y]` → `[{ id, title, created_at, message_count, last_message_at }]`
- `PATCH /api/sessions/:id` → `{ title }` (переименование)
- `DELETE /api/sessions/:id` (каскадно сообщения)

**Это — новые эндпоинты на бэкенде.** В рамках этого спека на бэкенде они **не делаются**. Бэкенд-задача — отдельный блок PROGRESS.md (Блок ~16). Пока эндпоинты не появились:

- Сайдбар показывает только текущую сессию из Dexie.
- Заглушка: "История появится после первого разговора".
- Создание новой сессии работает (просто новый `session_id` в `useSession`).
- Переименование/удаление — только локально в Dexie, без сервера.

Это **временный downgrade** — фронтенд не блокируется ожиданием бэкенда. Когда эндпоинты появятся — `useSessions` подключается к ним без переписывания UI.

### 6.3. Auto-detect темы

Только при **первом** заходе (когда `localStorage.getItem('kairos-theme')` не задан):

- Локальное время 21:00–06:59 → `dark`
- Иначе → `light`

После первого изменения через `ThemeToggle` — выбор сохраняется в localStorage и автодетект больше не запускается. Это решение пользователя и оно перевешивает «время суток».

### 6.4. Кризис: визуальный режим

При `crisis_level === "immediate"`:

- `SOSButton` → яркий красный + быстрая пульсация (`animate-pulse`)
- Автоматически открывается `CrisisPanel` (как сейчас в `ChatContainer.tsx`)
- Дополнительно показывается `CrisisInlineCard` под ответом бота

Никаких дополнительных автоматических манипуляций UI (сворачивания сайдбара, изменения фона) не делаем — в кризисе любые неожиданные движения могут дезориентировать. Принцип: меньше движения — меньше путаницы.

При `crisis_level === "high"`:

- `SOSButton` → красный + медленная пульсация (`animate-pulse-slow`)
- `CrisisInlineCard` показывается под ответом бота
- Сайдбар не трогаем

При `elevated`:

- `SOSButton` → тёплый предупреждающий цвет
- Inline-карточки нет

При `normal`:

- `SOSButton` → нейтральный приглушённый стиль (как обычная иконка), но всё ещё видна

### 6.5. EmptyState (приветственное сообщение)

Заменяет Figma-карточки-затравки. Один блок:

```tsx
<div className="flex flex-col items-center justify-center text-center max-w-xl mx-auto py-12">
  <motion.div
    className={cn("size-16 rounded-full ... shadow-2xl", t.glassSidebar)}
    animate={{ y: [0, -8, 0] }}
    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
  >
    <Sparkles className="size-8" />
  </motion.div>
  <h2 className={cn("text-2xl md:text-3xl font-semibold mt-6 mb-4", t.textMain)}>
    Здесь можно говорить как есть
  </h2>
  <p className={cn("text-base leading-relaxed", t.textMuted)}>
    Я — Кайрос. Не психолог и не врач, но я рядом, если тебе тяжело.
    Расскажи что у тебя сейчас — постараюсь помочь. Если это срочно
    — нажми SOS в правом верхнем углу.
  </p>
</div>
```

Никаких кликабельных предложений-затравок. Это упрощает первый ввод: пользователь сам формулирует, что у него происходит.

## 7. Безопасность, ФЗ-152, accessibility

### 7.1. ФЗ-152 и приватность

- Все картинки фонов — локально в `/public/wallpapers/`. Никаких прямых ссылок на Unsplash, Google Cloud Storage, Pexels.
- Шрифт — через `next/font/google`, который проксирует через наш сервер (документировано Next.js).
- Иконки — через `lucide-react` (npm пакет, без внешних запросов).
- Ноль внешних трекеров, ноль аналитики на frontend на этом этапе.

### 7.2. Безопасность

- Никаких inline-скриптов кроме `ThemeScript` (контролируемое содержимое).
- Никакого `dangerouslySetInnerHTML` для пользовательского контента.
- Все ссылки `tel:` — только на проверенные номера из `crisis/contacts.py`.

### 7.3. Accessibility

- `aria-label` на всех интерактивных элементах без видимого текста (SOS, тоггл, аватар, кнопка attach, etc).
- `prefers-reduced-motion` уважается: в `globals.css` глобальный media query отключающий анимации > 200ms.
- Контрастность текста: проверка на каждом темовом токене. `text-white/60` на тёмном фоне → проверить через axe-core или Lighthouse.
- Focus rings видны: в Figma они вычищены, восстанавливаем — `focus-visible:ring-2 ring-accent-400 outline-none`.
- Esc закрывает все Radix Dialog'и и контекстные меню (Radix делает это автоматически).
- Клавиатурная навигация: Tab проходит по всем интерактивным элементам в логичном порядке.

### 7.4. Производительность

- `motion/react` импортируется только там где используется — tree-shaking активен.
- `Background.tsx` использует Next `<Image>` с `priority` для default-картинки.
- Bundle target: < 250 KB gz для первой загрузки `/chat`.
- Lighthouse mobile target: > 80 (Performance, Accessibility, Best Practices, SEO).

### 7.5. Деградация на старых устройствах

- `backdrop-filter: blur` тяжёлый на Android < 9 и старых iOS Safari. В CSS:
  ```css
  @supports not (backdrop-filter: blur(16px)) {
    .glass-fallback {
      background-color: rgb(var(--bg-base) / 0.85);
    }
  }
  ```
- Если `prefers-reduced-motion: reduce` → отключаем все `animate-*` классы и motion-эффекты.

## 8. Тестирование

После каждого этапа реализации (план будет в writing-plans):

1. **Кризисные сценарии** — `frontend/components/Crisis/` должен:
   - Открывать `CrisisPanel` автоматически при `immediate`
   - Показывать `CrisisInlineCard` при `high` и `immediate`
   - Менять стиль SOS-кнопки по уровню
   - Все номера кликабельны как `tel:`
2. **Чат основной поток** — отправка сообщения, получение ответа, оптимистичный UI, fallback при ошибке.
3. **Tема и persist** — переключение, сохранение, autodetect только в первый раз.
4. **Сайдбар** — открытие/закрытие, переключение между сессиями (когда эндпоинты появятся).
5. **Lighthouse** — > 80 mobile.
6. **`forbidden_phrases.py`** — никакой клиентской логики, имитирующей ответы бота.

Тесты UI через Playwright — отложено в этом спеке (отдельный блок PROGRESS.md, скилл `webapp-testing`).

## 9. Что НЕ делается в этом спеке

- ❌ Аутентификация (`/auth/login`, `/auth/register`) — Блок 13 PROGRESS.md.
- ❌ Голосовой ввод — Фаза 6.
- ❌ Прикрепление файлов — за пределами MVP.
- ❌ Мобильные приложения (Capacitor) — Фаза 8.
- ❌ Десктоп (Tauri) — Фаза 8.
- ❌ Подписки и оплата — Блок 24 PROGRESS.md.
- ❌ Бэкенд-эндпоинты для сессий — отдельный блок (предположительно Блок ~16 PROGRESS.md).
- ❌ Полные настройки (уведомления, режим тишины, профиль заботы и пр.) — после MVP. На MVP `/settings` имеет только тему + обои.
- ❌ Закладки на сообщениях («инсайты») — отдельный блок после MVP. Сейчас Profile показывает только досье.

## 10. Риски и митигации

| Риск                                                                | Митигация                                                                                          |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `backdrop-filter: blur` тормозит на старых мобильных                | Feature-detection через `@supports`, fallback на сплошной полупрозрачный цвет                      |
| Перенос ломает кризисный модуль                                     | Логика и API кризисных компонентов **не меняются**. Меняются только классы и обёртка               |
| `motion/react` тяжёлый                                              | Используем точечно, `AnimatePresence` только где реально нужен                                     |
| SSR-flash светлой темы перед применением сохранённой               | `ThemeScript` inline в `<head>` до контента                                                        |
| Голос/время устройства ненадёжен (часовые пояса, путешественники)   | Auto-detect только в первый раз; пользователь всегда может переключить вручную                     |
| Новые зависимости (radix, motion, sonner) увеличат bundle           | Tree-shaking + lazy imports там где возможно. Bundle target — мониторим                            |
| Сайдбар сессий зависит от эндпоинта `/api/sessions` (его пока нет)  | Заглушка «История появится после первого разговора», локальное Dexie до появления API              |
| Кто-то трогает Figma Files и портит референс                        | `D:/Figma Files/` декларативно read-only. Все правки идут в `frontend/`. Документировано в README. |
| Bundle превысит 250 KB                                              | Точечный аудит. CVA + clsx + tailwind-merge суммарно < 6 KB. Radix добавляем только нужное.         |

## 11. Итоговая визуальная схема

### 11.1. /chat (default)

```
┌──────────────────────────────────────────────────────────────────┐
│  [BG: forest.jpg + light overlay (0.25)]                          │
│                                                                   │
│  ┌─────────────────┐                                  ☀  👤  🆘  │
│  │ + Новый разговор│                                              │
│  │ ─────────────── │   ┌────────────────────────────┐    ┌────┐  │
│  │ • Тревожность   │   │      Здесь можно           │    │💡  │  │
│  │ • Утрата        │   │      говорить как есть     │    │Со- │  │
│  │ • Конфликт      │   │                            │    │вет │  │
│  │ ...             │   │      Я — Кайрос ...        │    │дня │  │
│  │                 │   │                            │    └────┘  │
│  │                 │   └────────────────────────────┘             │
│  │                 │                                              │
│  │                 │   ┌────────────────────────────┐             │
│  │                 │   │  ▌ напиши, что у тебя...  ↑│             │
│  │ ⚙  ◀            │   └────────────────────────────┘             │
│  └─────────────────┘   Это не замена врачу. 112, 8-800-...        │
└──────────────────────────────────────────────────────────────────┘
```

### 11.2. /chat активный диалог + кризис

```
┌──────────────────────────────────────────────────────────────────┐
│  [BG чуть темнее в кризисе]                                       │
│                                                                   │
│  ┌─────────────────┐                                  ☀  👤  🆘  │
│  │ + Новый разговор│                                       (red)  │
│  │ ─────────────── │   ┌──────────────────────────┐               │
│  │ • Тревожность ✓ │   │ Как ты? :( Расскажи     │               │
│  │   (active)      │   │  что происходит сейчас. │               │
│  │ • Утрата        │   └──────────────────────────┘               │
│  │ • Конфликт      │       ┌────────────────────────────┐         │
│  │                 │       │ мне очень страшно, не     │         │
│  │                 │       │  знаю что делать          │         │
│  │                 │       └────────────────────────────┘         │
│  │                 │   ┌──────────────────────────┐               │
│  │                 │   │ Слышу. Давай попробуем    │               │
│  │                 │   │  замедлиться вместе...    │               │
│  │                 │   └──────────────────────────┘               │
│  │                 │   ╔══════════════════════════╗               │
│  │                 │   ║ ⚠ Кризисные контакты:    ║               │
│  │                 │   ║   112  |  8-800-333-44-34║               │
│  │                 │   ╚══════════════════════════╝               │
│  │                 │   ┌────────────────────────────┐             │
│  │ ⚙  ◀            │   │  ▌ ...                   ↑│             │
│  └─────────────────┘   └────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

### 11.3. /profile (досье)

```
┌──────────────────────────────────────────────────────────────────┐
│  [BG]                                                             │
│                                                                   │
│  ┌─────────────────┐                                  ☀  👤  🆘  │
│  │                 │   ┌─────────────────────────────────┐        │
│  │  Sidebar        │   │  Что Кайрос помнит обо мне    │        │
│  │                 │   │  ───────────────────────────    │        │
│  │                 │   │                                 │        │
│  │                 │   │  📁 Семья                  →    │        │
│  │                 │   │  📁 Работа                 →    │        │
│  │                 │   │  📁 Эмоции / Состояние    →    │        │
│  │                 │   │  📁 Отношения              →    │        │
│  │                 │   │  ...                            │        │
│  │                 │   │                                 │        │
│  │                 │   │  [Удалить всё досье]            │        │
│  └─────────────────┘   └─────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

## 12. Готовность к реализации

После одобрения этого дизайна — переход в writing-plans skill, который разобьёт это на пошаговый план с phases:

- Phase 1: Зависимости + dark theme + tokens + shell skeleton
- Phase 2: Background + RightDock + ThemeToggle + ThemeScript
- Phase 3: Sidebar + Sessions hook + new-chat
- Phase 4: ChatContainer rewrite + EmptyState + MessageBubble restyle
- Phase 5: Crisis components restyle (SOSButton в RightDock, CrisisPanel через Radix Dialog)
- Phase 6: Profile/Dossier restyle
- Phase 7: Settings page (тема + обои)
- Phase 8: Финальный полиш + Lighthouse + a11y проверка

---

*Этот документ — спека редизайна, не план реализации. План — следующий шаг.*

*История правок:*

- *Сессия 19 (2026-05-06): создание спеки на основе черновика Figma Make + сильных сторон существующего фронтенда. Утверждены: гибрид single+multi-chat, приветственное сообщение вместо карточек-затравок, autodetect темы по локальному времени при первом визите.*

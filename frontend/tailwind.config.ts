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

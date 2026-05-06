import type { Config } from "tailwindcss";

/**
 * Tailwind конфигурация Кайроса.
 *
 * Палитра: тёплые тона, низкая яркость — сервис должен ощущаться спокойным
 * и поддерживающим, не «ярким и весёлым».
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
      colors: {
        // Тёплая нейтральная база (фон, текст)
        warm: {
          50: "#FAF7F2",
          100: "#F4EFE7",
          200: "#E8DFD0",
          300: "#D4C5AE",
          400: "#B8A488",
          500: "#9D886B",
          600: "#7E6D54",
          700: "#5F5240",
          800: "#3F362B",
          900: "#1F1B16",
        },
        // Акцент: спокойный синий (доверие, безопасность)
        accent: {
          50: "#EEF4F8",
          100: "#D6E3ED",
          200: "#AECEDB",
          300: "#7AB1C2",
          400: "#4D93A8",
          500: "#357588",
          600: "#28596A",
          700: "#1D414C",
          800: "#142B33",
          900: "#0B1719",
        },
        // Кризис: приглушённый красный (тревога, внимание — не паника)
        crisis: {
          50: "#FAF0EE",
          100: "#F4D9D4",
          200: "#E8B0A6",
          300: "#D9847A",
          400: "#C7574F",
          500: "#A53A36",
          600: "#7F2A29",
          700: "#5C1E1D",
          800: "#3E1414",
          900: "#1F0A0A",
        },
      },
      fontFamily: {
        // Golos Text — официальный шрифт российского правительства,
        // открытая лицензия, прекрасно читается.
        sans: ["var(--font-golos)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
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
    },
  },
  plugins: [],
};

export default config;

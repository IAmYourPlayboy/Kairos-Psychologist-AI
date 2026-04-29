"use client";

import { useEffect, useState, useRef } from "react";

interface HumanTypingEffectProps {
  text: string;
  onComplete?: () => void;
  speed?: "slow" | "normal" | "fast";
}

/**
 * Компонент для имитации "живого" человеческого общения
 *
 * Особенности:
 * - Динамические паузы после знаков препинания
 * - Длинные паузы после многоточия (раздумье)
 * - Быстрая печать в середине предложения
 * - Замедление перед важными фразами
 */
export default function HumanTypingEffect({
  text,
  onComplete,
  speed = "normal",
}: HumanTypingEffectProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Базовые скорости (мс между символами)
  const baseSpeed = {
    slow: 80,
    normal: 50,
    fast: 30,
  }[speed];

  useEffect(() => {
    if (currentIndex >= text.length) {
      onComplete?.();
      return;
    }

    const currentChar = text[currentIndex];
    const nextChar = text[currentIndex + 1];
    const prevChar = text[currentIndex - 1];

    // Определить задержку на основе контекста
    let delay = baseSpeed;

    // 1. Многоточие — длинная пауза (раздумье)
    if (currentChar === "." && nextChar === "." && text[currentIndex + 2] === ".") {
      delay = 1500; // 1.5 секунды раздумья
    }
    // 2. После многоточия — ещё пауза
    else if (prevChar === "." && text[currentIndex - 2] === "." && text[currentIndex - 3] === ".") {
      delay = 800;
    }
    // 3. После точки, вопроса, восклицания — средняя пауза
    else if ([".", "?", "!"].includes(currentChar)) {
      delay = 500;
    }
    // 4. После запятой — короткая пауза
    else if (currentChar === ",") {
      delay = 300;
    }
    // 5. После тире — пауза (смена мысли)
    else if (currentChar === "—" || (currentChar === "-" && nextChar === " ")) {
      delay = 400;
    }
    // 6. Перед важными словами (эвристика: слова с заглавной буквы в середине предложения)
    else if (
      currentChar === " " &&
      nextChar &&
      nextChar === nextChar.toUpperCase() &&
      currentIndex > 0
    ) {
      delay = 200;
    }
    // 7. Пробелы — быстро
    else if (currentChar === " ") {
      delay = baseSpeed * 0.5;
    }
    // 8. Обычные символы — базовая скорость
    else {
      delay = baseSpeed;
    }

    // Добавить небольшую случайность (±20%) для естественности
    const randomness = 0.8 + Math.random() * 0.4;
    delay = delay * randomness;

    timeoutRef.current = setTimeout(() => {
      setDisplayedText((prev) => prev + currentChar);
      setCurrentIndex((prev) => prev + 1);
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [currentIndex, text, baseSpeed, onComplete]);

  // Сброс при изменении текста
  useEffect(() => {
    setDisplayedText("");
    setCurrentIndex(0);
  }, [text]);

  return <span>{displayedText}</span>;
}

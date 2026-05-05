"use client";

import type { CrisisContact } from "@/lib/types";

interface CrisisPanelProps {
  isOpen: boolean;
  onClose: () => void;
  contacts?: CrisisContact[];
}

// Дефолтные универсальные контакты (показываются если бекенд ничего не вернул).
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
 * Открывается по клику на SOS-кнопку или автоматически при immediate.
 */
export default function CrisisPanel({
  isOpen,
  onClose,
  contacts,
}: CrisisPanelProps) {
  if (!isOpen) return null;

  const list = contacts && contacts.length > 0 ? contacts : DEFAULT_CONTACTS;

  return (
    <div
      className="fixed inset-0 bg-warm-900/60 z-50 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-labelledby="crisis-panel-title"
      aria-modal="true"
    >
      <div
        className="bg-warm-50 rounded-2xl max-w-md w-full p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <h2
            id="crisis-panel-title"
            className="text-lg font-semibold text-warm-900"
          >
            Кому позвонить прямо сейчас
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-warm-500 hover:text-warm-700 transition-colors text-2xl leading-none"
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        <p className="text-sm text-warm-700 mb-4">
          Эти службы работают в России. Звонок бесплатный, анонимный.
        </p>

        <ul className="space-y-3">
          {list.map((contact) => (
            <li
              key={contact.phone}
              className="border border-warm-200 rounded-xl p-3 bg-white"
            >
              <a
                href={`tel:${contact.phone.replace(/[^\d+]/g, "")}`}
                className="block"
              >
                <div className="text-lg font-semibold text-accent-700">
                  {contact.phone}
                </div>
                <div className="text-sm font-medium text-warm-900">
                  {contact.name}
                </div>
                <div className="text-xs text-warm-600 mt-0.5">
                  {contact.description}
                </div>
              </a>
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={onClose}
          className="mt-4 w-full bg-warm-200 hover:bg-warm-300 rounded-xl py-2 text-warm-800 font-medium transition-colors"
        >
          Закрыть
        </button>
      </div>
    </div>
  );
}

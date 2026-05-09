/**
 * Дефолтные кризисные контакты России по возрастным группам.
 *
 * ВАЖНО: эти данные — зеркало `backend/app/core/crisis/contacts.py`.
 * Если меняешь номера — синхронно правь оба файла. Sync-тест
 * `backend/tests/test_crisis_contacts_sync.py` ловит расхождение.
 *
 * Принцип Сессии 18: SOS — единственная страховка при сбое analyzer.
 * Поэтому контакты должны быть на frontend, без зависимости от /api/chat.
 */

import type { CrisisContact } from "@/lib/types";

export type AgeGroup = "child" | "youth" | "adult";

/**
 * Универсальные контакты — показываются всегда, для любой возрастной группы.
 * Зеркало UNIVERSAL_CONTACTS в contacts.py.
 */
export const UNIVERSAL_CONTACTS: CrisisContact[] = [
  {
    name: "Экстренные службы",
    phone: "112",
    description: "Единый номер экстренных служб (работает без SIM-карты)",
  },
  {
    name: "МЧС — психологическая помощь",
    phone: "8-800-333-44-34",
    description: "Бесплатно, круглосуточно, анонимно",
  },
];

export const CHILD_CONTACTS: CrisisContact[] = [
  {
    name: "Детский телефон доверия",
    phone: "8-800-2000-122",
    description: "Бесплатно, круглосуточно, анонимно (до 18 лет)",
  },
];

export const YOUTH_CONTACTS: CrisisContact[] = [
  {
    name: "«Помощь рядом»",
    phone: "8-800-100-49-94",
    description: "Бесплатно, для молодёжи до 25 лет",
  },
];

export const ADULT_CONTACTS: CrisisContact[] = [
  {
    name: "Линия «0-24»",
    phone: "8-800-700-84-60",
    description: "Утрата, насилие, суицид — бесплатно, круглосуточно",
  },
];

/** Москва. Зеркало MOSCOW_CONTACTS. Пока не используется по умолчанию,
 *  но должно присутствовать чтобы sync-тест с backend не падал. */
export const MOSCOW_CONTACTS: CrisisContact[] = [
  {
    name: "Московская служба психологической помощи",
    phone: "051",
    description: "С мобильного: 8-495-051",
  },
];

/**
 * Вернуть полный список контактов для возрастной группы.
 * Логика идентична `get_crisis_contacts(age_group)` в contacts.py.
 */
export function getCrisisContacts(ageGroup?: AgeGroup): CrisisContact[] {
  const contacts = [...UNIVERSAL_CONTACTS];
  if (ageGroup === "child") {
    contacts.push(...CHILD_CONTACTS, ...YOUTH_CONTACTS);
  } else if (ageGroup === "youth") {
    contacts.push(...YOUTH_CONTACTS, ...ADULT_CONTACTS);
  } else if (ageGroup === "adult") {
    contacts.push(...ADULT_CONTACTS);
  } else {
    contacts.push(...CHILD_CONTACTS, ...YOUTH_CONTACTS, ...ADULT_CONTACTS);
  }
  return contacts;
}

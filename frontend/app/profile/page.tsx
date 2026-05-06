"use client";

import Link from "next/link";

import DossierView from "@/components/Dossier/DossierView";
import { useSession } from "@/hooks/useSession";

/**
 * Страница профиля.
 *
 * MVP: показывает только досье (что Кайрос помнит о пользователе).
 * После Блока 13 (auth) добавим: данные аккаунта, подписка, история сессий.
 */
export default function ProfilePage() {
  const { guestId } = useSession();

  if (!guestId) {
    return (
      <div className="max-w-3xl mx-auto p-4 text-warm-600">
        Подожди, загружаю профиль...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-warm-50">
      <header className="border-b border-warm-200 bg-warm-50/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            href="/chat"
            className="text-sm text-warm-700 hover:text-warm-900"
          >
            ← Вернуться в чат
          </Link>
          <span className="text-sm text-warm-500">Профиль</span>
        </div>
      </header>
      <DossierView guestId={guestId} />
    </div>
  );
}

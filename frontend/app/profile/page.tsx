"use client";

import DossierView from "@/components/Dossier/DossierView";
import { useSession } from "@/hooks/useSession";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";

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

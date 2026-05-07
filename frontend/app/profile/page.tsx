"use client";

import { AccountSection } from "@/components/Profile/AccountSection";
import { SessionsSection } from "@/components/Profile/SessionsSection";
import DossierView from "@/components/Dossier/DossierView";
import { useAuth } from "@/hooks/useAuth";
import { useSession } from "@/hooks/useSession";
import { cn, RIGHT_DOCK_PADDING } from "@/lib/cn";

/**
 * Страница профиля.
 *
 * Структура:
 * - AccountSection: аккаунт (или приглашение войти, если гость)
 * - SessionsSection: история чатов с сервера (только для залогиненных)
 * - DossierView: что Кайрос помнит — для гостя по guestId, для
 *   залогиненного по user.id (передаём через явный switch на бекенде —
 *   API досье сейчас работает по guest_id, апдейт API досье вынесем
 *   в отдельный блок)
 */
export default function ProfilePage() {
  const { user, status } = useAuth();
  const { guestId } = useSession();

  // ID для досье: для залогиненного — user.id, для гостя — guestId.
  // API досье уже умеет работать с обоими (см. backend/app/api/dossier.py).
  const dossierId = status === "authenticated" && user ? user.id : guestId;

  return (
    <div
      className={cn(
        "flex-1 w-full overflow-y-auto custom-scrollbar p-4 sm:p-6 lg:p-12",
        RIGHT_DOCK_PADDING,
      )}
    >
      <div className="mx-auto max-w-3xl space-y-6">
        <AccountSection />
        <SessionsSection />
        {dossierId ? (
          <DossierView guestId={dossierId} />
        ) : null}
      </div>
    </div>
  );
}

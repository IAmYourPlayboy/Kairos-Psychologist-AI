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
import { getCrisisContacts } from "@/lib/crisis-contacts";
import { spellPhoneForAria, toTelHref } from "@/lib/phoneUtils";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import type { CrisisContact } from "@/lib/types";

interface CrisisPanelProps {
  isOpen: boolean;
  onClose: () => void;
  contacts?: CrisisContact[];
}

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
  const list = contacts && contacts.length > 0 ? contacts : getCrisisContacts();

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
                href={`tel:${toTelHref(contact.phone)}`}
                aria-label={`Позвонить ${contact.name}: ${spellPhoneForAria(contact.phone)}`}
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

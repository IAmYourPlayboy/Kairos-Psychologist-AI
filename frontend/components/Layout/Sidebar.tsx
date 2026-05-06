"use client";

import { Fragment, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion } from "motion/react";
import { Edit2, MessageSquare, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { RenameChatDialog } from "@/components/Layout/RenameChatDialog";
import { cn } from "@/lib/cn";
import { useSession } from "@/hooks/useSession";
import { useSessions, type SessionMeta } from "@/hooks/useSessions";
import { useSidebar } from "@/hooks/useSidebar";
import { useThemeTokens } from "@/hooks/useThemeTokens";

const SIDEBAR_WIDTH = 240;

/**
 * Левый сайдбар: «новый разговор» + список сессий.
 *
 * MVP: один активный чат по умолчанию (уклон в single-chat).
 * Кнопка + создаёт новую сессию. Текущая остаётся в списке.
 *
 * Контекстное меню: ПКМ или двойной клик → переименовать / удалить.
 */
export function Sidebar() {
  const t = useThemeTokens();
  const router = useRouter();
  const pathname = usePathname();
  const { isOpen } = useSidebar();
  const { sessionId, resetSession, switchToSession } = useSession();
  const { sessions, renameSession, deleteSession } = useSessions();

  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    session: SessionMeta;
  } | null>(null);
  const [renameTarget, setRenameTarget] = useState<SessionMeta | null>(null);

  // Закрываем контекстное меню при любом клике вне.
  // requestAnimationFrame чтобы не сразу схлопнуть тот же click event,
  // который открыл меню.
  useEffect(() => {
    if (!contextMenu) return;
    const close = () => setContextMenu(null);
    const id = window.requestAnimationFrame(() => {
      window.addEventListener("click", close);
    });
    return () => {
      window.cancelAnimationFrame(id);
      window.removeEventListener("click", close);
    };
  }, [contextMenu]);

  const isOnChat = pathname === "/chat" || pathname === "/";

  const handleNewChat = () => {
    resetSession();
    if (!isOnChat) router.push("/chat");
  };

  const handleSelectSession = (s: SessionMeta) => {
    switchToSession(s.id);
    if (!isOnChat) router.push("/chat");
  };

  const handleContextMenu = (e: React.MouseEvent, s: SessionMeta) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, session: s });
  };

  return (
    <>
      <motion.aside
        initial={false}
        animate={{
          width: isOpen ? SIDEBAR_WIDTH : 0,
          borderRightWidth: isOpen ? 1 : 0,
        }}
        transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
        className={cn(
          "h-full flex-shrink-0 overflow-hidden relative z-structure transition-colors duration-700",
          t.glassSidebar,
        )}
        style={{ willChange: "width" }}
        aria-label="История бесед"
      >
        <div
          className="h-full flex flex-col p-4 pb-28"
          style={{ width: SIDEBAR_WIDTH }}
        >
          <Button
            onClick={handleNewChat}
            className={cn(
              "w-full justify-start gap-3 h-12 px-4 rounded-xl",
              t.btnPrimary,
            )}
          >
            <Plus className="size-4" />
            Новый разговор
          </Button>

          <div className="h-6" />

          <div
            className={cn(
              "text-xs font-semibold tracking-wider uppercase mb-2 px-2 opacity-60",
              t.textMain,
            )}
          >
            Ваши беседы
          </div>

          <div className="flex-1 overflow-y-auto pr-1 -mr-1 flex flex-col gap-0.5 custom-scrollbar">
            {sessions === null ? (
              <div className={cn("text-xs px-2 py-3", t.textMuted)}>
                Загружаю…
              </div>
            ) : sessions.length === 0 ? (
              <div className={cn("text-xs px-2 py-3 leading-relaxed", t.textMuted)}>
                История появится после первого сообщения.
              </div>
            ) : (
              sessions.map((s, idx) => {
                const isActive = sessionId === s.id;
                return (
                  <Fragment key={s.id}>
                    <Button
                      variant="ghost"
                      onContextMenu={(e) => handleContextMenu(e, s)}
                      onDoubleClick={(e) => handleContextMenu(e, s)}
                      onClick={() => handleSelectSession(s)}
                      className={cn(
                        "w-full font-medium justify-start h-11 px-3 rounded-xl group",
                        t.textMuted,
                        t.btnHover,
                        isActive && "bg-white/10 dark:bg-white/15",
                      )}
                    >
                      <MessageSquare
                        className={cn(
                          "size-4 mr-2 opacity-60 transition-transform group-hover:scale-110",
                          isActive && "opacity-100",
                        )}
                      />
                      <span className="truncate">{s.title}</span>
                    </Button>
                    {idx < sessions.length - 1 && (
                      <div className={cn("h-px mx-3", t.divider)} />
                    )}
                  </Fragment>
                );
              })
            )}
          </div>
        </div>
      </motion.aside>

      {/* Контекстное меню */}
      {contextMenu && (
        <div
          className={cn(
            "fixed z-overlay py-1.5 w-48 rounded-xl shadow-2xl backdrop-blur-xl border",
            t.glassPanel,
            t.textMain,
          )}
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            type="button"
            className={cn(
              "flex items-center gap-3 px-3 py-2 text-sm cursor-pointer mx-1.5 rounded-md w-[calc(100%-12px)]",
              t.btnHover,
            )}
            onClick={() => {
              setRenameTarget(contextMenu.session);
              setContextMenu(null);
            }}
          >
            <Edit2 className="size-4" /> Переименовать
          </button>
          <div className={cn("h-px my-1", t.divider)} />
          <button
            type="button"
            className="flex items-center gap-3 px-3 py-2 text-sm cursor-pointer mx-1.5 rounded-md text-crisis-500 hover:bg-crisis-500/10 w-[calc(100%-12px)]"
            onClick={async () => {
              if (
                !confirm(
                  `Удалить беседу «${contextMenu.session.title}»? Сообщения будут удалены безвозвратно.`,
                )
              ) {
                setContextMenu(null);
                return;
              }
              await deleteSession(contextMenu.session.id);
              if (sessionId === contextMenu.session.id) {
                resetSession();
              }
              toast.success("Беседа удалена");
              setContextMenu(null);
            }}
          >
            <Trash2 className="size-4" /> Удалить
          </button>
        </div>
      )}

      {/* Диалог переименования */}
      <RenameChatDialog
        open={renameTarget !== null}
        initialTitle={renameTarget?.title ?? ""}
        onClose={() => setRenameTarget(null)}
        onConfirm={async (newTitle) => {
          if (!renameTarget) return;
          await renameSession(renameTarget.id, newTitle);
          toast.success("Беседа переименована");
          setRenameTarget(null);
        }}
      />
    </>
  );
}

export { SIDEBAR_WIDTH };

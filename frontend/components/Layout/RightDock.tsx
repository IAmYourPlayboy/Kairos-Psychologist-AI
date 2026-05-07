"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { User, LogIn } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { ThemeToggle } from "@/components/Layout/ThemeToggle";
import { TipCard } from "@/components/Layout/TipCard";
import { cn } from "@/lib/cn";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/hooks/useTheme";
import { useThemeTokens } from "@/hooks/useThemeTokens";

/**
 * Правый плавающий dock: тоггл темы + аватар (ведёт на /profile) + TipCard.
 *
 * SOS-кнопка добавляется в Phase 5 — она требует доступа к crisisLevel
 * из useChat-контекста, поэтому будет рендериться внутри ChatContainer
 * и абсолютно позиционироваться в этой же области.
 *
 * Скрывается на узких экранах (<768px).
 */
export function RightDock() {
  const t = useThemeTokens();
  const { isDark } = useTheme();
  const { user, status } = useAuth();
  const pathname = usePathname();
  const isOnProfile = pathname.startsWith("/profile");
  const isOnAuth = pathname.startsWith("/auth");

  // Куда ведёт аватар:
  // - залогинен: /profile (или /chat если уже на профиле)
  // - гость: /auth/login (если уже на /auth/* — ничего не делаем)
  const isAuthenticated = status === "authenticated";
  const avatarHref = isAuthenticated
    ? isOnProfile
      ? "/chat"
      : "/profile"
    : "/auth/login";
  const avatarLabel = isAuthenticated
    ? isOnProfile
      ? "Вернуться в чат"
      : "Открыть профиль"
    : "Войти в аккаунт";

  // Иконка: для гостя — LogIn, для залогиненного — User или первая буква имени.
  const initial = user?.display_name?.[0] || user?.email?.[0] || "";

  return (
    <aside
      className="hidden md:flex absolute right-0 top-0 h-full w-[260px] lg:w-[280px] flex-col p-6 gap-4 items-end z-floating-low pointer-events-none"
      aria-label="Дополнительная панель"
    >
      <div className="flex items-center gap-3 pointer-events-auto">
        <ThemeToggle />
        <Link href={avatarHref} aria-label={avatarLabel}>
          <Avatar
            className={cn(
              "size-11 cursor-pointer ring-2 ring-transparent transition-all duration-300 hover:scale-105 active:scale-95 shadow-md",
              (isOnProfile || isOnAuth) &&
                (isDark ? "ring-white/50" : "ring-accent-500/50"),
            )}
          >
            <AvatarFallback
              className={cn(
                "backdrop-blur-xl font-medium border uppercase",
                t.glassSidebar,
                t.textMain,
              )}
            >
              {isAuthenticated && initial ? (
                initial
              ) : isAuthenticated ? (
                <User className="size-5" />
              ) : (
                <LogIn className="size-5" />
              )}
            </AvatarFallback>
          </Avatar>
        </Link>
      </div>

      <TipCard />
    </aside>
  );
}

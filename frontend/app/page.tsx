import { redirect } from "next/navigation";

/**
 * Главная страница.
 *
 * MVP: сразу редиректим на /chat — нет онбординга, нет регистрации.
 * Кризисная помощь должна быть в один клик.
 */
export default function HomePage() {
  redirect("/chat");
}

import ChatContainer from "@/components/Chat/ChatContainer";

export const metadata = {
  title: "Чат — Кайрос",
};

/**
 * Главная страница чата.
 *
 * MVP: один экран, без онбординга и регистрации.
 * Сразу даём пользователю возможность написать.
 */
export default function ChatPage() {
  return <ChatContainer />;
}

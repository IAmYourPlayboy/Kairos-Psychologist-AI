import { RegisterForm } from "@/components/Auth/RegisterForm";

export const metadata = {
  title: "Регистрация — Кайрос",
  robots: { index: false, follow: false },
};

export default function RegisterPage() {
  return (
    <div className="mx-auto max-w-md w-full px-4 py-10">
      <div className="rounded-2xl bg-white/60 dark:bg-neutral-900/60 backdrop-blur-md border border-warm-200/60 dark:border-neutral-800/60 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold mb-1">Создать аккаунт</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-6">
          С аккаунтом твоя история сохранится и будет доступна на других
          устройствах. Без — всё работает локально и теряется при чистке кук.
        </p>
        <RegisterForm />
      </div>
    </div>
  );
}

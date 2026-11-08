"use client";

import { createContext, useContext, useEffect, type ReactNode } from "react";
import { useTelegram } from "@/hooks/useTelegram";
import { useLangStore } from "@/store/langStore";

type TelegramContextValue = ReturnType<typeof useTelegram>;

const TelegramContext = createContext<TelegramContextValue | null>(null);

export function TelegramProvider({ children }: { children: ReactNode }) {
  const value = useTelegram();
  const { webApp, user } = value;
  const lang = useLangStore((s) => s.lang);
  const initLang = useLangStore((s) => s.init);

  useEffect(() => {
    if (webApp) initLang(user?.language_code);
  }, [webApp, user, initLang]);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  return <TelegramContext.Provider value={value}>{children}</TelegramContext.Provider>;
}

export function useTelegramContext() {
  const ctx = useContext(TelegramContext);
  if (!ctx) throw new Error("useTelegramContext TelegramProvider ichida ishlatilishi kerak");
  return ctx;
}

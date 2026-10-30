"use client";

import { useEffect, useState } from "react";

type TelegramWebApp = {
  initData: string;
  initDataUnsafe: { user?: { id: number; first_name?: string; username?: string } };
  ready: () => void;
  expand: () => void;
  close: () => void;
  BackButton: { show: () => void; hide: () => void; onClick: (cb: () => void) => void; offClick: (cb: () => void) => void };
  MainButton: {
    text: string;
    show: () => void;
    hide: () => void;
    setText: (text: string) => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
    showProgress: () => void;
    hideProgress: () => void;
  };
  HapticFeedback?: { impactOccurred: (style: string) => void };
  colorScheme: "light" | "dark";
};

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

// Telegram tashqarisida (oddiy brauzerda) ochilganda ham ishlab turishi uchun soxta obyekt.
function fallbackWebApp(): TelegramWebApp {
  return {
    initData: "",
    initDataUnsafe: {},
    ready: () => {},
    expand: () => {},
    close: () => {},
    BackButton: { show: () => {}, hide: () => {}, onClick: () => {}, offClick: () => {} },
    MainButton: {
      text: "",
      show: () => {},
      hide: () => {},
      setText: () => {},
      onClick: () => {},
      offClick: () => {},
      showProgress: () => {},
      hideProgress: () => {},
    },
    colorScheme: "dark",
  };
}

export function useTelegram() {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);

  useEffect(() => {
    const app = window.Telegram?.WebApp ?? fallbackWebApp();
    app.ready();
    app.expand();
    setWebApp(app);
  }, []);

  return {
    webApp,
    user: webApp?.initDataUnsafe.user ?? null,
    initData: webApp?.initData ?? "",
  };
}

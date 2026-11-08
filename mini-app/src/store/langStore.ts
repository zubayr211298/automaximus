import { create } from "zustand";
import { isLang, type Lang } from "@/lib/i18n";

const STORE_KEY = "am_lang";

type LangState = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  // Birinchi ochilganda: ?lang= -> saqlangan tanlov -> Telegram interfeys tili -> o'zbekcha
  init: (telegramLanguageCode?: string) => void;
};

export const useLangStore = create<LangState>((set) => ({
  lang: "uz",
  setLang: (lang) => {
    try {
      localStorage.setItem(STORE_KEY, lang);
    } catch {}
    set({ lang });
  },
  init: (telegramLanguageCode) => {
    let next: Lang = telegramLanguageCode?.toLowerCase().startsWith("ru") ? "ru" : "uz";
    try {
      const fromUrl = new URLSearchParams(window.location.search).get("lang");
      const stored = localStorage.getItem(STORE_KEY);
      if (isLang(fromUrl)) {
        next = fromUrl;
        localStorage.setItem(STORE_KEY, fromUrl);
      } else if (isLang(stored)) {
        next = stored;
      }
    } catch {}
    set({ lang: next });
  },
}));

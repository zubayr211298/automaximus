"use client";

import { useLangStore } from "@/store/langStore";
import { UI, type UiKey } from "@/lib/i18n";

export function useT() {
  const lang = useLangStore((s) => s.lang);
  return { lang, t: (key: UiKey): string => UI[lang][key] };
}

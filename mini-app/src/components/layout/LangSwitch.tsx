"use client";

import { LANGS, UI } from "@/lib/i18n";
import { useLangStore } from "@/store/langStore";

export function LangSwitch() {
  const lang = useLangStore((s) => s.lang);
  const setLang = useLangStore((s) => s.setLang);

  return (
    <div
      role="group"
      aria-label={UI[lang].langLabel}
      style={{
        display: "inline-flex",
        border: "1px solid var(--card-2)",
        borderRadius: 10,
        overflow: "hidden",
        background: "var(--card)",
      }}
    >
      {LANGS.map((l) => (
        <button
          key={l}
          type="button"
          aria-pressed={lang === l}
          onClick={() => setLang(l)}
          style={{
            minHeight: 40,
            minWidth: 46,
            padding: "0 12px",
            border: "none",
            background: lang === l ? "var(--accent)" : "transparent",
            color: "var(--text)",
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: ".04em",
          }}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
